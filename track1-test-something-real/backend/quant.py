"""Transparent scenario assumptions; these are not fitted credit or causal models."""
import math
import random
from collections import defaultdict

ASSUMPTIONS = {
    'resolve_dispute': {'without': .10, 'with': .45, 'effort_hours': 1.5},
    'draft_reminder': {'without': .40, 'with': .55, 'effort_hours': .25},
    'schedule_followup': {'without': .70, 'with': .73, 'effort_hours': .25},
}

def rank_invoice(amount, action):
    assumptions=ASSUMPTIONS[action]
    recovery=amount*(assumptions['with']-assumptions['without'])
    return {'expected_incremental_cash':round(recovery,2),
        'value_per_hour':round(recovery/assumptions['effort_hours'],2),
        'assumptions':assumptions,
        'reason':f"${amount:,.0f} × {(assumptions['with']-assumptions['without'])*100:.0f}pp assumed action uplift ÷ {assumptions['effort_hours']}h effort"}

def portfolio_model(invoices, runs=1000, seed=42):
    """30-day illustrative cash model: independent invoice arrivals, stated assumptions."""
    totals=defaultdict(float)
    for invoice in invoices: totals[invoice['customer']]+=invoice['amount']
    total=sum(totals.values())
    hhi=sum((value/total)**2 for value in totals.values())*10000 if total else 0
    rng=random.Random(seed)
    samples=[]
    for _ in range(runs):
        samples.append(sum(r['amount'] for r in invoices if rng.random()<ASSUMPTIONS[r['suggested_action']]['without']))
    samples.sort()
    def quantile(p):
        return round(samples[min(len(samples)-1,math.floor((len(samples)-1)*p))],2)
    low,median,high=quantile(.05),quantile(.5),quantile(.95)
    return {'p05':low,'p50':median,'p95':high,'cash_at_risk':round(median-low,2),
        'concentration_hhi':round(hhi),'runs':runs,'seed':seed,'horizon_days':30,
        'assumptions':ASSUMPTIONS,
        'note':'Illustrative independent Bernoulli invoice receipts. Probabilities and effort are assumptions, not fitted estimates. No correlation or partial payments. Not a validated cash forecast.'}
