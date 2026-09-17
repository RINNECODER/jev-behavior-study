"""Replay v2 code-only trajectories and independently execute path witnesses."""
from collections import Counter
import json
from pathlib import Path
from ..engine import Snake
from .oracle import restore
from .efficient import certify
from .experiment import dump


def verify(directory):
    manifest=json.loads((directory/'manifest.json').read_text());completion=json.loads((directory/'completion.json').read_text())
    assert not manifest['model'],'This verifier is for the conditional code-only branch'
    assert completion['completed']==completion['planned']==len(manifest['seeds'])
    totals=Counter();episodes=[]
    for seed in manifest['seeds']:
        g=Snake(seed=seed,target=24,max_steps=600);p=directory/f'oracle-{seed}.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
        segments=[];start=0;minimum=None
        for i,r in enumerate(rows):
            assert r['before']==g.snapshot();c=r['certificate']
            # Recompute all successful certificates. Terminal unknowns preserve
            # the budget failure and are not classified as a gameplay collision.
            if c['resolved']:
                assert certify(g)==c
                assert r['action']==c['optimal'][0] and r['call'] is None
                if minimum is None:minimum=c['distance']
                for a in c['optimal']:
                    h=restore(g.snapshot());h.max_steps=1000000;h.starvation=1000000;h.target=1000000
                    for action in c['paths'][a]:h.step(action)
                    assert h.score==g.score+1 and len(c['paths'][a])==c['distance']
                score=g.score;g.step(r['action']);totals['executed_moves']+=1
                if g.score>score:segments.append({'moves':g.moves-start,'minimum':minimum});start=g.moves;minimum=None
            else:
                assert i==len(rows)-1 and r['action'] is None and r['call'] is None
                assert c['root_status'] in ['budget_exhausted','unreachable'] or 'budget_exhausted' in c['status'].values()
                g.status='no_route' if c['root_status']=='unreachable' else 'planner_unknown'
                totals['terminal_'+c['root_status']]+=1
            assert g.snapshot()==r['after']
        s=json.loads((directory/f'oracle-{seed}.json').read_text());assert s['final']==g.snapshot() and s['moves']==g.moves
        assert all(x['moves']==x['minimum'] for x in segments)
        totals['food_segments']+=len(segments);totals[g.status]+=1
        episodes.append({'seed':seed,'score':g.score,'moves':g.moves,'outcome':g.status})
    result={'episodes':len(episodes),'successes':totals['target_reached'],'totals':dict(totals),'games':episodes,'verification_scope':'All transitions, successful certificates, and path witnesses recomputed. Terminal unknown budget records checked structurally, not rerun.'}
    dump(directory/'analysis.json',result);return result

if __name__=='__main__':
    import sys
    print(json.dumps(verify(Path(sys.argv[1])),indent=2))
