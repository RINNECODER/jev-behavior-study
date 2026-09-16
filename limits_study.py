"""Frozen decision, full-permutation, and difficulty panels; one question per call."""
import json
from itertools import permutations
from pathlib import Path
from behavior_study import payload,q,YN,run

HYPOTHESES=[
 'Descriptive choices and a live prerequisite-to-decision pipeline outperform direct choices on new scenarios.',
 'Arithmetic choices vary across all 24 permutations despite fixed meanings and IDs.',
 'Accuracy declines with logical depth, number of tracked objects, or competing records.'
]
ITEMS=[('laptop','screen repair'),('violin','string replacement'),('camera','sensor cleaning'),
 ('printer','roller replacement'),('sewing machine','motor repair'),('guitar','neck adjustment'),
 ('vacuum cleaner','motor inspection'),('blender','blade replacement'),('headphones','cable repair'),
 ('drone','propeller replacement'),('projector','lens cleaning'),('game console','port repair')]

def scenarios():
    out=[]
    for i,(item,service) in enumerate(ITEMS):
        for kind in ['service','inspection','collection','appointment']:
            lead=f'I am at home and the service shop is a five-minute walk away. '
            if kind=='service':facts=f'My {item} is at home. I am going to the shop to have its {service} performed there today.'
            elif kind=='inspection':facts=f'My {item} is at home. The technician needs to examine this exact item in person at the shop today.'
            elif kind=='collection':facts=f'My {item} is already at the shop after its {service}. I am going there to collect it.'
            else:facts=f'My {item} is at home. I am going to the shop only to book a future {service} appointment. The shop explicitly says not to bring the item for this booking visit.'
            label='bring' if kind in ['service','inspection'] else 'go_without'
            out.append(dict(id=f'{i}-{kind}',item=item,kind=kind,facts=lead+facts,label=label))
    return out

def decision(s,described=False,reverse=False):
    opts={'bring':'Bring it','go_without':'Go without it'}
    if described:opts={'bring':f'Bring my {s["item"]} from home to the shop on this visit.',
        'go_without':f'Go to the shop without bringing my {s["item"]} from home on this visit.'}
    if reverse:opts=dict(reversed(list(opts.items())))
    return q(f'To accomplish my stated purpose for this visit, should I bring my {s["item"]} from home or go without bringing it?',opts)

