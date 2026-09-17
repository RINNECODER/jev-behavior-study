"""Verify entire episodes, independent segment certificates, usage and assistance."""
from collections import defaultdict,Counter
import csv
import hashlib
import json
from pathlib import Path
from ..engine import Snake,ACTIONS
from .oracle import assess,restore
from .experiment import dump,payload_for
from .analyze import wilson


def verify(directory):
    manifest=json.loads((directory/'manifest.json').read_text());completion=json.loads((directory/'completion.json').read_text())
    assert completion['planned']==completion['completed']==len(manifest['jobs'])
    groups=defaultdict(list);usage=[];replays=[]
    for profile,variant,seed in manifest['jobs']:
        ident=f'{profile}-{seed}';summary=json.loads((directory/(ident+'.json')).read_text())
        g=Snake(seed=seed,target=manifest.get('target',8),max_steps=manifest.get('max_steps',200));assert summary['initial']==g.snapshot()
        rows=[json.loads(x) for x in (directory/(ident+'.jsonl')).read_text().splitlines()]
        stats=Counter();segments=[];segment_start=0;segment_min=None;seen=set();frames=[]
        for i,row in enumerate(rows):
            assert row['before']==g.snapshot() and g.status=='playing'
            if 'error' in row:
                assert i==len(rows)-1;g.status='planner_error';assert row['after']==g.snapshot();stats['planner_errors']+=1;continue
            d=row['decision'];o=assess(g);assert d['oracle']==o and o['resolved'] and o['optimal']
            if segment_min is None:segment_min=o['distance']
            fingerprint=(tuple(g.body),g.heading,g.food)
            stats['repeated_states']+=fingerprint in seen;seen.add(fingerprint)
            c=d['call'];before_score=g.score
            if c:
                order=list(ACTIONS);offset=(g.seed+g.moves)%3;order=order[offset:]+order[:offset]
                payload,mapping=payload_for(g,'exact' if profile=='verified' else variant,o,order)
                assert payload==c['payload'] and mapping==d['mapping']
                assert hashlib.sha256(json.dumps(payload).encode()).hexdigest()==c['payload_sha256']
                stats['attempted_calls']+=1
                if not c['valid']:
                    assert i==len(rows)-1 and d['action'] is None;g.status='api_error';stats['api_errors']+=1
                    assert row['after']==g.snapshot();frames.append({'state':row['after'],'error':c.get('error')});continue
                r=json.loads(c['raw_response']);assert r==c['response'] and r['model']=='jev-1.13.0'
                answer=r['answers']['move'];proposal=mapping[answer['choice']];assert proposal==d['proposal']
                stats['valid_calls']+=1;stats['model_shortest']+=proposal in o['optimal'];stats['model_legal']+=proposal in o['legal']
                usage.append({'episode':ident,'profile':profile,'move':i+1,'input_tokens':r['usage']['input_tokens'],'output_tokens':r['usage']['output_tokens'],'latency_ms':c['latency_ms'],'planner_ms':d['planner_ms'],'proposal':proposal,'action':d['action'],'overridden':d['overridden'],'shortest':proposal in o['optimal']})
                expected=proposal if profile!='verified' or proposal in o['optimal'] else o['optimal'][0]
                assert expected==d['action'];assert d['overridden']==(proposal!=expected)
                stats['input_tokens']+=r['usage']['input_tokens'];stats['output_tokens']+=r['usage']['output_tokens']
            else:assert profile=='oracle' and d['action']==o['optimal'][0] and not d['overridden']
            # Validate EACH supplied path against actual game transition rules.
            for a,path in o['paths'].items():
                if path is None:continue
                h=restore(g.snapshot());h.max_steps=1000000;h.starvation=1000000;h.target=1000000
                for action in path:h.step(action)
                assert h.score==g.score+1 and len(path)==o['costs'][a]
            stats['executed_moves']+=1;stats['executed_shortest']+=d['action'] in o['optimal'];stats['overrides']+=d['overridden']
            g.step(d['action']);assert row['after']==g.snapshot()
            if g.score>before_score:
                segments.append({'moves':g.moves-segment_start,'minimum_at_start':segment_min,'efficient':g.moves-segment_start==segment_min})
                segment_min=None;segment_start=g.moves
            frames.append({'state':row['after'],'decision':{'action':d['action'],'proposal':d['proposal'],'overridden':d['overridden'],'oracle':o,'planner_ms':d['planner_ms'],'answer':c['response']['answers']['move'] if c and c['valid'] else None,'usage':c['response']['usage'] if c and c['valid'] else {'input_tokens':0,'output_tokens':0},'latency_ms':c['latency_ms'] if c else 0}})
        assert g.snapshot()==summary['final'] and g.moves==summary['moves'] and g.score==summary['score']
        assert stats['overrides']==summary['overrides'] and stats['valid_calls']==summary['valid_calls']
        entry={**summary,'stats':dict(stats),'segments':segments};groups[profile].append(entry)
        replays.append({'id':ident,'profile':profile,'seed':seed,'initial':summary['initial'],'final':summary['final'],'frames':frames})
    result={}
    for profile,episodes in groups.items():
        totals=Counter()
        for e in episodes:totals.update(e['stats'])
        n=len(episodes);success=sum(e['outcome']=='target_reached' for e in episodes);segments=[s for e in episodes for s in e['segments']]
        result[profile]={'episodes':n,'successes':success,'success_wilson_95':wilson(success,n),'mean_food':sum(e['score'] for e in episodes)/n,'endings':dict(Counter(e['outcome'] for e in episodes)),'stats':dict(totals),'food_segments':len(segments),'shortest_food_segments':sum(s['efficient'] for s in segments),'segment_efficiency':sum(s['minimum_at_start'] for s in segments)/sum(s['moves'] for s in segments) if segments else None}
    dump(directory/'analysis.json',result)
    if usage:
        with (directory/'per_question.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(usage[0]),lineterminator="\n");w.writeheader();w.writerows(usage)
    dump(directory/'verified_replays.json',replays)
    return result

if __name__=='__main__':
    import sys
    print(json.dumps(verify(Path(sys.argv[1])),indent=2))
