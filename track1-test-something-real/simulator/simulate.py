"""Synthetic HTTP traffic. This validates instrumentation, not business impact."""
import argparse
import random
import time
import uuid
import httpx

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url',default='http://127.0.0.1:8000')
parser.add_argument('--visitors',type=int,default=100)
parser.add_argument('--seed',type=int,default=42)
parser.add_argument('--model',choices=['null','effect'],default='null')
parser.add_argument('--allow-live',action='store_true',help='Explicitly allow sending synthetic events to a live experiment')
parser.add_argument('--think-time',type=float,default=0,help='Seconds of real wait before an action; default rapid pipeline test')
args=parser.parse_args()
if not 1<=args.visitors<=2000 or not 0<=args.think_time<=600:
    parser.error('Use 1–2000 visitors and 0–600 seconds think time.')
rng=random.Random(args.seed)
run_id=f'synthetic-{uuid.uuid4().hex[:12]}'
counts={}
with httpx.Client(base_url=args.url,timeout=30) as client:
    health=client.get('/api/health');health.raise_for_status()
    if health.json()['mode']=='live' and not args.allow_live:
        parser.error('Live experiment detected. Use a dedicated synthetic environment and --allow-live.')
    for index in range(args.visitors):
        identifier=f'{run_id}-{index}'
        response=client.post('/api/session',json={'visitor_id':identifier,'simulated':True,'run_id':run_id});response.raise_for_status()
        result=response.json()
        session={'visitor_id':identifier,'token':result['token']}
        response=client.post('/api/workspace',json=session);response.raise_for_status()
        invoice=response.json()['invoices'][0]
        response=client.post('/api/exposure',json=session);response.raise_for_status()
        variant=result['variant']
        counts.setdefault(variant,{'exposed':0,'actions':0})['exposed']+=1
        probability=0.38 if args.model=='effect' and variant=='decision_brief' else 0.30
        if rng.random()<probability:
            if args.think_time:time.sleep(args.think_time)
            response=client.post('/api/tasks',json={**session,'invoice_id':invoice['id'],'action':invoice['suggested_action'],'note':f'SYNTHETIC behaviour model {args.model}; run {run_id}.'})
            response.raise_for_status()
            counts[variant]['actions']+=1
print({'run_id':run_id,'seed':args.seed,'model':args.model,'cohorts':counts})
print('SYNTHETIC ONLY. Conversion probabilities are programmed assumptions; rapid-run timings are not human timings.')