def cases():
    out=[]
    def add(id,group,state,question,expected,reps=3,**factors):
        out.append(dict(id=id,group=group,payload=payload(state,{'answer':question}),expected={'answer':expected},repetitions=reps,factors=factors))
    for s in scenarios():
        for reverse in [False,True]:
            for mode in ['direct','described','check']:
                question=decision(s,mode=='described',reverse)
                label=s['label']
                if mode=='check':
                    opts=dict(reversed(list(YN.items()))) if reverse else YN
                    question=q(f'Does accomplishing my stated purpose for this visit require bringing my {s["item"]} from home to the shop? Answer yes if required, no if not required, or cannot_be_determined if the facts do not establish this.',opts)
                    label='yes' if label=='bring' else 'no'
                add(f'decision-{s["id"]}-{mode}-{reverse}','decision',s['facts'],question,label,
                    scenario=s['id'],kind=s['kind'],mode=mode,reverse=reverse,label=s['label'])
    numbers=[(4,9,7,3),(8,7,11,5),(13,11,23,8),(27,16,73,21),(43,19,97,32),(132,25,329,61)]
    for i,(boxes,each,sold,received) in enumerate(numbers):
        values=[boxes*each-sold+received,boxes*each-sold-received,boxes*each+sold+received,boxes*each-sold]
        assert len(set(values))==4
        opts={f'v{j}':str(v) for j,v in enumerate(values)}
        state=f'A shop has {boxes} boxes of {each} pens each. It sells {sold} pens and receives {received} loose pens. How many pens does it now have?'
        for j,order in enumerate(permutations(opts)):
            add(f'permutation-{i}-{j}','permutation',state,q('Select the exact number of pens now in the shop.',{k:opts[k] for k in order}),'v0',
                template=i,order=list(order),correct_position=order.index('v0')+1)
    for depth in [1,2,4,8,16,32]:
        for sample in range(3):
            for label in ['yes','no','cannot_be_determined']:
                rules=[f'If object Z is in category K{j}, then it is in category K{j+1}.' for j in range(depth)]
                if label=='yes':fact='Object Z is in category K0.';target=depth
                elif label=='no':fact=f'Object Z is not in category K{depth}.';target=0
                else:fact=f'Object Z is in category K{depth}.';target=0
                if sample==1:rules.reverse()
                elif sample==2:rules=rules[::2]+rules[1::2]
                state='Only the following one-way rules and fact are given. Do not assume converse rules. '+' '.join(rules)+' '+fact
                question=q(f'Is object Z in category K{target}? Choose yes if necessarily true, no if necessarily false, or cannot_be_determined if either is possible.',YN)
                add(f'logic-{depth}-{sample}-{label}','logic_depth',state,question,label,depth=depth,order=sample,label=label)
    rooms=['kitchen','hall','garden','office']
    for count in [1,2,4,8,16]:
        for sample in range(3):
            loc={j:rooms[(j+sample)%4] for j in range(count)}
            facts=[f'Item I{j} starts in the {loc[j]}.' for j in range(count)]
            import random
            rng=random.Random(20260920+count*10+sample)
            for step in range(5):
                for j in range(count):
                    dest=rng.choice([r for r in rooms if r!=loc[j]])
                    facts.append(f'Ada moves item I{j} from the {loc[j]} to the {dest}.');loc[j]=dest
                    facts.append(f'Ben visits the {rooms[(j+step+2)%4]} without moving any item.')
            target=(sample*3)%count
            add(f'tracking-{count}-{sample}','multi_tracking',' '.join(facts),q(f'Where is item I{target} after all events?',{r:r for r in rooms}),loc[target],objects=count,sample=sample,target=target)
    for distractors in [0,16,128,512]:
        for position in ['start','middle','end']:
            for sample in range(3):
                other=[f'Asset A{j:04d}, version {j%7+1}, color { ["red","blue","green","yellow"][j%4]}.' for j in range(distractors)]
                # Conflicting records are explicitly versioned; the highest version wins.
                colors=['red','blue','green','yellow'];colors=colors[sample:]+colors[:sample]
                relevant=[f'Asset TARGET, version {v}, color {colors[v-1]}.' for v in [2,4,1,3]]
                index={'start':0,'middle':len(other)//2,'end':len(other)}[position]
                state='Each asset has versioned color records. Its current color is the record with the highest version number, regardless of text order.\n'+'\n'.join(other[:index]+relevant+other[index:])
                add(f'records-{distractors}-{position}-{sample}','competing_records',state,q('What is the current color of asset TARGET?',{c:c for c in ['red','blue','green','yellow']}),colors[3],distractors=distractors,position=position,sample=sample)
    assert len({c['id'] for c in out})==len(out)
    return out

def pipeline_cases(source):
    source=Path(source)
    manifest=json.loads((source/'manifest.json').read_text());lookup={c['id']:c for c in manifest['cases']}
    scenario={s['id']:s for s in scenarios()};out=[]
    rows=[json.loads(s) for s in (source/'results.jsonl').read_text().splitlines()]
    for row in rows:
        c=lookup[row['case_id']];f=c['factors']
        if c['group']!='decision' or f['mode']!='check':continue
        assert 'error' not in row
        s=scenario[f['scenario']];answer=row['response']['answers']['answer']['choice']
        state=s['facts']+'\nA prior prerequisite check asked whether accomplishing this visit requires bringing the item from home. Its selected answer was: '+answer+'. Use this check together with the original facts to make the final decision.'
        out.append(dict(id=f'pipeline-{row["trial"]}',group='pipeline',payload=payload(state,{'answer':decision(s,False,f['reverse'])}),
            expected={'answer':s['label']},repetitions=1,factors=dict(scenario=s['id'],kind=s['kind'],mode='pipeline',reverse=f['reverse'],label=s['label'],
                source_run=source.name,source_trial=row['trial'],source_case_id=c['id'],source_repetition=row['repetition'],check_answer=answer,check_correct=row['all_correct'])))
    assert len(out)==288
    return out

if __name__=='__main__':run(cases,'limits-study',20260920,HYPOTHESES)
