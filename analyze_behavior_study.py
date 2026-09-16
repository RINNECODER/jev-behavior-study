"""Verify and aggregate recorded study responses without calling the API."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parent


def analyze(path):
    manifest=json.loads((path/'manifest.json').read_text())
    cases={c['id']:c for c in manifest['cases']}
    rows=[json.loads(x) for x in (path/'results.jsonl').read_text().splitlines()]
    schedule=json.loads((path/'schedule.json').read_text())
    assert len(rows)==len(schedule)==sum(c['repetitions'] for c in cases.values())
    assert {r['trial'] for r in rows}==set(range(1,len(rows)+1))
    assert len({(r['case_id'],r['repetition']) for r in rows})==len(rows)
    grouped=defaultdict(list)
    question_rows=[]
    for r in rows:
        c=cases[r['case_id']]
        assert schedule[r['trial']-1]==[r['case_id'],r['repetition']]
        assert hashlib.sha256(json.dumps(c['payload']).encode()).hexdigest()==r['payload_sha256']
        assert r['http_status']==200 and 'error' not in r
        raw=json.loads(r['raw_response'])
        assert raw==r['response'] and raw['model']==manifest['model']
        flags=[]
        for name,target in c['expected'].items():
            a=raw['answers'][name]
            opts=c['payload']['questions'][name]['criteria']
            assert a['type']=='choice' and a['choice'] in opts
            assert set(a['probabilities'])==set(opts)
            assert all(0<=v<=1 for v in a['probabilities'].values())
            # API rounds displayed scores to two decimals.
            assert abs(sum(a['probabilities'].values())-1)<=0.061
            assert 0<=a['confidence']<=1
            correct=a['choice']==target
            assert correct==r['checks'][name]['correct']
            flags.append(correct)
            question_rows.append(dict(case_id=c['id'],group=c['group'],trial=r['trial'],question=name,
                expected=target,choice=a['choice'],correct=correct,confidence=a['confidence'],
                target_probability=a['probabilities'][target],top_probability=max(a['probabilities'].values()),
                brier=sum((v-(k==target))**2 for k,v in a['probabilities'].items())))
        assert all(flags)==r['all_correct']
        grouped[c['id']].append(r)
    case_rows=[]
    for id,c in cases.items():
        rs=grouped[id]
        assert len(rs)==c['repetitions']
        qs=[q for q in question_rows if q['case_id']==id]
        d=dict(id=id,group=c['group'],factors=c['factors'],requests=len(rs),correct=sum(r['all_correct'] for r in rs),
               accuracy=sum(r['all_correct'] for r in rs)/len(rs),question_count=len(qs),
               mean_target_probability=statistics.mean(q['target_probability'] for q in qs),
               mean_confidence=statistics.mean(q['confidence'] for q in qs),
               input_tokens=statistics.mean(r['response']['usage']['input_tokens'] for r in rs),
               output_tokens=statistics.mean(r['response']['usage']['output_tokens'] for r in rs),
               latency_ms=statistics.median(r['latency_ms'] for r in rs),
               selections={k:dict(Counter(r['response']['answers'][k]['choice'] for r in rs)) for k in c['expected']})
        case_rows.append(d)
    tables={}
    def tab(name,group,fields):
        buckets=defaultdict(list)
        for c in case_rows:
            if c['group']==group and all(f in c['factors'] for f in fields):buckets[tuple(c['factors'][f] for f in fields)].append(c)
        table=[]
        for key,cs in buckets.items():
            n=sum(c['requests'] for c in cs); k=sum(c['correct'] for c in cs)
            table.append(dict(zip(fields,key),conditions=len(cs),requests=n,correct=k,accuracy=k/n,
                              input_tokens=sum(c['input_tokens']*c['requests'] for c in cs)/n,
                              output_tokens=sum(c['output_tokens']*c['requests'] for c in cs)/n))
        tables[name]=table
    for field in ['placement','wording','unknown','reverse']: tab('factor_'+field,'factorial',[field])
    tab('factor_placement_wording','factorial',['placement','wording'])
    tab('transfer_mode','transfer',['mode'])
    tab('transfer_label','transfer',['mode','label'])
    tab('transfer_scenarios','transfer',['scenario','mode'])
    tab('length','length',['filler_words','mode'])
    tab('length_filler','length',['filler_words','filler','mode'])
    tab('length_position','length',['filler_words','position','mode'])
    tab('long_transfer','long_transfer',['filler_words','mode','label'])
    tab('counting','counting',['form'])
    tab('counting_words','counting',['word','form'])
    tab('described_transfer','described_transfer',['cohort','label','reverse'])
    tab('described_scenarios','described_transfer',['scenario','cohort'])
    tab('distance','distance',['distance'])
    tab('replication','replication',['placement','wording'])
    tab('count_followup','count_followup',['word','placement','wording'])
    tab('evidence','evidence',['evidence'])
    # Per-answer confidence bins are diagnostics on this selected synthetic suite,
    # not an estimate of production calibration.
    bins=[]
    for low,high in [(0,.5),(.5,.8),(.8,.95),(.95,1.00001)]:
        subset=[q for q in question_rows if low<=q['confidence']<high]
        bins.append({'low':low,'high':min(high,1),'answers':len(subset),'accuracy':statistics.mean(q['correct'] for q in subset) if subset else None})
    summary={'run':path.name,'requests':len(rows),'conditions':len(cases),'answers':len(question_rows),
             'errors':0,'models':dict(Counter(r['response']['model'] for r in rows)),
             'input_tokens':sum(r['response']['usage']['input_tokens'] for r in rows),
             'output_tokens':sum(r['response']['usage']['output_tokens'] for r in rows),
             'first_request':min(r['started_at'] for r in rows),'last_request':max(r['started_at'] for r in rows),
             'max_input_tokens':max(r['response']['usage']['input_tokens'] for r in rows),
             'case_results':case_rows,'tables':tables,'confidence_bins':bins,
             'validation':'Every raw response, hash, schedule entry, model, selected-answer label, question key, displayed probability set/range and request count verified. Rounded displayed probability sums allowed tolerance 0.061.'}
    (path/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (path/'conditions.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(case_rows[0]), lineterminator="\n"); w.writeheader()
        for r in case_rows:w.writerow({k:json.dumps(v) if isinstance(v,dict) else v for k,v in r.items()})
    with (path/'answers.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(question_rows[0]), lineterminator="\n");w.writeheader();w.writerows(question_rows)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['case_results','tables']},indent=2))
    for k in ['factor_placement_wording','factor_unknown','factor_reverse','transfer_mode','transfer_label','length','long_transfer','counting']:
        print(k,json.dumps(tables[k]))
    print('BATCH/KEY/OPTIONS',json.dumps([c for c in case_rows if c['group'] in ['batching','question_key','options']]))
    return summary


if __name__=='__main__': analyze(Path(sys.argv[1]))
