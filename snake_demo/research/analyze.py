"""Regenerate evidence and describe effects without treating moves as IID games."""
from collections import defaultdict,Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from .experiment import ROOT,VARIANTS,dump,job_payload
from .oracle import restore,assess


def wilson(k,n):
    if not n:return None
    z=1.95996398454;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-half,center+half]


def summarize(rows):
    n=len(rows);valid=[r for r in rows if r['valid']];v=len(valid)
    result={'attempted':n,'valid':v,'errors':n-v}
    for key in ['correct','safe','argmax_correct','choice_is_argmax']:
        eligible=[r for r in valid if key in r]
        if eligible:
            k=sum(r[key] for r in eligible);result[key]={'count':k,'n':len(eligible),'rate':k/len(eligible),'wilson_95':wilson(k,len(eligible))}
    result['input_tokens']=sum(r.get('input_tokens',0) for r in rows);result['output_tokens']=sum(r.get('output_tokens',0) for r in rows)
    wrong=[r for r in valid if not r['correct']]
    result['wrong_confidence_ge_0_9']=sum(r['confidence']>=.9 for r in wrong)
    return result


def analyze(directory):
    corpus={i['id']:i for i in json.loads((directory/'corpus.json').read_text())};manifest=json.loads((directory/'manifest.json').read_text());rows=[];groups=defaultdict(list)
    for item in corpus.values():assert assess(restore(item['state']))==item['oracle']
    for job in manifest['jobs']:
        record=json.loads((directory/(job['id']+'.json')).read_text());assert record['job']==job
        item=corpus[job['state_id']];c=record['call'];payload,mapping=job_payload(job,item)
        assert json.loads(json.dumps(payload))==c['payload'] and mapping==record['mapping'];assert hashlib.sha256(json.dumps(payload).encode()).hexdigest()==c['payload_sha256']
        row={'id':job['id'],'state_id':job['state_id'],'split':item['split'],'kind':job['kind'],'variant':job.get('variant',job.get('predicate')),'valid':c['valid']}
        if c['valid']:
            p=json.loads(c['raw_response']);assert p==c['response'] and p['model']=='jev-1.13.0'
            answer=next(iter(p['answers'].values()));prob=answer['probabilities'];choice=answer['choice'];maximum=max(prob.values());tops=[k for k,v in prob.items() if v==maximum]
            row.update(p['usage']);row.update({'latency_ms':c['latency_ms'],'confidence':answer['confidence'],'choice':choice,'choice_is_argmax':choice in tops})
            if job['kind']=='atomic':
                g=restore(item['state']);a=job['action'];dest=g.destination(a)
                correct=g.safe(a) if job['predicate']=='safe' else abs(dest[0]-g.food[0])+abs(dest[1]-g.food[1])<abs(g.body[0][0]-g.food[0])+abs(g.body[0][1]-g.food[1])
                expected='yes' if correct else 'no';row['correct']=choice==expected;row['argmax_correct']=expected in tops
            else:
                action=mapping[choice];row['action']=action;row['correct']=action in item['oracle']['optimal'];row['safe']=action in item['oracle']['legal'];row['argmax_correct']=all(mapping[k] in item['oracle']['optimal'] for k in tops)
                row['regret']=None if item['oracle']['costs'][action] is None else item['oracle']['costs'][action]-item['oracle']['distance']
            assert sum(prob.values())>.95 and sum(prob.values())<1.05
        rows.append(row);groups[(row['split'],row['kind'],row['variant'])].append(row)
    metrics={'/'.join(k):summarize(v) for k,v in groups.items()};selection={}
    for category,variants in [('unassisted',VARIANTS[:3]),('assisted',VARIANTS[3:])]:
        # Error attempts count against selection; no exploiting an incomplete batch.
        def rank(v):
            m=metrics['development/ablation/'+v]
            return (m['correct']['count']/m['attempted'],m['safe']['count']/m['attempted'],-variants.index(v))
        selection[category]=max(variants,key=rank)
    paired={}
    for split in ['development','holdout']:
        by=defaultdict(dict)
        for r in rows:
            if r['split']==split and r['kind']=='ablation' and r['valid']:by[r['state_id']][r['variant']]=r
        for a,b in [('original','compact'),('compact','absolute'),('compact','local'),('local','exact')]:
            pairs=[x for x in by.values() if a in x and b in x];paired[f'{split}/{a}->{b}']={'n':len(pairs),'improved':sum(not x[a]['correct'] and x[b]['correct'] for x in pairs),'worsened':sum(x[a]['correct'] and not x[b]['correct'] for x in pairs)}
    orders=defaultdict(list)
    for r in rows:
        if r['kind']=='order' and r['valid']:orders[r['state_id']].append(r)
    repeat_pairs=[]
    for sid,rs in orders.items():
        by=defaultdict(list)
        for r in rs:by[r['id'].rsplit('-',1)[0]].append(r)
        repeat_pairs += [a[0]['action']!=a[1]['action'] for a in by.values() if len(a)==2]
    summary={'total':summarize(rows),'metrics':metrics,'selection':selection,'paired':paired,'order':{'states':len(orders),'states_with_multiple_choices':sum(len(set(r['action'] for r in rs))>1 for rs in orders.values()),'identical_payload_pairs':len(repeat_pairs),'different_choices_on_identical_payload':sum(repeat_pairs)}}
    dump(directory/'analysis.json',summary);dump(directory/'selection.json',{'selected_from':'development only','variants':selection,'rule':'shortest-action count/attempts, legal count/attempts, frozen listed order'})
    fields=sorted(set().union(*(r.keys() for r in rows)))
    with (directory/'per_question.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    return summary


def audit_old():
    old=ROOT.parent/'records'/'20260917T013832Z-benchmark';rows=[]
    for path in sorted(old.glob('classic-jev_*.jsonl')):
        for line in path.read_text().splitlines():
            row=json.loads(line);d=row.get('decision',{})
            if d.get('source')!='jev':continue
            o=assess(restore(row['before']));a=d['action'];answer=d['response']['answers']['move'];prob=answer['probabilities']
            rows.append({'episode':path.stem,'move':row['before']['moves']+1,'resolved':o['resolved'],'oracle':o,'action':a,'safe':a in o['legal'],'correct':a in o['optimal'] if o['resolved'] else None,'choice_is_argmax':prob[a]==max(prob.values()),'confidence':answer['confidence']})
    dump(ROOT/'records'/'old-classic-audit.json',rows)
    result={}
    for profile in ['jev_direct','jev_guarded']:
        subset=[r for r in rows if profile in r['episode']];resolved=[r for r in subset if r['resolved']]
        result[profile]={'calls':len(subset),'resolved':len(resolved),'legal':sum(r['safe'] for r in subset),'shortest':sum(r['correct'] for r in resolved),'choice_is_argmax':sum(r['choice_is_argmax'] for r in subset),'wrong_high_confidence':sum(not r['correct'] and r['confidence']>=.9 for r in resolved)}
    dump(ROOT/'records'/'old-classic-summary.json',result);return result

if __name__=='__main__':
    import sys
    print(json.dumps(audit_old() if len(sys.argv)<2 else analyze(Path(sys.argv[1])),indent=2))
