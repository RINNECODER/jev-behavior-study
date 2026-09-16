"""Verify and analyze both phases, including exact dependency and token accounting."""
import csv
import json
import statistics
import sys
from collections import defaultdict,Counter
from pathlib import Path
from analyze_behavior_study import analyze
from limits_study import cases,pipeline_cases

def read(path):
    return ({c['id']:c for c in json.loads((path/'manifest.json').read_text())['cases']},
        [json.loads(s) for s in (path/'results.jsonl').read_text().splitlines()])

def analyze_all(first,second):
    for path in [first,second]:analyze(path)
    c1,r1=read(first);c2,r2=read(second)
    assert list(c1.values())==cases()
    assert list(c2.values())==pipeline_cases(first)
    source={r['trial']:r for r in r1};bins=defaultdict(list);csvrows=[];workflows=[]
    for path,cs,rs in [(first,c1,r1),(second,c2,r2)]:
        for r in rs:
            c=cs[r['case_id']];f=c['factors'];a=r['response']['answers']['answer'];u=r['response']['usage'];g=c['group']
            out=dict(run=path.name,trial=r['trial'],case_id=c['id'],family=g,expected=c['expected']['answer'],choice=a['choice'],correct=r['all_correct'],
                input_tokens=u['input_tokens'],output_tokens=u['output_tokens'],confidence=a['confidence'])
            csvrows.append(out)
            if g in ['decision','pipeline']:
                bins['decision',f['mode']].append(out)
                bins['decision_kind',f['mode'],f['kind']].append(out)
                bins['decision_order',f['mode'],f['reverse']].append(out)
            elif g=='permutation':
                bins['position',f['correct_position']].append(out)
                bins['arithmetic_template',f['template']].append(out)
                bins['template_position',f['template'],f['correct_position']].append(out)
            elif g=='logic_depth':
                bins[g,f['depth']].append(out);bins['logic_label',f['label']].append(out)
                bins['logic_order',f['order']].append(out)
            elif g=='multi_tracking':bins[g,f['objects']].append(out)
            elif g=='competing_records':
                bins[g,f['distractors']].append(out);bins['record_position',f['distractors'],f['position']].append(out)
            if g=='pipeline':
                prior=source[f['source_trial']];pu=prior['response']['usage']
                assert f['check_answer']==prior['response']['answers']['answer']['choice']
                assert f['check_correct']==prior['all_correct']
                workflows.append(dict(scenario=f['scenario'],reverse=f['reverse'],source_trial=f['source_trial'],final_trial=r['trial'],
                    check_correct=prior['all_correct'],final_correct=r['all_correct'],joint_correct=prior['all_correct'] and r['all_correct'],
                    check_input_tokens=pu['input_tokens'],check_output_tokens=pu['output_tokens'],
                    final_input_tokens=u['input_tokens'],final_output_tokens=u['output_tokens'],
                    workflow_input_tokens=pu['input_tokens']+u['input_tokens'],workflow_output_tokens=pu['output_tokens']+u['output_tokens']))
    assert len({w['source_trial'] for w in workflows})==len(workflows)==288
    tables=[]
    for key,rs in sorted(bins.items(),key=lambda kv:str(kv[0])):
        tables.append(dict(panel=key[0],condition=list(key[1:]),correct=sum(r['correct'] for r in rs),n=len(rs),
            input_tokens_mean=statistics.mean(r['input_tokens'] for r in rs),output_tokens_mean=statistics.mean(r['output_tokens'] for r in rs)))
    permutation=[]
    for t in range(6):
        rs=[r for r in r1 if c1[r['case_id']]['group']=='permutation' and c1[r['case_id']]['factors']['template']==t]
        permutation.append(dict(template=t,choices=dict(Counter(r['response']['answers']['answer']['choice'] for r in rs)),
            perfect_permutations=sum(all(r['all_correct'] for r in rs if r['case_id']==c['id']) for c in c1.values() if c['group']=='permutation' and c['factors']['template']==t)))
    summary=dict(runs=[first.name,second.name],requests=len(csvrows),tables=tables,permutation_templates=permutation,
        pipeline_joint_correct=sum(w['joint_correct'] for w in workflows),pipeline_n=len(workflows),
        wrong_checks=sum(not w['check_correct'] for w in workflows),rescued_wrong_checks=sum(not w['check_correct'] and w['final_correct'] for w in workflows),
        correct_checks_wrong_final=sum(w['check_correct'] and not w['final_correct'] for w in workflows),
        workflow_input_tokens_mean=statistics.mean(w['workflow_input_tokens'] for w in workflows),
        workflow_output_tokens_mean=statistics.mean(w['workflow_output_tokens'] for w in workflows),
        input_tokens=sum(r['input_tokens'] for r in csvrows),output_tokens=sum(r['output_tokens'] for r in csvrows),
        max_input_tokens=max(r['input_tokens'] for r in csvrows))
    for path in [first,second]:
        selected=[r for r in csvrows if r['run']==path.name]
        with (path/'per_question.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(selected[0]),lineterminator='\n');w.writeheader();w.writerows(selected)
    with (second/'workflow_usage.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(workflows[0]),lineterminator='\n');w.writeheader();w.writerows(workflows)
    (second/'limits_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('LIMITS SUMMARY',json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':analyze_all(Path(sys.argv[1]),Path(sys.argv[2]))
