"""Offline-only labels. Never imported by the model policy or game runner."""
from collections import defaultdict,Counter
import csv
import hashlib
import json
from pathlib import Path
from ..engine import Snake,ACTIONS
from ..research.efficient import certify
from ..research.experiment import dump
from ..research.analyze import wilson
from .policy import VARIANTS,payload,observation
from .run import state_game


def check_decision(g,variant,history,order,d,ident,usage):
    first=None;last=None
    assert 1<=len(d['calls'])<=2
    for i,entry in enumerate(d['calls']):
        assert i==0 or variant=='review';stage='proposal' if i==0 else 'review';assert entry['stage']==stage
        p,m=payload(g,variant,history,order,first if i else None);c=entry['record']
        assert c['payload']==p and hashlib.sha256(json.dumps(p).encode()).hexdigest()==c['payload_sha256']
        record={'id':ident,'variant':variant,'stage':stage,'valid':c['valid'],'latency_ms':c['latency_ms'],'input_tokens':None,'output_tokens':None,'choice':None}
        if c['valid']:
            r=json.loads(c['raw_response']);assert r==c['response'] and r['model']=='jev-1.13.0' and c['http_status']==200
            a=r['answers']['move'];assert a['type']=='choice' and a['choice'] in m and set(a['probabilities'])==set(m)
            assert all(0<=x<=1 for x in a['probabilities'].values()) and abs(sum(a['probabilities'].values())-1)<.04
            last=m[a['choice']];record.update(r['usage']);record['choice']=last
            if i==0:first=last
        else:
            assert i==len(d['calls'])-1 and d['action'] is None;last=None
        usage.append(record)
    assert first==d['first_action'];assert last==d['action']
    if variant=='review' and d['calls'][0]['record']['valid']:assert len(d['calls'])==2
    else:assert len(d['calls'])==1


def score(g,d,o):
    a=d['action'];first=d['first_action'];resolved=o['resolved'] and bool(o['optimal'])
    return {'attempts':1,'valid_decisions':int(a is not None),'legal':int(a is not None and g.safe(a)),
      'oracle_resolved':int(resolved),'oracle_unknown':int(not resolved),'shortest':int(resolved and a in o['optimal']),
      'first_shortest':int(resolved and first in o['optimal']),'revisions':int(a is not None and first!=a),
      'review_improved':int(resolved and first not in o['optimal'] and a in o['optimal']),
      'review_worsened':int(resolved and first in o['optimal'] and a is not None and a not in o['optimal'])}


