"""ATLAS: isolated business workspaces and server-side experiment instrumentation."""
import csv
import hashlib
import io
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.quant import rank_invoice, portfolio_model

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

class Visitor(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    simulated: bool = False
    run_id: str = Field(default='', max_length=100)
    preview_variant: Literal['control', 'decision_brief'] | None = None

class Session(BaseModel):
    visitor_id: str
    token: str

class Import(Session):
    csv_text: str = Field(max_length=200000)

class Task(Session):
    invoice_id: str
    action: Literal['draft_reminder', 'resolve_dispute', 'schedule_followup']
    note: str = Field(default='', max_length=1000)

SEED = [
    ('INV-2041', 'Meridian Logistics', 'Logistics', 186000, -46, 'open'),
    ('INV-2042', 'Northstar Systems', 'Technology', 124500, -32, 'disputed'),
    ('INV-2043', 'Helix Manufacturing', 'Manufacturing', 92000, -22, 'open'),
    ('INV-2044', 'Cobalt Energy', 'Energy', 76000, -12, 'open'),
    ('INV-2045', 'Vertex Health', 'Healthcare', 58500, -7, 'open'),
    ('INV-2046', 'Meridian Logistics', 'Logistics', 42000, 8, 'open'),
    ('INV-2047', 'Arbor Retail', 'Retail', 34500, 12, 'open'),
    ('INV-2048', 'Northstar Systems', 'Technology', 28000, 18, 'open'),
    ('INV-2049', 'Helix Manufacturing', 'Manufacturing', 22500, 25, 'open'),
    ('INV-2050', 'Cobalt Energy', 'Energy', 18000, -63, 'disputed'),
    ('INV-2051', 'Vertex Health', 'Healthcare', 64000, 6, 'open'),
    ('INV-2052', 'Arbor Retail', 'Retail', 48500, -3, 'open'),
]


def create_app(db_path=None, mode=None, clock=time.time, provider=None):
    mode = mode or os.getenv('ATLAS_MODE', 'demo')
    if mode not in ('demo', 'live'):
        raise ValueError('ATLAS_MODE must be demo or live')
    flag_name = os.getenv('FLAGSMITH_FLAG', 'collections_workspace')
    if mode == 'live' and provider is None:
        from flagsmith import Flagsmith, EventProcessorConfig
        key = os.getenv('FLAGSMITH_SERVER_KEY')
        if not key:
            raise ValueError('Live mode requires FLAGSMITH_SERVER_KEY in .env')
        provider = Flagsmith(environment_key=key, enable_events=True,
                             event_processor_config=EventProcessorConfig(max_buffer_items=1))
    database = sqlite3.connect(db_path or os.getenv('ATLAS_DB', 'atlas.sqlite3'), check_same_thread=False)
    database.row_factory = sqlite3.Row
    database.executescript('''
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, mode TEXT, variant TEXT, source TEXT, enrolled INTEGER,
        token TEXT, simulated INTEGER, run_id TEXT, exposed REAL, converted REAL,
        dataset TEXT DEFAULT 'sample', as_of TEXT DEFAULT '2026-11-25');
      CREATE TABLE IF NOT EXISTS invoices (
        workspace TEXT, id TEXT, customer TEXT, sector TEXT, cents INTEGER,
        due TEXT, status TEXT, PRIMARY KEY(workspace,id));
      CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY, workspace TEXT, invoice TEXT, action TEXT, note TEXT, created REAL,
        UNIQUE(workspace,invoice));
      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY, visitor TEXT, name TEXT, value REAL, metadata TEXT, status TEXT,
        UNIQUE(visitor,name));
    ''')
    database.commit()
    lock = threading.RLock()
    app = FastAPI(title='ATLAS Business Operations Intelligence', version='0.1.0')
    app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(','),
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    def get_person(identifier):
        return database.execute('SELECT * FROM sessions WHERE id=?', (identifier,)).fetchone()

    def auth(body):
        person = get_person(body.visitor_id)
        if not person or not secrets.compare_digest(person['token'], body.token):
            raise HTTPException(403, 'Unknown workspace session')
        if person['mode'] != mode:
            raise HTTPException(409, 'Start a new workspace after changing experiment mode')
        return person

    def record(person, name, value=None):
        metadata = {'simulated': bool(person['simulated']), 'run_id': person['run_id'], 'source': person['source']}
        database.execute('INSERT OR IGNORE INTO events(visitor,name,value,metadata,status) VALUES(?,?,?,?,?)',
            (person['id'], name, value, json.dumps(metadata), 'pending' if person['enrolled'] else 'local'))
        database.commit()

    def dispatch(person):
        for item in database.execute("SELECT * FROM events WHERE visitor=? AND status='pending' ORDER BY id", (person['id'],)).fetchall():
            try:
                if item['name'] == 'exposure':
                    provider.track_exposure_event(flag_name, identifier=person['id'], value=person['variant'], metadata=json.loads(item['metadata']))
                else:
                    provider.track_event(item['name'], identifier=person['id'], value=item['value'], metadata=json.loads(item['metadata']))
            except Exception:
                break
            database.execute("UPDATE events SET status='sdk_accepted' WHERE id=?", (item['id'],))
            database.commit()

    def invoices(person):
        today = date.fromisoformat(person['as_of'])
        result = []
        for item in database.execute('SELECT * FROM invoices WHERE workspace=?', (person['id'],)):
            days = max(0, (today - date.fromisoformat(item['due'])).days)
            action = 'resolve_dispute' if item['status'] == 'disputed' else 'draft_reminder' if days else 'schedule_followup'
            # Transparent triage heuristic, never a credit/default probability.
            ranking = rank_invoice(item['cents'] / 100, action)
            priority = ranking['value_per_hour']
            task = database.execute('SELECT id FROM tasks WHERE workspace=? AND invoice=?', (person['id'], item['id'])).fetchone()
            result.append({'id': item['id'], 'customer': item['customer'], 'sector': item['sector'],
                'amount': item['cents'] / 100, 'due_date': item['due'], 'days_overdue': days,
                'status': item['status'], 'priority': round(priority), 'suggested_action': action,
                'task_id': task['id'] if task else None, **ranking})
        return result

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': mode, 'flag': flag_name}

    @app.post('/api/session')
    def session(body: Visitor):
        with lock:
            person = get_person(body.visitor_id)
            if person and person['mode'] != mode:
                raise HTTPException(409, 'Start a new identity after changing experiment mode')
            if body.preview_variant and mode == 'live':
                raise HTTPException(400, 'Forced variants are disabled in live mode')
            if not person:
                variant, source, enrolled = 'control', 'fallback', False
                if mode == 'demo':
                    variant = body.preview_variant or ('decision_brief' if int(hashlib.sha256(body.visitor_id.encode()).hexdigest(), 16) % 2 else 'control')
                    source = 'preview' if body.preview_variant else 'demo'
                else:
                    try:
                        flag = provider.get_identity_flags(body.visitor_id).get_flag(flag_name)
                        if flag.enabled and str(flag.value) in ('control', 'decision_brief'):
                            variant, source = str(flag.value), 'flagsmith'
                            enrolled = bool(flag.experiment and flag.experiment.in_experiment and flag.variant == variant)
                    except Exception:
                        pass
                database.execute('INSERT INTO sessions(id,mode,variant,source,enrolled,token,simulated,run_id) VALUES(?,?,?,?,?,?,?,?)',
                    (body.visitor_id, mode, variant, source, enrolled, secrets.token_urlsafe(24), body.simulated, body.run_id))
                snapshot = date(2026, 11, 25)
                for identifier, customer, sector, amount, offset, status in SEED:
                    database.execute('INSERT INTO invoices VALUES(?,?,?,?,?,?,?)', (body.visitor_id, identifier, customer, sector, amount * 100, str(snapshot + timedelta(days=offset)), status))
                database.commit()
                person = get_person(body.visitor_id)
            return {'variant': person['variant'], 'source': person['source'], 'mode': mode,
                    'enrolled': bool(person['enrolled']), 'token': person['token']}

    @app.post('/api/exposure')
    def exposure(body: Session):
        with lock:
            person = auth(body)
            database.execute('UPDATE sessions SET exposed=COALESCE(exposed,?) WHERE id=?', (clock(), person['id']))
            database.commit()
            record(person, 'exposure')
            dispatch(person)
            return {'ok': True}

    @app.post('/api/workspace')
    def workspace(body: Session):
        with lock:
            person = auth(body)
            items = invoices(person)
            tasks = [dict(r) for r in database.execute('SELECT id,invoice,action,note,created FROM tasks WHERE workspace=? ORDER BY id DESC', (person['id'],))]
            return {'invoices': items, 'tasks': tasks, 'dataset': person['dataset'], 'as_of': person['as_of'], 'currency': 'USD', 'quant': portfolio_model(items)}

    @app.post('/api/tasks')
    def create_task(body: Task):
        with lock:
            person = auth(body)
            if person['exposed'] is None:
                raise HTTPException(409, 'Display the workspace before recording an action')
            item = next((r for r in invoices(person) if r['id'] == body.invoice_id), None)
            if not item:
                raise HTTPException(404, 'Invoice not found')
            if body.action != item['suggested_action']:
                record(person, 'invalid_action_attempted', 1)
                dispatch(person)
                raise HTTPException(422, 'Disputed invoices need dispute review; overdue invoices need a reminder; current invoices need a scheduled follow-up.')
            if not body.note.strip():
                raise HTTPException(422, 'Add a review note before saving the task')
            database.execute('INSERT OR IGNORE INTO tasks(workspace,invoice,action,note,created) VALUES(?,?,?,?,?)',
                (person['id'], item['id'], body.action, body.note.strip(), clock()))
            elapsed = max(0, clock() - person['exposed'])
            account_scores = {}
            for invoice in invoices(person):
                account_scores[invoice['customer']] = account_scores.get(invoice['customer'], 0) + invoice['priority']
            top_five = {name for name, _ in sorted(account_scores.items(), key=lambda pair: (-pair[1], pair[0]))[:5]}
            high_priority = item['customer'] in top_five
            if not high_priority:
                record(person, 'low_priority_action', 1)
            if person['converted'] is None and elapsed <= 600 and high_priority and person['dataset'] == 'sample':
                database.execute('UPDATE sessions SET converted=? WHERE id=?', (clock(), person['id']))
                database.commit()
                record(person, 'valid_collection_action', elapsed)
            database.commit()
            dispatch(person)
            return {'ok': True, 'within_window': elapsed <= 600, 'high_priority': high_priority, 'message': 'Task saved. No message sent and no payment executed.'}

    @app.post('/api/import')
    def import_csv(body: Import):
        with lock:
            person = auth(body)
            reader = csv.DictReader(io.StringIO(body.csv_text.lstrip('\ufeff')))
            required = {'invoice_id', 'customer', 'amount', 'due_date', 'status', 'currency'}
            if not required.issubset(reader.fieldnames or []):
                raise HTTPException(422, 'Required columns: ' + ', '.join(sorted(required)))
            parsed, seen = [], set()
            try:
                for n, item in enumerate(reader, 1):
                    if n > 500:
                        raise ValueError('Maximum 500 invoices per import')
                    identifier, customer = item['invoice_id'].strip(), item['customer'].strip()
                    amount = Decimal(item['amount'])
                    if not amount.is_finite() or amount <= 0 or amount > 1000000000 or amount.as_tuple().exponent < -2:
                        raise ValueError('Amounts must be positive with at most two decimal places')
                    if not identifier or len(identifier) > 80 or not customer or len(customer) > 120 or identifier in seen:
                        raise ValueError('Invoice IDs must be unique; IDs and customer names must be present and within limits')
                    if item['status'] not in ('open', 'disputed') or item['currency'] != 'USD':
                        raise ValueError('Use open/disputed status and USD currency only')
                    due = str(date.fromisoformat(item['due_date']))
                    parsed.append((person['id'], identifier, customer, 'Imported', int(amount * 100), due, item['status']))
                    seen.add(identifier)
                if not parsed:
                    raise ValueError('No invoice rows found')
            except (ValueError, InvalidOperation, TypeError, KeyError, AttributeError) as error:
                raise HTTPException(422, f'Invalid CSV: {error}') from error
            # Imports would change the task difficulty; keep them out of the controlled experiment.
            if mode == 'live' and person['enrolled']:
                raise HTTPException(409, 'Imports are disabled for enrolled experiment sessions; use a separate demo workspace')
            if database.execute('SELECT 1 FROM tasks WHERE workspace=?', (person['id'],)).fetchone():
                raise HTTPException(409, 'Start a fresh workspace to import after recording tasks')
            database.execute('DELETE FROM invoices WHERE workspace=?', (person['id'],))
            database.executemany('INSERT INTO invoices VALUES(?,?,?,?,?,?,?)', parsed)
            database.execute("UPDATE sessions SET dataset='imported',as_of=? WHERE id=?", (str(date.today()), person['id']))
            database.commit()
            return {'imported': len(parsed)}

    @app.get('/api/lab')
    def lab():
        with lock:
            arms = []
            for cohort in ('human', 'synthetic'):
                for variant in ('control', 'decision_brief'):
                    counts = database.execute('''SELECT COUNT(*) AS exposures, COUNT(converted) AS conversions,
                        AVG(converted-exposed) AS mean_seconds FROM sessions WHERE mode=? AND variant=? AND simulated=?
                        AND exposed IS NOT NULL AND dataset='sample' AND source NOT IN ('fallback','preview')
                        AND (?='demo' OR enrolled=1)''', (mode, variant, cohort == 'synthetic', mode)).fetchone()
                    arms.append({'cohort': cohort, 'variant': variant, **dict(counts)})
            pending = database.execute("SELECT COUNT(*) FROM events WHERE status='pending'").fetchone()[0]
            return {'mode': mode, 'arms': arms, 'pending_events': pending, 'decision_brief': 'KEEP RUNNING',
                'note': 'Local audit counts. Check Bayesian results and confirmed delivery in Flagsmith. Imported and forced-preview sessions are excluded.'}

    app.state.database = database
    return app

app = create_app()
