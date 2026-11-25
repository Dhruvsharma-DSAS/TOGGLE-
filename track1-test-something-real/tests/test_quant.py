from backend.quant import portfolio_model, rank_invoice
from fastapi.testclient import TestClient
from backend.main import create_app

def test_distribution_quantiles_and_diversification_bounds():
    items=[{'customer':'A','amount':100,'suggested_action':'draft_reminder'},
           {'customer':'B','amount':100,'suggested_action':'draft_reminder'}]
    result=portfolio_model(items)
    assert result==portfolio_model(items)
    assert 0<=result['p05']<=result['p50']<=result['p95']<=200
    assert result['concentration_hhi']==5000
    assert result['cash_at_risk']==result['p50']-result['p05']
    assert portfolio_model([])['p95']==0

def test_value_per_hour_uses_published_effort_and_uplift():
    result=rank_invoice(1000,'draft_reminder')
    assert result['expected_incremental_cash']==150
    assert result['value_per_hour']==600

def test_low_priority_task_is_saved_but_not_counted_as_primary(tmp_path):
    app=create_app(str(tmp_path/'quant.sqlite3'))
    client=TestClient(app)
    result=client.post('/api/session',json={'visitor_id':'low-priority-test'}).json()
    body={'visitor_id':'low-priority-test','token':result['token']}
    items=client.post('/api/workspace',json=body).json()['invoices']
    scores={}
    for invoice in items:scores[invoice['customer']]=scores.get(invoice['customer'],0)+invoice['priority']
    bottom=min(scores,key=scores.get)
    invoice=next(i for i in items if i['customer']==bottom)
    client.post('/api/exposure',json=body)
    response=client.post('/api/tasks',json={**body,'invoice_id':invoice['id'],'action':invoice['suggested_action'],'note':'Legitimate lower priority work.'})
    assert response.status_code==200
    assert response.json()['high_priority'] is False
    assert app.state.database.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]==1
    names=[r[0] for r in app.state.database.execute('SELECT name FROM events')]
    assert 'low_priority_action' in names
    assert 'valid_collection_action' not in names
