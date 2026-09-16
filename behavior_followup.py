"""Exploratory follow-up specified after the first study; held-out scenario checks."""
from behavior_study import BASE, DIRECT, FEASIBLE, YN, cases, payload, q, run


def followup_cases():
    out=[]
    def add(id,group,p,expected,reps,**factors):
        out.append(dict(id=id,group=group,payload=p,expected=expected,repetitions=reps,factors=factors))
    old=[c for c in cases() if c['group']=='transfer' and c['factors']['mode']=='direct']
    scenarios=[(c['factors']['scenario'],c['payload']['state'],c['factors']['label'],'reused') for c in old]
    scenarios += [
      ('brakes','My car is at home. A mechanic needs to replace its brake pads at the workshop, a five-minute walk away. The car is safe and legal to drive there.','drive','new'),
      ('alignment','My car is at home. I have booked a wheel alignment for it at a service center a five-minute walk away. It is safe and legal to drive there.','drive','new'),
      ('windscreen','My car is at home. A glass specialist must replace its windshield at their workshop, a five-minute walk away. It is safe and legal to drive there.','drive','new'),
      ('paint','My car is at home. A body shop a five-minute walk away needs it on site for a paint repair. It is safe and legal to drive there.','drive','new'),
      ('keys','I am collecting spare keys from a locksmith a five-minute walk away. My car is already parked at the locksmith and I have no other vehicle.','walk','new'),
      ('interview','I am attending a job interview at a tire shop a five-minute walk away. I have no car available.','walk','new'),
      ('manual','I am collecting a printed manual from a dealership a five-minute walk away. No car inspection is needed, and the road is closed to cars but the footpath is open.','walk','new'),
      ('office','I am going to the garage office a five-minute walk away to hand over a signed form. My car is undergoing repairs there and I have no other vehicle.','walk','new'),
    ]
    for name,state,label,cohort in scenarios:
        for reverse in [False,True]:
            opts={'walk':'Travel there on foot, leaving any car at home where it is.','drive':'Travel there in my car, bringing it with me.'}
            if reverse:opts=dict(reversed(list(opts.items())))
            add(f'described-{name}-{int(reverse)}','described_transfer',payload(state,{'answer':q(DIRECT,opts)}),{'answer':label},10,
                scenario=name,label=label,cohort=cohort,reverse=reverse)
    for distance,text in [('absent',''),('walk5','The car wash is a 5-minute walk from my home.'),('drive5','The car wash is a 5-minute drive from my home.'),('meters100','The car wash is 100 meters from my home.'),('km50','The car wash is 50 kilometers from my home.')]:
        add('distance-'+distance,'distance',payload('I need to wash my car. '+text,{'answer':q(DIRECT,{'walk':'Walk','drive':'Drive'})}),{'answer':'drive'},20,distance=distance)
    for placement in ['inline','state']:
        for wording,text in [('direct',DIRECT),('goal',FEASIBLE)]:
            add(f'replicate-{placement}-{wording}','replication',payload(BASE if placement=='state' else '',{'answer':q(text if placement=='state' else BASE+' '+text,{'walk':'Walk','drive':'Drive'})}),{'answer':'drive'},25,placement=placement,wording=wording)
    for word in ['straberry','strawberry']:
        for placement in ['inline','state']:
            for wording in ['original','explicit']:
                if wording=='original':instruction=f"How many R's are in {word if placement=='inline' else 'the supplied text'}? Answer only with the number."
                else:instruction=f"How many occurrences of the letter r, ignoring case, are in {word if placement=='inline' else 'the supplied text'}?"
                add(f'countfollow-{word}-{placement}-{wording}','count_followup',payload(word if placement=='state' else '',{'answer':q(instruction,{str(i):str(i) for i in range(11)})}),{'answer':'3'},15,word=word,placement=placement,wording=wording)
    for name,extra in [('none',''),('facts',' The car must be physically present at the car wash to be washed there. Walking there while leaving the car at home will not accomplish this goal.'),('previous_answers',' Previously checked prerequisites: the car must be physically present: yes; walking there and leaving the car at home accomplishes the goal: no.')]:
        add('evidence-'+name,'evidence',payload(BASE+extra,{'answer':q(DIRECT,{'walk':'Walk','drive':'Drive'})}),{'answer':'drive'},20,evidence=name)
    return out


if __name__=='__main__':run(followup_cases,'behavior-followup',20260917)