def write_usage(directory,usage):
    with (directory/'per_question.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(usage[0]),lineterminator='\n');w.writeheader();w.writerows(usage)


def screen(directory):
    manifest=json.loads((directory/'manifest.json').read_text());completion=json.loads((directory/'completion.json').read_text());assert completion['completed']==completion['planned']==len(manifest['jobs'])
    corpus={x['id']:x for x in json.loads((directory/'corpus.json').read_text())};oracles={sid:certify(state_game(x['state'])) for sid,x in corpus.items()}
    totals=defaultdict(Counter);usage=[];scored=[]
    for job in manifest['jobs']:
        r=json.loads((directory/(job['id']+'.json')).read_text());assert r['job']==job
        item=corpus[job['state_id']];g=state_game(item['state']);d=r['decision'];v=job['variant']
        check_decision(g,v,item['history'],job['order'],d,job['id'],usage)
        s=score(g,d,oracles[job['state_id']]);totals[v].update(s);scored.append({'id':job['id'],'state_id':job['state_id'],'variant':v,'action':d['action'],'score':s})
    for v in totals:
        calls=[r for r in usage if r['variant']==v];totals[v].update({'calls':len(calls),'valid_calls':sum(r['valid'] for r in calls),'input_tokens':sum(r['input_tokens'] or 0 for r in calls),'output_tokens':sum(r['output_tokens'] or 0 for r in calls)})
    candidates=[v for v in VARIANTS if v!='original']
    selected=sorted(candidates,key=lambda v:(-totals[v]['shortest']/totals[v]['attempts'],-totals[v]['legal'],totals[v]['calls'],VARIANTS.index(v)))[:3]
    result={'metrics':{k:dict(v) for k,v in totals.items()},'selected':selected,'oracle_resolved_states':sum(o['resolved'] for o in oracles.values())}
    dump(directory/'analysis.json',result);dump(directory/'offline_labels.json',oracles);dump(directory/'scored_decisions.json',scored);write_usage(directory,usage);return result


def games(directory):
    manifest=json.loads((directory/'manifest.json').read_text());completion=json.loads((directory/'completion.json').read_text());assert completion['completed']==completion['planned']==len(manifest['jobs'])
    groups=defaultdict(list);usage=[];labels=[];replays=[]
    for variant,seed in manifest['jobs']:
        ident=f'{variant}-{seed}';summary=json.loads((directory/(ident+'.json')).read_text());g=Snake(seed=seed);history=[];totals=Counter();seen=set();segments=[];segment_start=0;segment_min=None;frames=[]
        assert summary['initial']==g.snapshot()
        rows=[json.loads(line) for line in (directory/(ident+'.jsonl')).read_text().splitlines()]
        for i,r in enumerate(rows):
            assert r['before']==g.snapshot() and g.status=='playing'
            order=list(ACTIONS);offset=(seed+g.moves)%3;order=order[offset:]+order[:offset];d=r['decision']
            check_decision(g,variant,history,order,d,f'{ident}:{i+1}',usage)
            o=certify(g);s=score(g,d,o);totals.update(s);labels.append({'id':f'{ident}:{i+1}','oracle':o,'score':s})
            if g.moves==segment_start:segment_min=o['distance'] if o['resolved'] else None
            key=(tuple(g.body),g.heading,g.food);totals['repeated_states']+=key in seen;seen.add(key);before_score=g.score
            if d['action'] is None:g.status='api_error'
            else:history.append({'observation':observation(g),'action':d['action']});g.step(d['action'])
            assert r['after']==g.snapshot()
            if g.score>before_score:
                segments.append({'moves':g.moves-segment_start,'minimum_at_start':segment_min});segment_start=g.moves
            calls=[c['record'] for c in d['calls']];last=calls[-1]
            frames.append({'state':g.snapshot(),'decision':{'action':d['action'],'first_action':d['first_action'],'calls':[{'stage':entry['stage'],'usage':entry['record'].get('response',{}).get('usage'),'latency_ms':entry['record']['latency_ms']} for entry in d['calls']],
              'answer':last.get('response',{}).get('answers',{}).get('move'),'usage':last.get('response',{}).get('usage'),'latency_ms':sum(c['latency_ms'] for c in calls)},'offline_score':s})
        assert summary['final']==g.snapshot() and summary['moves']==g.moves and summary['food']==g.score
        own=[c for c in usage if c['id'].startswith(ident+':')]
        assert summary['calls']==len(own) and summary['valid_calls']==sum(c['valid'] for c in own)
        totals.update({'calls':len(own),'valid_calls':sum(c['valid'] for c in own),'input_tokens':sum(c['input_tokens'] or 0 for c in own),'output_tokens':sum(c['output_tokens'] or 0 for c in own)})
        groups[variant].append({'id':ident,'seed':seed,'food':g.score,'moves':g.moves,'outcome':g.status,'stats':dict(totals),'segments':segments})
        replays.append({'id':ident,'variant':variant,'seed':seed,'initial':summary['initial'],'final':summary['final'],'frames':frames})
    metrics={}
    for v,episodes in groups.items():
        totals=Counter()
        for e in episodes:totals.update(e['stats'])
        success=sum(e['outcome']=='target_reached' for e in episodes);segments=[s for e in episodes for s in e['segments']];eligible=[s for s in segments if s['minimum_at_start'] is not None]
        metrics[v]={'episodes':len(episodes),'successes':success,'success_wilson_95':wilson(success,len(episodes)),'total_food':sum(e['food'] for e in episodes),'mean_food':sum(e['food'] for e in episodes)/len(episodes),'endings':dict(Counter(e['outcome'] for e in episodes)),'stats':dict(totals),'completed_food_segments':len(segments),'scored_food_segments':len(eligible),'shortest_food_segments':sum(s['moves']==s['minimum_at_start'] for s in eligible)}
    result={'metrics':metrics,'episodes':dict(groups)}
    if manifest['phase']=='development_games':
        candidates=[v for v in manifest['variants'] if v!='original']
        result['selected']=sorted(candidates,key=lambda v:(-metrics[v]['successes'],-metrics[v]['total_food'],-metrics[v]['stats']['shortest']/metrics[v]['stats']['attempts'],metrics[v]['stats']['calls'],VARIANTS.index(v)))[:2]
    else:
        control={e['seed']:e for e in groups['original']};result['paired_vs_original']={}
        for v,episodes in groups.items():
            if v=='original':continue
            result['paired_vs_original'][v]={'food_wins':sum(e['food']>control[e['seed']]['food'] for e in episodes),'food_ties':sum(e['food']==control[e['seed']]['food'] for e in episodes),'food_losses':sum(e['food']<control[e['seed']]['food'] for e in episodes),'completion_wins':sum(e['outcome']=='target_reached' and control[e['seed']]['outcome']!='target_reached' for e in episodes),'completion_losses':sum(e['outcome']!='target_reached' and control[e['seed']]['outcome']=='target_reached' for e in episodes)}
    dump(directory/'analysis.json',result);dump(directory/'offline_labels.json',labels);dump(directory/'verified_replays.json',replays);write_usage(directory,usage);return result

if __name__=='__main__':
    import sys
    p=Path(sys.argv[1]);mode=json.loads((p/'manifest.json').read_text())['phase'];print(json.dumps(screen(p) if mode=='development_screen' else games(p),indent=2))
