"""Frozen same-state ablations, repeated-order probes and atomic questions."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import time
import urllib.request
import urllib.error
from ..controller import MODEL,make_payload,load_env
from ..engine import Snake,ACTIONS,DIRECTIONS
from .oracle import assess,restore
ROOT=Path(__file__).resolve().parent
VARIANTS=['original','compact','absolute','local','exact']


def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def fingerprint(state):
    fields={k:state[k] for k in ['size','snake','heading','food','obstacles','wrap']}
    return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()


def compact(g):
    return {'board_size':g.size,'solid_edges':True,'head':list(g.body[0]),'body_head_to_tail':g.snapshot()['snake'],
            'heading':DIRECTIONS[g.heading],'food':list(g.food),'coordinates':'x right, y down; origin top left; zero indexed'}


def payload_for(g,variant,oracle=None,order=None):
    order=order or list(ACTIONS)
    if variant=='original':
        p=make_payload(g,'jev_direct');criteria=p['questions']['move']['criteria']
        p['questions']['move']['criteria']={a:criteria[a] for a in order};return p,{a:a for a in order}
    state=compact(g);criteria={};mapping={}
    instruction=('Choose the first move of a shortest LEGAL route to the current food. '
      'The head moves one cell. Do not hit solid edges or the body. No reverse turn. '
      'The tail vacates on non-food moves. Minimize steps to food; any equally shortest route is acceptable.')
    for a in order:
        x,y=g.destination(a);direction=DIRECTIONS[(g.heading+ACTIONS[a])%4]
        key=direction if variant=='absolute' else a;mapping[key]=a
        criteria[key]=f'Move {direction} to ({x}, {y}).'
    if variant=='local':
        state['candidate_facts']={a:{'safe_next_move':g.safe(a),'manhattan_distance_after_move':abs(g.destination(a)[0]-g.food[0])+abs(g.destination(a)[1]-g.food[1])} for a in order}
        instruction+=' Candidate facts were computed by code. Use safety first, then route length; Manhattan distance ignores body detours.'
    if variant=='exact':
        assert oracle and oracle['resolved']
        state['verified_routes']={a:{'status':oracle['status'][a],'total_moves_to_food':oracle['costs'][a]} for a in order}
        instruction=('Code has already computed the exact shortest legal route length starting with each action, including that first move. '
        'Choose an action with the SMALLEST non-null total_moves_to_food. Null is invalid or unreachable. '
        'Any tied minimum is correct. Do not prefer straight or any direction over a smaller number.')
    return {'model':MODEL,'state':state,'questions':{'move':{'type':'choice','instructions':instruction,'criteria':criteria}}},mapping


def call(payload):
    body=json.dumps(payload).encode();record={'payload':payload,'payload_sha256':hashlib.sha256(body).hexdigest(),'started_at':datetime.now(timezone.utc).isoformat()}
    started=time.perf_counter()
    request=urllib.request.Request('https://api.typesafe.ai/v1/systemone',data=body,headers={'Authorization':'Bearer '+os.environ['TYPESAFE_API_KEY'],'Content-Type':'application/json','Cache-Control':'no-cache'})
    try:
        with urllib.request.build_opener().open(request,timeout=60) as response:
            record['http_status']=response.status;record['raw_response']=response.read().decode()
        parsed=json.loads(record['raw_response']);record['response']=parsed
        assert parsed['model']==MODEL
        for key,q in payload['questions'].items():
            a=parsed['answers'][key];assert a['type']=='choice' and a['choice'] in q['criteria']
            assert set(a['probabilities'])==set(q['criteria'])
        record['valid']=True
    except Exception as error:
        record['valid']=False;record['error']=type(error).__name__
        if isinstance(error,urllib.error.HTTPError):record['http_status']=error.code
    record['latency_ms']=round((time.perf_counter()-started)*1000,2)
    return record


def generated(seeds,policy):
    states=[];rng=random.Random(871)
    for seed in seeds:
        g=Snake(seed=seed)
        while g.status=='playing':
            states.append({'state':g.snapshot(),'source':f'{policy}-{seed}'})
            legal=g.legal()
            g.step(g.baseline() if policy=='baseline' else rng.choice(legal) if legal else 'straight')
    return states


def sample_states(candidates,n,rng,seen):
    rng.shuffle(candidates);out=[]
    for item in candidates:
        f=fingerprint(item['state'])
        if f in seen:continue
        o=assess(restore(item['state']))
        if not o['resolved'] or not o['optimal']:continue
        seen.add(f);out.append({**item,'fingerprint':f,'oracle':o})
        if len(out)==n:return out
    raise RuntimeError('Insufficient unique resolved states')


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(2026091701);seen=set();development=[]
    old=ROOT.parent/'records'/'20260917T013832Z-benchmark'
    for c in ['jev_direct','baseline']:
        candidates=[]
        for p in sorted(old.glob(f'classic-{c}-*.jsonl')):
            for line in p.read_text().splitlines():
                row=json.loads(line);candidates.append({'state':row['before'],'source':p.stem})
        development+=sample_states(candidates,20,rng,seen)
    development+=sample_states(generated(range(201,221),'random'),20,rng,seen)
    holdout=[]
    for policy in ['baseline','random']:holdout+=sample_states(generated(range(301,321),policy),30,rng,seen)
    corpus=[]
    for split,items in [('development',development),('holdout',holdout)]:
        for i,item in enumerate(items):corpus.append({**item,'id':f'{split}-{i:03}','split':split})
    dump(out/'corpus.json',corpus);jobs=[]
    for item in corpus:
        offset=int(item['id'].split('-')[-1])%3;order=list(ACTIONS);order=order[offset:]+order[:offset]
        for variant in VARIANTS:jobs.append({'id':item['id']+'-'+variant,'state_id':item['id'],'kind':'ablation','variant':variant,'order':order})
    for item in corpus[:12]:
        for i,order in enumerate(itertools.permutations(ACTIONS)):
            for repetition in range(2):jobs.append({'id':f"{item['id']}-order-{i}-{repetition}",'state_id':item['id'],'kind':'order','variant':'original','order':list(order),'repetition':repetition})
    for item in corpus[:30]:
        for action in ACTIONS:
            for predicate in ['safe','progress']:jobs.append({'id':f"{item['id']}-{predicate}-{action}",'state_id':item['id'],'kind':'atomic','action':action,'predicate':predicate})
    rng.shuffle(jobs);dump(out/'manifest.json',{'model':MODEL,'jobs':jobs,'workers':4,'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),'prepared_at':datetime.now(timezone.utc).isoformat()})
    print('Prepared',len(corpus),'states and',len(jobs),'jobs',flush=True)


def job_payload(job,item):
    g=restore(item['state'])
    if job['kind']!='atomic':return payload_for(g,job['variant'],item['oracle'],job['order'])
    action=job['action'];dest=g.destination(action);state=compact(g)
    state['candidate']={'turn':action,'destination':dest}
    instruction=('Will this single candidate move avoid both the boundary and the snake body? The tail vacates unless food is eaten.' if job['predicate']=='safe' else 'Will this candidate move strictly reduce the Manhattan distance from head to food? Ignore collisions for this question. Manhattan distance is abs(x_head-x_food)+abs(y_head-y_food).')
    return {'model':MODEL,'state':state,'questions':{'check':{'type':'choice','instructions':instruction,'criteria':{'yes':'The statement is true.','no':'The statement is false.'}}}},None


def execute(out):
    manifest=json.loads((out/'manifest.json').read_text());corpus={x['id']:x for x in json.loads((out/'corpus.json').read_text())}
    def run(job):
        target=out/(job['id']+'.json')
        if target.exists():return json.loads(target.read_text())
        payload,mapping=job_payload(job,corpus[job['state_id']]);result={'job':job,'mapping':mapping,'call':call(payload)};dump(target,result);return result
    completed=0;failed=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(run,j) for j in manifest['jobs']]):
            result=future.result();completed+=1;failed+=not result['call']['valid']
            if completed%50==0:print('Completed',completed,'errors',failed,flush=True)
    dump(out/'completion.json',{'completed':completed,'failed':failed});print('Done',completed,failed,flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run']);p.add_argument('directory',type=Path);args=p.parse_args()
    if args.mode=='prepare':prepare(args.directory)
    else:load_env(ROOT.parents[1]/'.env');execute(args.directory)
if __name__=='__main__':main()
