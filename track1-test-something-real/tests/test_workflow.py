from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app

@pytest.fixture
def setup(tmp_path):
    now = [1000.0]
    app = create_app(str(tmp_path / 'test.sqlite3'), clock=lambda: now[0])
    return TestClient(app), now, app.state.database

def session(client, identifier='visitor-test-001', **kwargs):
    response = client.post('/api/session', json={'visitor_id': identifier, **kwargs})
    assert response.status_code == 200
    return {'visitor_id': identifier, 'token': response.json()['token']}

def expose(client, body):
    assert client.post('/api/exposure', json=body).status_code == 200

def task(client, body, invoice='INV-2041', action='draft_reminder', **kwargs):
    return client.post('/api/tasks', json={**body, 'invoice_id':invoice, 'action':action, 'note':'Reviewed invoice and next step.', **kwargs})

def test_stable_assignment_and_session_token(setup):
    client, _, _ = setup
    first = client.post('/api/session',json={'visitor_id':'stable-user-001'}).json()
    second = client.post('/api/session',json={'visitor_id':'stable-user-001'}).json()
    assert first == second

def test_server_clock_and_retry_deduplication_survive_restart(setup, tmp_path):
    client, now, db = setup
    body = session(client)
    expose(client, body)
    now[0] += 40
    assert task(client, body).status_code == 200
    now[0] += 20
    expose(client, body)
    assert task(client, body).status_code == 200
    assert db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM events WHERE name='valid_collection_action'").fetchone()[0] == 1
    assert db.execute("SELECT value FROM events WHERE name='valid_collection_action'").fetchone()[0] == 40
    restarted=TestClient(create_app(str(tmp_path / 'test.sqlite3'),clock=lambda:now[0]))
    assert len(restarted.post('/api/workspace',json=body).json()['tasks']) == 1
    assert task(restarted,body).status_code == 200
    assert db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 1

def test_late_action_saves_task_but_never_counts_primary_conversion(setup):
    client, now, db = setup
    body = session(client)
    expose(client,body)
    now[0] += 601
    assert task(client,body).json()['within_window'] is False
    assert db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM events WHERE name='valid_collection_action'").fetchone()[0] == 0

def test_conversion_requires_exposure_and_real_invoice(setup):
    client, _, db = setup
    body=session(client)
    assert task(client,body).status_code == 409
    expose(client,body)
    assert task(client,body,invoice='nonexistent').status_code == 404
    assert task(client,body,note=' ').status_code == 422
    assert db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 0

def test_dispute_guardrail_rejects_wrong_action(setup):
    client, _, db = setup
    body=session(client)
    expose(client,body)
    assert task(client,body,invoice='INV-2042').status_code == 422
    assert db.execute("SELECT COUNT(*) FROM events WHERE name='invalid_action_attempted'").fetchone()[0] == 1
    assert task(client,body,invoice='INV-2042',action='resolve_dispute').status_code == 200

def test_workspace_isolation(setup):
    client, _, _ = setup
    first=session(client,'workspace-first')
    second=session(client,'workspace-second')
    expose(client,first)
    task(client,first)
    assert client.post('/api/workspace',json=second).json()['tasks'] == []
    assert client.post('/api/workspace',json={**first,'token':second['token']}).status_code == 403

def test_preview_and_synthetic_counts_are_separated(setup):
    client, _, _=setup
    preview=session(client,'preview-visitor',preview_variant='decision_brief')
    synthetic=session(client,'synthetic-visitor',simulated=True,run_id='audit-test')
    for body in (preview,synthetic):
        expose(client,body)
        task(client,body)
    arms=client.get('/api/lab').json()['arms']
    assert sum(a['exposures'] for a in arms if a['cohort']=='human') == 0
    assert sum(a['exposures'] for a in arms if a['cohort']=='synthetic') == 1

@pytest.mark.parametrize('row',[
    'A,Client,1.001,USD,2026-11-01,open',
    'A,Client,NaN,USD,2026-11-01,open',
    'A,Client,100,EUR,2026-11-01,open',
    'A,Client,100,USD,not-a-date,open',
    'A,Client,100,USD,2026-11-01,paid',
    'A,Client,100,USD,2026-11-01,open\nA,Client,200,USD,2026-11-01,open',
])
def test_import_validation_is_atomic(setup,row):
    client, _, _=setup
    body=session(client)
    header='invoice_id,customer,amount,currency,due_date,status\n'
    response=client.post('/api/import',json={**body,'csv_text':header+row})
    assert response.status_code == 422
    assert len(client.post('/api/workspace',json=body).json()['invoices']) == 12

def test_import_precise_money_and_tasks_protect_audit(setup):
    client, _, _=setup
    body=session(client)
    text='invoice_id,customer,amount,currency,due_date,status\nCUSTOM-01,Test company,123.45,USD,2020-01-01,open'
    assert client.post('/api/import',json={**body,'csv_text':text}).status_code == 200
    data=client.post('/api/workspace',json=body).json()
    assert data['invoices'][0]['amount'] == 123.45
    assert data['dataset'] == 'imported'
    expose(client,body)
    task(client,body,invoice='CUSTOM-01')
    assert client.post('/api/import',json={**body,'csv_text':text}).status_code == 409

class Provider:
    def __init__(self,fail=False):
        self.fail=fail
        self.calls=[]
    def get_identity_flags(self,identifier):
        if self.fail: raise RuntimeError('offline')
        return SimpleNamespace(get_flag=lambda name:SimpleNamespace(enabled=True,value='decision_brief',variant='decision_brief',experiment=SimpleNamespace(in_experiment=True)))
    def track_exposure_event(self,*args,**kwargs): self.calls.append(('exposure',kwargs))
    def track_event(self,name,**kwargs): self.calls.append((name,kwargs))

def test_live_exposure_after_display_and_event_metadata(tmp_path):
    provider=Provider()
    client=TestClient(create_app(str(tmp_path/'live.sqlite3'),mode='live',provider=provider))
    body=session(client,simulated=True,run_id='run-1')
    assert provider.calls == []
    expose(client,body)
    task(client,body)
    assert [c[0] for c in provider.calls] == ['exposure','valid_collection_action']
    assert provider.calls[1][1]['metadata']['simulated'] is True
    assert provider.calls[1][1]['metadata']['run_id'] == 'run-1'
    assert client.post('/api/session',json={'visitor_id':'forced-live-001','preview_variant':'decision_brief'}).status_code == 400
    text='invoice_id,customer,amount,currency,due_date,status\nA,Client,100,USD,2020-01-01,open'
    assert client.post('/api/import',json={**body,'csv_text':text}).status_code == 409

def test_live_fallback_never_emits_exposure_or_conversion(tmp_path):
    provider=Provider(fail=True)
    client=TestClient(create_app(str(tmp_path/'fallback.sqlite3'),mode='live',provider=provider))
    body=session(client)
    expose(client,body)
    task(client,body)
    assert provider.calls == []
    assert sum(a['exposures'] for a in client.get('/api/lab').json()['arms']) == 0

def test_concurrent_retries_create_one_task(setup):
    client, _, db=setup
    body=session(client)
    expose(client,body)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results=list(executor.map(lambda _:task(client,body).status_code, range(8)))
    assert results == [200]*8
    assert db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 1
