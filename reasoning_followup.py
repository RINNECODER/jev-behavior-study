"""Adaptive follow-up: resolve pilot entailment ambiguity and probe harder exact tasks."""
from itertools import product
from behavior_study import payload,q,run,YN
HYPOTHESES=[
 'Three-way truth-status wording resolves the pilot entailment ambiguity.',
 'Conditional reasoning transfers across eight distinct rule templates.',
 'Counting remains sensitive to spacing on novel strings.',
 'Multi-step arithmetic remains accurate with irrelevant quantities.',
 'Object tracking transfers to longer sequences.'
]

def cases():
    out=[]
    def add(group,ident,facts,text,opts,label,**factors):
        for mode in ['plain','reversed','explicit']:
            options=dict(reversed(list(opts.items()))) if mode=='reversed' else opts
            instruction=text if mode!='explicit' else 'Use only the supplied facts and rules. Do not assume unstated facts. Check the exact requested condition before selecting an answer. '+text
            out.append(dict(id=f'{group}-{ident}-{mode}',group=group,payload=payload(facts,{'answer':q(instruction,options)}),
                expected={'answer':label},repetitions=3,factors=dict(item=str(ident),mode=mode,**factors)))
    templates=[('the switch is on','the lamp is lit'),('the badge is valid','the door is unlocked'),
        ('the box is heavy','the shelf is reinforced'),('the sensor is active','the indicator is green'),
        ('the parcel is fragile','the parcel is padded'),('the ticket is premium','the seat is reserved'),
        ('the plant is flowering','the plant is watered'),('the file is approved','the file is signed')]
    for t,(ptext,qtext) in enumerate(templates):
        names={'p':ptext,'q':qtext}
        for j,(observed,value,target) in enumerate(product(['p','q'],[False,True],['p','q'])):
            vals={dict(p=p,q=q)[target] for p,q in product([False,True],repeat=2)
                  if (not p or q) and dict(p=p,q=q)[observed]==value}
            label='yes' if vals=={True} else 'no' if vals=={False} else 'cannot_be_determined'
            fact=names[observed] if value else names[observed].replace(' is ',' is not ')
            facts=f'The only rule given is: if {ptext}, then {qtext}. Fact: {fact}. No converse rule is stated.'
            text=f'Based on these facts, is this statement true: "{names[target]}"? Select yes if it must be true, no if it must be false, and cannot_be_determined if either truth value remains possible.'
            add('conditional_truth',f'{t}-{j}',facts,text,YN,label,template=t,observed=observed,value=value,target=target)
    strings=['raven','river','mirror','rarer','raspberry','refrigerator','rrarr','abrrrba','RrArR','r_r_r_r','rrrrrrr','ababa']
    for i,word in enumerate(strings):
        for spaced in [False,True]:
            shown=' '.join(word) if spaced else word
            add('exact_count',f'{i}-{spaced}',f'Text: {shown}',
                'How many occurrences of the letter r are in the text, ignoring letter case? Spaces and underscores do not count as letters.',
                {str(n):str(n) for n in range(9)},str(word.lower().count('r')),word=word,spaced=spaced)
    for i,(boxes,each,given,received) in enumerate([(3,8,5,2),(7,6,9,4),(12,9,17,6),(23,14,61,19),(41,17,83,26),(125,24,317,58)]):
        label=boxes*each-given+received
        for noise in [False,True]:
            facts=f'A store has {boxes} boxes with {each} pencils in each box. It sells {given} pencils and receives {received} loose pencils.'
            if noise: facts+=' Separately, the store has 13 empty shelves and 7 chairs; no pencils are on those shelves or chairs.'
            opts={str(n):str(n) for n in [label,boxes+each-given+received,boxes*each+given+received,boxes*each-given-received]}
            add('multistep_math',f'{i}-{noise}',facts,'How many pencils does the store now have?',opts,str(label),noise=noise,template=i)
    rooms=['kitchen','hall','garden','office']
    for count in [4,12,32]:
        for sample in range(2):
            location=rooms[sample];facts=[f'The key starts in the {location}.']
            for step in range(count):
                dest=rooms[(step+sample+1)%4]
                if step%3!=0:
                    facts.append(f'Event {step+1}: Ada moves the key from the {location} to the {dest}.');location=dest
                else: facts.append(f'Event {step+1}: Ben visits the {dest} without moving the key.')
            add('long_tracking',f'{count}-{sample}',' '.join(facts),'Where is the key after the final event?',{x:x for x in rooms},location,events=count)
    assert len({c['id'] for c in out})==len(out)
    return out
if __name__=='__main__': run(cases,'reasoning-followup',20260919,HYPOTHESES)
