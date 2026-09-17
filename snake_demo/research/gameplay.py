"""Held-out closed-loop tests with explicit planner assistance accounting."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import json
from pathlib import Path
import random
import time
from ..engine import Snake,ACTIONS
from .oracle import assess
from .experiment import ROOT,call,dump,payload_for


def decision(g,profile,variant=None):
    start=time.perf_counter();oracle=assess(g);planner_ms=round((time.perf_counter()-start)*1000,2)
    if not oracle['resolved']:raise RuntimeError('Planner search unresolved; no optimality claim')
    if not oracle['optimal']:raise RuntimeError('No route to food; no valid shortest move')
    if profile=='oracle':return {'action':oracle['optimal'][0],'proposal':None,'overridden':False,'source':'exact_planner','oracle':oracle,'planner_ms':planner_ms,'call':None}
    order=list(ACTIONS);offset=(g.seed+g.moves)%3;order=order[offset:]+order[:offset]
    payload,mapping=payload_for(g,'exact' if profile=='verified' else variant,oracle,order)
    record=call(payload)
    result={'oracle':oracle,'planner_ms':planner_ms,'call':record,'source':'jev_with_exact_planner' if profile in ['verified','assisted'] else 'jev','mapping':mapping}
    if not record['valid']:return {**result,'action':None,'proposal':None,'overridden':False}
    proposal=mapping[record['response']['answers']['move']['choice']]
    action=proposal if profile!='verified' or proposal in oracle['optimal'] else oracle['optimal'][0]
    return {**result,'proposal':proposal,'action':action,'overridden':action!=proposal}


def episode(job,out,target=8,max_steps=200):
    profile,variant,seed=job;g=Snake(seed=seed,target=target,max_steps=max_steps);ident=f'{profile}-{seed}';path=out/(ident+'.jsonl')
    if path.exists():raise RuntimeError('Refusing to overwrite a game')
    initial=g.snapshot();rows=[]
    with path.open('w') as file:
        while g.status=='playing':
            before=g.snapshot()
            try:
                d=decision(g,profile,variant)
                if d['action'] is None:g.status='api_error'
                else:g.step(d['action'])
                row={'before':before,'decision':d,'after':g.snapshot()}
            except Exception as error:
                g.status='planner_error';row={'before':before,'error':type(error).__name__,'after':g.snapshot()}
            rows.append(row);file.write(json.dumps(row)+'\n');file.flush()
    calls=[r['decision']['call'] for r in rows if r.get('decision',{}).get('call')]
    summary={'id':ident,'profile':profile,'variant':variant,'seed':seed,'initial':initial,'final':g.snapshot(),'score':g.score,'moves':g.moves,'outcome':g.status,'model_calls':len(calls),'valid_calls':sum(c['valid'] for c in calls),'overrides':sum(r.get('decision',{}).get('overridden',False) for r in rows)}
    dump(out/(ident+'.json'),summary);return summary


def prepare(out,diagnosis):
    out.mkdir(parents=True,exist_ok=False);selection=json.loads((diagnosis/'selection.json').read_text())['variants']
    jobs=[(profile,variant,seed) for profile,variant in [('unassisted',selection['unassisted']),('assisted',selection['assisted']),('verified','exact'),('oracle',None)] for seed in range(1001,1017)]
    random.Random(2026091702).shuffle(jobs)
    dump(out/'manifest.json',{'jobs':jobs,'selection':selection,'prepared_at':datetime.now(timezone.utc).isoformat(),'target':8,'max_steps':200,'starvation':50,'workers':4,'method':'Frozen held-out seeds; no retries. All profiles measured against exact current-food oracle. Code assistance disclosed.'})


def run(out):
    manifest=json.loads((out/'manifest.json').read_text());jobs=manifest['jobs'];summaries=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(episode,j,out,manifest.get('target',8),manifest.get('max_steps',200)) for j in jobs]):
            r=future.result();summaries.append(r);print(len(summaries),r['id'],r['score'],r['moves'],r['outcome'],'overrides',r['overrides'],flush=True)
    dump(out/'completion.json',{'planned':len(jobs),'completed':len(summaries)})


def stress(out):
    out.mkdir(parents=True,exist_ok=False);jobs=[('oracle',None,s) for s in range(2001,2101)]
    dump(out/'manifest.json',{'jobs':jobs,'target':8,'max_steps':200,'starvation':50,'method':'Code-only extension, not Jev accuracy'})
    run(out)
