"""Original controlled reasoning tasks, inspired by bAbI/GSM-Symbolic/retrieval tests.
Ground truth is determined before requests; no model-based grading.
"""
from itertools import product
from behavior_study import payload, q, run, YN

HYPOTHESES = [
 'Meaning-preserving option reversal preserves accuracy.',
 'Explicit evidence-only instructions improve logical entailment.',
 'Irrelevant numerical details preserve arithmetic answers.',
 'Retrieval accuracy varies with record count and target position.',
 'Simple prerequisites transfer beyond travel decisions.',
]

def cases():
    out = []
    def add(family, ident, facts, question, options, label, **factors):
        for mode in ['plain', 'reversed', 'explicit']:
            opts = dict(reversed(list(options.items()))) if mode == 'reversed' else options
            text = question
            if mode == 'explicit':
                text = ('Use only the supplied facts and rules. Do not assume unstated facts. '
                        'Check the exact requested condition before selecting an answer. ' + text)
            out.append(dict(id=f'{family}-{ident}-{mode}', group=family,
                payload=payload(facts, {'answer':q(text, opts)}), expected={'answer':label},
                repetitions=3, factors=dict(item=str(ident), mode=mode, **factors)))
    # Exhaustively enumerate two-proposition worlds satisfying a material implication.
    for i, (observed, value, target) in enumerate(product(['p','q'], [False,True], ['p','q'])):
        worlds = [dict(p=p,q=q) for p,q in product([False,True], repeat=2) if (not p or q)]
        possible = {w[target] for w in worlds if w[observed] == value}
        label = 'yes' if possible == {True} else 'no' if possible == {False} else 'cannot_be_determined'
        names = {'p':'the switch is on','q':'the lamp is lit'}
        fact = names[observed] if value else names[observed].replace(' is ', ' is not ')
        add('conditional',i,'For this device, if the switch is on, then the lamp is lit. '+fact+'.',
            'Does it follow that '+names[target]+'?',YN,label, observed=observed,value=value,target=target)
    for i, (lit, negated) in enumerate(product([False,True], repeat=2)):
        add('negation',i,'The lamp is '+('lit.' if lit else 'not lit.'),
            'Is the statement "The lamp is '+('not lit' if negated else 'lit')+'" true?',YN,
            'yes' if lit != negated else 'no')
    # All possible memberships for a named individual: no existential assumptions.
    quant = [
      ('All daxes are blue. Neri is a dax.','Is Neri blue?','yes'),
      ('No daxes are blue. Neri is a dax.','Is Neri blue?','no'),
      ('Some daxes are blue. Neri is a dax.','Is Neri blue?','cannot_be_determined'),
      ('All daxes are blue. Neri is blue.','Is Neri a dax?','cannot_be_determined'),
      ('All daxes are blue. Neri is not blue.','Is Neri a dax?','no'),
      ('Some daxes are blue.','Does at least one blue dax exist?','yes'),
      ('No daxes are blue.','Does at least one blue dax exist?','no'),
      ('All daxes are blue.','Does at least one dax exist?','cannot_be_determined')]
    for i,(f,t,l) in enumerate(quant): add('quantifiers',i,f+' Use classical logic; a category may be empty.',t,YN,l)
    for i,(a,b,c) in enumerate([(8,3,2),(17,6,4),(24,9,7),(51,18,11),(103,27,16),(200,65,32)]):
        result=a-b+c
        opts={str(n):str(n) for n in [result,a+b+c,a-b-c,a]}
        for noise in [False,True]:
            facts=f'Mina starts with {a} apples, gives away {b}, then receives {c} more.'
            if noise: facts+=' Of the apples now in her possession, 5 have spots; she keeps all of them.'
            add('arithmetic',f'{i}-{noise}',facts,'How many apples does Mina now have?',opts,str(result),noise=noise,template=i)
    for i,(a,b) in enumerate([('9.11','9.9'),('0.7','0.65'),('12.01','12.1'),('3.14','3.09'),('0.09','0.1'),('10.0','10.00')]):
        from decimal import Decimal
        label='first' if Decimal(a)>Decimal(b) else 'second' if Decimal(b)>Decimal(a) else 'equal'
        add('decimal',i,f'The first number is {a}. The second number is {b}.','Which number is larger?',
            {'first':'The first','second':'The second','equal':'They are equal'},label)
    rooms=['kitchen','hall','garden','office']
    for i in range(8):
        start,finish=rooms[i%4],rooms[(i+1)%4]
        f=f'Ada carries a key into the {start}. Ada leaves the key there. Ada goes to the {finish}.'
        target=start
        if i>=4:
            f+=f' Ben picks up the key in the {start} and carries it into the {finish}.'
            target=finish
        add('object_tracking',i,f,'Where is the key now?',{x:x for x in rooms},target)
    for i in range(6):
        names=['Ada','Ben','Cora','Davi']
        names=names[i%4:]+names[:i%4]
        facts=' '.join(f'{names[j]} arrived before {names[j+1]}.' for j in range(3))
        latest=i%2==0
        add('ordering',i,facts,'Who arrived '+('last?' if latest else 'first?'),
            {x:x for x in ['Ada','Ben','Cora','Davi']},names[-1] if latest else names[0])
    # Explicit rules isolate satisfying a goal, without external-world ambiguity.
    for i,(thing,service) in enumerate([('coat','repair'),('watch','battery replacement'),('bicycle','tire repair'),('document','in-person stamping')]):
        for present in [False,True]:
            facts=(f'I need {service} for my {thing} at a shop. The shop requires the {thing} physically present. '
                   f'The {thing} is '+('already at the shop.' if present else 'at my home.'))
            add('prerequisite',f'{i}-{present}',facts,f'Must I bring the {thing} from home to the shop to accomplish this?',YN,
                'no' if present else 'yes',present=present)
    for i,(fact,question,label) in enumerate([
        ('A sealed box contains a ball. Its color is not specified.','Is the ball red?','cannot_be_determined'),
        ('The meeting is on Tuesday. Its time is not specified.','Does the meeting start at 9 AM?','cannot_be_determined'),
        ('In this fictional world, every bird is flightless. Zed is a bird.','Can Zed fly?','no'),
        ('In this fictional world, all ice is hot. This cube is ice.','Is this cube hot?','yes'),
        ('The receipt says the total is 12 dollars.','Is the total 12 dollars?','yes'),
        ('The receipt says the total is 12 dollars.','Is the total 15 dollars?','no')]):
        add('evidence',i,fact,question,YN,label)
    for count in [16,128,512]:
        for position in ['start','middle','end']:
            for sample in range(3):
                records=[f'Record R{n:04d} has code C{(n*37+sample*11)%997:03d}.' for n in range(count)]
                index={'start':0,'middle':count//2,'end':count-1}[position]
                answer=f'C{(index*37+sample*11)%997:03d}'
                opts={f'C{(index*37+sample*11+d)%997:03d}':f'C{(index*37+sample*11+d)%997:03d}' for d in [0,17,39,61]}
                # Rotate the correct option's position independently of the record location.
                items=list(opts.items()); shift=sample%4; opts=dict(items[shift:]+items[:shift])
                add('retrieval',f'{count}-{position}-{sample}','\n'.join(records),f'What is the code for record R{index:04d}?',opts,answer,
                    records=count,position=position,sample=sample)
    assert len({c['id'] for c in out})==len(out)
    for c in out: assert c['expected']['answer'] in c['payload']['questions']['answer']['criteria']
    return out

if __name__=='__main__': run(cases,'everyday-study',20260918,HYPOTHESES)
