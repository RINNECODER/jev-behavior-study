"""Frozen paired-seed episodes. Each model action is saved before another is requested."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import json
from pathlib import Path
import random
import time
from .engine import Snake,LEVELS
from .controller import choose,load_env
ROOT=Path(__file__).resolve().parent

def episode(job,out,max_steps=200,target=8,starvation=50):
    level,controller,seed=job;ident=f'{level}-{controller}-{seed}'
    game=Snake(level,seed,max_steps,target,starvation);initial=game.snapshot();rows=[];began=time.perf_counter()
    with (out/(ident+'.jsonl')).open('w') as file:
        while game.status=='playing':
            before=game.snapshot()
            try:
                decision=choose(game,controller);game.step(decision['action'])
                row={'before':before,'decision':decision,'after':game.snapshot()}
            except Exception as error:
                # Keep failures visible, without logging headers/credentials or retrying.
                game.status='api_error';row={'before':before,'error':type(error).__name__,'after':game.snapshot()}
            rows.append(row);file.write(json.dumps(row)+'\n');file.flush()
    calls=[r['decision'] for r in rows if r.get('decision',{}).get('source')=='jev']
    summary={'id':ident,'level':level,'controller':controller,'seed':seed,'initial':initial,'final':game.snapshot(),
        'score':game.score,'moves':game.moves,'outcome':game.status,'model_calls':len(calls),
        'forced_moves':sum(r.get('decision',{}).get('source')=='forced_safe' for r in rows),
        'input_tokens':sum(d['response']['usage']['input_tokens'] for d in calls),
        'output_tokens':sum(d['response']['usage']['output_tokens'] for d in calls),
        'elapsed_seconds':round(time.perf_counter()-began,3)}
    (out/(ident+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--plan-only',action='store_true');p.add_argument('--workers',type=int,default=4)
    args=p.parse_args();load_env(ROOT.parent/'.env')
    seeds=[11] if args.pilot else list(range(101,109))
    levels=['classic'] if args.pilot else list(LEVELS)
    jobs=[(l,c,s) for l in levels for c in ['jev_direct','jev_guarded','baseline'] for s in seeds]
    random.Random(20260923).shuffle(jobs)
    limit=30 if args.pilot else 200;target=3 if args.pilot else 8
    print(f'{len(jobs)} episodes, at most {sum(c!="baseline" for l,c,s in jobs)*limit} Jev calls',flush=True)
    if args.plan_only:return
    out=ROOT/'records'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+('-pilot' if args.pilot else '-benchmark'));out.mkdir(parents=True)
    manifest={'model':'jev-1.13.0','pilot':args.pilot,'seeds':seeds,'levels':LEVELS,'jobs':jobs,'max_steps':limit,'target':target,'starvation':50,
        'workers':args.workers,'method':'One decision per turn; wall-clock latency is measured but does not advance the board. Guarded mode filters immediately fatal moves and executes a sole safe move without a model call. No retries. Seeds shared across controllers, future food can diverge as occupied cells differ.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Saving',out,flush=True)
    summaries=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(episode,j,out,limit,target):j for j in jobs}
        for future in as_completed(futures):
            result=future.result();summaries.append(result);print(f'{len(summaries)}/{len(jobs)} {result["id"]}: food={result["score"]}, moves={result["moves"]}, {result["outcome"]}',flush=True)
    (out/'completion.json').write_text(json.dumps({'planned':len(jobs),'completed':len(summaries),'api_error_episodes':sum(s['outcome']=='api_error' for s in summaries)},indent=2)+'\n')
    print('Finished',out,flush=True)
if __name__=='__main__':main()
