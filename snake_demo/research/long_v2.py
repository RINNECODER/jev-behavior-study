"""Adaptive bounded-certificate long-game test. Every failure remains visible."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import time
from ..engine import Snake
from .efficient import certify
from .experiment import ROOT,dump,call,compact


def model_payload(g,c):
    return {'model':'jev-1.13.0','state':{'board':compact(g),'candidates':{a:{'minimum_required_moves':c['lower_bounds'][a],'exact':c['status'][a]=='solved','status':c['status'][a]} for a in c['status']}},'questions':{'move':{'type':'choice','instructions':'Choose the action with the smallest non-null minimum_required_moves. The minimum is an exact shortest route certified by code. Other numbers may be lower bounds on longer routes. Null means collision. Any tied minimum is correct.','criteria':{a:a.title()+' turn.' for a in c['status']}}}}


def episode(seed,out,model=False):
    g=Snake(seed=seed,target=24,max_steps=600);rows=[];ident=('jev' if model else 'oracle')+'-'+str(seed);initial=g.snapshot()
    with (out/(ident+'.jsonl')).open('w') as f:
        while g.status=='playing':
            before=g.snapshot();start=time.perf_counter();c=certify(g);ms=round((time.perf_counter()-start)*1000,2)
            row={'before':before,'certificate':c,'planner_ms':ms,'call':None,'action':None}
            if not c['resolved'] or not c['optimal']:g.status='planner_unknown' if c['root_status']!='unreachable' else 'no_route'
            else:
                if model:
                    record=call(model_payload(g,c));row['call']=record
                    if not record['valid']:g.status='api_error'
                    else:row['action']=record['response']['answers']['move']['choice']
                else:row['action']=c['optimal'][0]
                if row['action'] is not None:g.step(row['action'])
            row['after']=g.snapshot();rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
    result={'id':ident,'seed':seed,'initial':initial,'final':g.snapshot(),'moves':g.moves,'score':g.score,'outcome':g.status,'model':model,'decisions':len(rows)}
    dump(out/(ident+'.json'),result);return result


def run(out,seeds,model=False,method=''):
    out.mkdir(parents=True,exist_ok=False);dump(out/'manifest.json',{'seeds':list(seeds),'model':model,'target':24,'max_steps':600,'starvation':50,'method':method})
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(episode,s,out,model) for s in seeds]):
            r=future.result();results.append(r);print(r['id'],r['score'],r['moves'],r['outcome'],flush=True)
    dump(out/'completion.json',{'completed':len(results),'planned':len(seeds),'successes':sum(r['outcome']=='target_reached' for r in results)})
    return results
