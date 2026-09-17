"""Run policies without invoking any safety or route scorer."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
from ..engine import Snake,ACTIONS
from ..research.experiment import dump,fingerprint
from .policy import VARIANTS,decide,observation
ROOT=Path(__file__).resolve().parent


def prepare_screen(out):
    out.mkdir(parents=True,exist_ok=False);candidates=[];seen=set()
    source=ROOT.parent/'research/records/gameplay-v1'
    for path in sorted(source.glob('unassisted-*.jsonl')):
        history=[]
        for i,line in enumerate(path.read_text().splitlines()):
            r=json.loads(line);state=r['before'];f=fingerprint(state)
            if f not in seen:
                seen.add(f);candidates.append({'state':state,'history':list(history[-4:]),'source':str(path.relative_to(ROOT.parent)), 'source_row':i,'fingerprint':f})
            d=r.get('decision',{})
            if d.get('action'):
                # The old policy's actual model action, never oracle information.
                g=Snake();g.body=list(map(tuple,state['snake']));g.food=tuple(state['food']);g.heading=['north','east','south','west'].index(state['heading']);g.score=state['score'];g.since_food=state['since_food']
                history.append({'observation':observation(g),'action':d['action']})
    rng=random.Random(2026091708);rng.shuffle(candidates);corpus=[{'id':f'dev-{i:03}',**x} for i,x in enumerate(candidates[:80])]
    dump(out/'corpus.json',corpus)
    jobs=[{'id':x['id']+'-'+v,'state_id':x['id'],'variant':v,'order':list(ACTIONS)[i%3:]+list(ACTIONS)[:i%3]} for i,x in enumerate(corpus) for v in VARIANTS];rng.shuffle(jobs)
    dump(out/'manifest.json',{'jobs':jobs,'phase':'development_screen','workers':4,'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),'prepared_at':datetime.now(timezone.utc).isoformat()})
    print('Prepared',len(corpus),'states',len(jobs),'decisions',flush=True)


def state_game(s):
    g=Snake(seed=s['seed']);g.body=list(map(tuple,s['snake']));g.heading=['north','east','south','west'].index(s['heading']);g.food=tuple(s['food']);g.score=s['score'];g.moves=s['moves'];g.since_food=s['since_food'];return g


def run_screen(out):
    corpus={x['id']:x for x in json.loads((out/'corpus.json').read_text())};jobs=json.loads((out/'manifest.json').read_text())['jobs']
    def job(j):
        p=out/(j['id']+'.json')
        if p.exists():raise RuntimeError('Refusing to overwrite existing call')
        item=corpus[j['state_id']];d=decide(state_game(item['state']),j['variant'],item['history'],j['order']);dump(p,{'job':j,'decision':d});return d
    done=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(job,j) for j in jobs]):
            future.result();done+=1
            if done%80==0:print('Screen decisions',done,flush=True)
    dump(out/'completion.json',{'planned':len(jobs),'completed':done})


def prepare_games(out,variants,seeds,phase,selection):
    out.mkdir(parents=True,exist_ok=False);jobs=[(v,s) for v in variants for s in seeds];random.Random(2026091709).shuffle(jobs)
    dump(out/'manifest.json',{'jobs':jobs,'phase':phase,'selection':selection,'variants':variants,'seeds':list(seeds),'target':8,'max_steps':200,'starvation':50,'workers':4,'prepared_at':datetime.now(timezone.utc).isoformat()})


def episode(job,out):
    variant,seed=job;g=Snake(seed=seed);initial=g.snapshot();history=[];ident=f'{variant}-{seed}';path=out/(ident+'.jsonl');rows=[]
    if path.exists():raise RuntimeError('Refusing to overwrite existing game')
    with path.open('w') as f:
        while g.status=='playing':
            before=g.snapshot();order=list(ACTIONS);offset=(seed+g.moves)%3;order=order[offset:]+order[:offset]
            d=decide(g,variant,history,order)
            if d['action'] is None:g.status='api_error'
            else:
                history.append({'observation':observation(g),'action':d['action']});g.step(d['action'])
            r={'before':before,'decision':d,'after':g.snapshot()};rows.append(r);f.write(json.dumps(r)+'\n');f.flush()
    calls=[c['record'] for r in rows for c in r['decision']['calls']]
    summary={'id':ident,'variant':variant,'seed':seed,'initial':initial,'final':g.snapshot(),'food':g.score,'moves':g.moves,'outcome':g.status,'calls':len(calls),'valid_calls':sum(c['valid'] for c in calls)}
    dump(out/(ident+'.json'),summary);return summary


def run_games(out):
    jobs=json.loads((out/'manifest.json').read_text())['jobs'];done=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(episode,j,out) for j in jobs]):
            r=future.result();done+=1;print(done,r['id'],r['food'],r['moves'],r['outcome'],flush=True)
    dump(out/'completion.json',{'planned':len(jobs),'completed':done})
