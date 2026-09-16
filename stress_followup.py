"""Adaptive complexity follow-up after the initial difficulty panels hit ceiling."""
import random
from behavior_study import payload,q,YN,run
HYPOTHESES=['Scrambling names/rules and breaking chains reveals limits hidden by regular chain structure.',
 'Tracking carried versus dropped objects is harder than explicit object moves.',
 'Dispersed conflicting target records challenge highest-version selection in longer context.']

def cases():
    out=[]
    def add(id,group,state,question,expected,**factors):
        out.append(dict(id=id,group=group,payload=payload(state,{'answer':question}),expected={'answer':expected},repetitions=3,factors=factors))
    for depth in [8,32,128]:
        for sample in range(2):
            for label in ['yes','no','cannot_be_determined']:
                rng=random.Random(7300+depth+sample)
                names=[f'T{n}' for n in rng.sample(range(1000,9999),2*depth+3)]
                chain=names[:depth+1];other=names[depth+1:]
                edges=list(zip(chain,chain[1:]))+list(zip(other,other[1:]))
                if label=='cannot_be_determined':edges.remove((chain[depth//2],chain[depth//2+1]))
                rng.shuffle(edges)
                rules=[f'If Z has {a}, then Z has {b}.' for a,b in edges]
                fact=f'Z has {chain[0]}.' if label!='no' else f'Z does not have {chain[-1]}.'
                target=chain[-1] if label!='no' else chain[0]
                state='These are the only one-way rules and facts; do not assume converse rules. '+' '.join(rules)+' Fact: '+fact
                add(f'graph-{depth}-{sample}-{label}','scrambled_logic',state,q(f'Does Z have {target}? Choose yes if necessarily true, no if necessarily false, and cannot_be_determined if both are possible.',YN),label,depth=depth,sample=sample,label=label)
    rooms=['kitchen','hall','garden','office']
    for count in [8,16,32]:
        for sample in range(2):
            rng=random.Random(8400+count+sample)
            actor={j:rng.choice(rooms) for j in range(count)};object_loc=actor.copy();holding={j:True for j in actor}
            text=[f'Person P{j} is in the {actor[j]} holding item I{j}.' for j in actor]
            for step in range(5):
                order=list(actor);rng.shuffle(order)
                for j in order:
                    if step in [2,4]:
                        actor[j]=object_loc[j];text.append(f'P{j} goes to the {actor[j]} and picks up I{j}.');holding[j]=True
                    actor[j]=rng.choice([r for r in rooms if r!=actor[j]])
                    text.append(f'P{j} goes to the {actor[j]}.')
                    if holding[j]:object_loc[j]=actor[j]
                    if step in [1,3] or (step==4 and j%2==0):
                        text.append(f'P{j} puts down I{j} there.');holding[j]=False
                    if step==4:
                        actor[j]=rng.choice([r for r in rooms if r!=actor[j]]);text.append(f'P{j} goes to the {actor[j]}.')
                        if holding[j]:object_loc[j]=actor[j]
            target=sample%count
            state='People take held items with them when they move; items put down stay where left until picked up. '+' '.join(text)
            add(f'carry-{count}-{sample}','carry_tracking',state,q(f'Where is item I{target} after all events?',{r:r for r in rooms}),object_loc[target],objects=count,sample=sample,target=target)
    for count in [128,512,1024]:
        for position in ['start','middle','end']:
            for sample in range(2):
                colors=['red','blue','green','yellow'];colors=colors[sample:]+colors[:sample]
                records=[f'Asset A{j:04d}, version {j%7+1}, color {colors[j%4]}.' for j in range(count)]
                records.insert(len(records)//4,f'Asset TARGET, version 1, color {colors[0]}.')
                records.insert(len(records)//2,f'Asset TARGET, version 2, color {colors[1]}.')
                records.insert(3*len(records)//4,f'Asset TARGET, version 3, color {colors[2]}.')
                index={'start':0,'middle':len(records)//2,'end':len(records)}[position]
                records.insert(index,f'Asset TARGET, version 4, color {colors[3]}.')
                state='The current color of an asset is its highest-version record, regardless of text order.\n'+'\n'.join(records)
                add(f'dispersed-{count}-{position}-{sample}','dispersed_records',state,q('What is the current color of asset TARGET?',{r:r for r in ['red','blue','green','yellow']}),colors[3],distractors=count,position=position,sample=sample)
    return out
if __name__=='__main__':run(cases,'stress-followup',20260922,HYPOTHESES)
