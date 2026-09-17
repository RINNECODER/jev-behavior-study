"""Verify complete episodes, export exact per-decision usage and playable replays."""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics
from .controller import make_payload,MODEL
from .engine import Snake,LEVELS
from .server import public_decision
ROOT=Path(__file__).resolve().parent

def analyze(path,export=True):
    path=Path(path);manifest=json.loads((path/'manifest.json').read_text());completion=json.loads((path/'completion.json').read_text())
    assert completion['planned']==completion['completed']==len(manifest['jobs'])
    episodes=[];usage=[];buckets=defaultdict(list);all_latencies=[]
    for level,controller,seed in manifest['jobs']:
        ident=f'{level}-{controller}-{seed}';saved=json.loads((path/(ident+'.json')).read_text())
        rows=[json.loads(line) for line in (path/(ident+'.jsonl')).read_text().splitlines()]
        game=Snake(level,seed,manifest['max_steps'],manifest['target'],manifest['starvation'])
        assert saved['initial']==game.snapshot();frames=[];inputs=outputs=calls=forced=0;latencies=[]
        for index,row in enumerate(rows):
            assert game.status=='playing' and row['before']==game.snapshot(),(ident,index,'before')
            if 'error' in row:
                assert index==len(rows)-1
                game.status='api_error';assert row['after']==game.snapshot()
                frames.append({'state':compact(game.snapshot()),'error':row['error']});continue
            d=row['decision'];action=d['action'];source=d['source']
            if source=='jev':
                assert controller!='baseline'
                if controller=='jev_guarded':assert len(game.legal())>=2
                payload=make_payload(game,controller);assert payload==d['payload']
                assert hashlib.sha256(json.dumps(payload).encode()).hexdigest()==d['payload_sha256']
                parsed=json.loads(d['raw_response']);assert parsed==d['response'] and parsed['model']==MODEL and d['http_status']==200
                assert set(parsed['answers'])=={'move'}
                a=parsed['answers']['move'];assert a['type']=='choice' and a['choice']==action
                opts=payload['questions']['move']['criteria'];assert action in opts and set(a['probabilities'])==set(opts)
                assert all(0<=p<=1 for p in a['probabilities'].values()) and abs(sum(a['probabilities'].values())-1)<.04
                assert 0<=a['confidence']<=1
                u=parsed['usage'];assert all(isinstance(u[k],int) and u[k]>=0 for k in ['input_tokens','output_tokens'])
                inputs+=u['input_tokens'];outputs+=u['output_tokens'];calls+=1;latencies.append(d['latency_ms'])
                usage.append({'episode':ident,'level':level,'controller':controller,'seed':seed,'move':index+1,'action':action,'input_tokens':u['input_tokens'],'output_tokens':u['output_tokens'],'latency_ms':d['latency_ms']})
            elif source=='baseline':assert controller=='baseline' and action==game.baseline()
            elif source=='forced_safe':assert controller=='jev_guarded' and game.legal()==[action];forced+=1
            elif source=='no_safe_move':assert controller=='jev_guarded' and not game.legal() and action=='straight'
            else:raise AssertionError(source)
            game.step(action);assert row['after']==game.snapshot(),(ident,index,'after')
            frames.append({'state':compact(game.snapshot()),'decision':public_decision(d)})
        assert game.status!='playing' and saved['final']==game.snapshot()
        assert (saved['score'],saved['moves'],saved['outcome'])==(game.score,game.moves,game.status)
        assert (saved['input_tokens'],saved['output_tokens'],saved['model_calls'],saved['forced_moves'])==(inputs,outputs,calls,forced)
        ep={**saved,'frames':frames,'trace':f'https://github.com/RINNECODER/jev-behavior-study/blob/main/snake_demo/records/{path.name}/{ident}.jsonl',
            'median_latency_ms':statistics.median(latencies) if latencies else None}
        episodes.append(ep);buckets[level,controller].append(ep);all_latencies+=latencies
    assert len({e['id'] for e in episodes})==len(episodes)
    assert completion['api_error_episodes']==sum(e['outcome']=='api_error' for e in episodes)
    metrics=[]
    for (level,controller),eps in sorted(buckets.items()):
        n=sum(e['model_calls'] for e in eps)
        ls=[r['latency_ms'] for r in usage if r['level']==level and r['controller']==controller]
        metrics.append({'level':level,'controller':controller,'episodes':len(eps),'mean_food':statistics.mean(e['score'] for e in eps),
            'median_food':statistics.median(e['score'] for e in eps),'best_food':max(e['score'] for e in eps),
            'target_successes':sum(e['outcome']=='target_reached' for e in eps),'endings':dict(Counter(e['outcome'] for e in eps)),
            'model_calls':n,'forced_moves':sum(e['forced_moves'] for e in eps),
            'mean_input_tokens_per_call':sum(e['input_tokens'] for e in eps)/n if n else None,
            'mean_output_tokens_per_call':sum(e['output_tokens'] for e in eps)/n if n else None,
            'median_latency_ms':statistics.median(ls) if ls else None,
            'p95_latency_ms':sorted(ls)[min(len(ls)-1,int(.95*len(ls)))] if ls else None,
            'best_episode':max(eps,key=lambda e:(e['score'],-e['moves']))['id']})
    summary={'run':path.name,'pilot':manifest['pilot'],'episodes':len(episodes),'model':MODEL,'model_calls':len(usage),
        'input_tokens':sum(r['input_tokens'] for r in usage),'output_tokens':sum(r['output_tokens'] for r in usage),
        'api_error_episodes':completion['api_error_episodes'],'metrics':metrics,'target':manifest['target']}
    (path/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    if usage:
        with (path/'per_decision_usage.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(usage[0]),lineterminator='\n');w.writeheader();w.writerows(usage)
    if export:
        bundle={**summary,'levels':LEVELS,'runs':sorted(episodes,key=lambda e:e['id'])}
        (ROOT/'web'/'data.js').write_text('window.SNAKE_DATA = '+json.dumps(bundle,separators=(',',':'))+';\n')
    print(json.dumps(summary,indent=2));return summary

def compact(state):return {k:state[k] for k in ['snake','food','heading','score','moves','since_food','status']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--no-export',action='store_true');a=p.parse_args();analyze(a.path,not a.no_export)
