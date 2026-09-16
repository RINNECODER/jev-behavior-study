"""Recompute all extension metrics and per-question token usage from raw responses."""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from analyze_behavior_study import analyze

def main(path):
    analysis=analyze(path)
    cases={c['id']:c for c in json.loads((path/'manifest.json').read_text())['cases']}
    rows=[json.loads(s) for s in (path/'results.jsonl').read_text().splitlines()]
    buckets=defaultdict(list)
    per_question=[]
    for r in rows:
        c=cases[r['case_id']]; a=r['response']['answers']['answer']; u=r['response']['usage']
        eligible=c['group']!='conditional'
        keys=[(c['group'],c['factors']['mode'])]
        if eligible: keys.append(('ALL',c['factors']['mode']))
        for key in keys: buckets[key].append(r)
        per_question.append(dict(trial=r['trial'],case_id=c['id'],family=c['group'],
            mode=c['factors']['mode'],expected=c['expected']['answer'],choice=a['choice'],
            correct=r['all_correct'],score_eligible=eligible,confidence=a['confidence'],input_tokens=u['input_tokens'],output_tokens=u['output_tokens']))
    metrics=[]
    for (family,mode),rs in sorted(buckets.items()):
        metrics.append(dict(family=family,mode=mode,score_eligible=family!='conditional',correct=sum(r['all_correct'] for r in rs),n=len(rs),
            mean_input_tokens=statistics.mean(r['response']['usage']['input_tokens'] for r in rs),
            mean_output_tokens=statistics.mean(r['response']['usage']['output_tokens'] for r in rs)))
    with (path/'per_question.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(per_question[0]),lineterminator='\n');w.writeheader();w.writerows(per_question)
    (path/'extension_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print('EXTENSION_METRICS',json.dumps(metrics))
    print('IMPERFECT_PLAIN',json.dumps([c for c in analysis['case_results'] if c['factors']['mode']=='plain' and c['accuracy']<1]))

if __name__=='__main__': main(Path(sys.argv[1]))
