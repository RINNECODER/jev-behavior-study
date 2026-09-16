"""Predeclared controlled Jev study; no retries, no cross-request context."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent
MODEL = 'jev-1.13.0'
BASE = 'I need to wash my car. The car wash is a 5-minute walk from my home.'
DIRECT = 'Should I walk or drive there?'
FEASIBLE = 'Which option accomplishes my goal of getting my car washed at the car wash?'
YN = {'yes': 'Yes', 'no': 'No', 'cannot_be_determined': 'Cannot be determined'}
A = 'Does my car need to be physically present at the car wash to be washed there?'
B = 'If I walk to the car wash and leave my car at home, will that accomplish my goal of getting my car washed there?'


def q(text, criteria):
    return {'type': 'choice', 'instructions': text, 'criteria': criteria}


def payload(state, questions):
    return {'model': MODEL, 'state': state, 'questions': questions}


def cases():
    out = []
    def add(id, group, p, expected, reps, **factors):
        out.append(dict(id=id, group=group, payload=p, expected=expected, repetitions=reps, factors=factors))
    # Full 2x2x2x2 factorial. Each main effect is averaged over the other factors.
    for place in ['inline', 'state']:
        for wording, text in [('direct', DIRECT), ('goal', FEASIBLE)]:
            for unknown in [False, True]:
                for reverse in [False, True]:
                    opts = {'walk': 'Walk', 'drive': 'Drive'}
                    if unknown: opts['cannot_be_determined'] = 'Cannot be determined'
                    if reverse: opts = dict(reversed(list(opts.items())))
                    p = payload(BASE if place == 'state' else '', {'answer': q(text if place == 'state' else BASE+' '+text, opts)})
                    add(f'factor-{place}-{wording}-{int(unknown)}-{int(reverse)}', 'factorial', p, {'answer':'drive'}, 25,
                        placement=place, wording=wording, unknown=unknown, reverse=reverse)
    # Questions alone/together and whether a direct answer changes in the same batch.
    state = 'I want to have my car washed at a car wash located a 5-minute walk from my home.'
    defs = {'A':q(A,YN), 'B':q(B,YN), 'transport':q(DIRECT,{'walk':'Walk','drive':'Drive'})}
    expected = {'A':'yes','B':'no','transport':'drive'}
    for names in [('A',),('B',),('A','B'),('transport',),('A','B','transport')]:
        add('batch-'+'-'.join(names),'batching',payload(state,{k:defs[k] for k in names}),{k:expected[k] for k in names},25,names=list(names))
    # Matched question-ID control; instruction text identical.
    for name in ['answer','transport']:
        add('key-'+name,'question_key',payload(BASE,{name:q(DIRECT,{'walk':'Walk','drive':'Drive'})}),{name:'drive'},25,key=name)
    # Meaning-preserving option descriptions and letter-case counting controls.
    add('options-described','options',payload(BASE,{'answer':q(DIRECT,{'walk':'Travel there on foot, leaving my car at home.','drive':'Travel there in my car, bringing it with me.'})}),{'answer':'drive'},25)
    add('rule-feasibility','options',payload(BASE,{'answer':q('Choose the option that satisfies the goal and its necessary conditions. Consider convenience only among options that can accomplish the goal. '+DIRECT,{'walk':'Walk','drive':'Drive'})}),{'answer':'drive'},25)
    # Balanced synthetic scenarios, labeled in advance. They test counterexamples,
    # not the frequency of these situations in the real world.
    scenarios = [
      ('wash','I need my car washed at the car wash. My car is at home. The car wash is a five-minute walk away.','drive'),
      ('tires','I need the tires on my car replaced at the tire shop. My car is at home. The shop is a five-minute walk away.','drive'),
      ('inspection','My car must undergo its annual vehicle inspection at the inspection center. My car is at home. The center is a five-minute walk away.','drive'),
      ('oil','I have booked an oil change for my car at the garage. My car is at home. The garage is a five-minute walk away.','drive'),
      ('weigh','I need my car weighed on the vehicle scale at the weigh station. My car is at home. The station is a five-minute walk away.','drive'),
      ('trade','The dealer has asked to physically inspect my car for a trade-in valuation. My car is at home. The dealer is a five-minute walk away.','drive'),
      ('pickup','My car is already at the car wash, and I need to collect it. I have no other vehicle available. The car wash is a five-minute walk away.','walk'),
      ('job','I am going to a job interview at the car wash. I have no car available. The car wash is a five-minute walk away.','walk'),
      ('receipt','I only need to collect a paper receipt from the car wash. My car is not needed, and the pedestrian route is open while the road is closed to vehicles. It is a five-minute walk away.','walk'),
      ('supplies','I need to buy a sponge from the car wash shop. My car has a dead battery and cannot be driven. The shop is a five-minute walk away.','walk'),
      ('refund','I need to discuss a refund in person at the car wash. No car inspection is required. I have no vehicle available. It is a five-minute walk away.','walk'),
      ('mobile','A mobile service is washing my car at home. I only need to take a signed form to its office. My car must stay at home for the service. The office is a five-minute walk away.','walk'),
    ]
    def scenario_payload(state, mode):
        if mode == 'direct':
            return payload(state,{'answer':q(DIRECT,{'walk':'Walk','drive':'Drive'})})
        if mode == 'goal':
            return payload(state,{'answer':q('Which travel option is feasible and accomplishes the stated goal under the supplied constraints?',{'walk':'Walk','drive':'Drive'})})
        return payload(state,{'bring':q('Must I bring my car from home to the destination to accomplish the stated goal?',YN),
                              'walk':q('Would walking to the destination without bringing a car from home accomplish the stated goal under the supplied constraints?',YN)})
    for name,state,label in scenarios:
        for mode in ['direct','goal','checks']:
            exp = {'answer':label} if mode != 'checks' else {'bring':'yes' if label=='drive' else 'no','walk':'no' if label=='drive' else 'yes'}
            add(f'transfer-{name}-{mode}','transfer',scenario_payload(state,mode),exp,10,scenario=name,mode=mode,label=label)
    # Length/position tests on the same car-wash facts; fillers are data, not instructions.
    filler_sentences = {
      'neutral': 'The neighborhood archive lists brick buildings, painted fences, garden beds, library shelves, weather records, meeting rooms, and ordinary maintenance dates.',
      'walking': 'A separate resident walks to the nearby bakery for bread, enjoys the short pedestrian route, and finds walking convenient for that unrelated errand.',
    }
    for words in [0,256,1024,4096,8192]:
        for filler in (['neutral'] if words==0 else ['neutral','walking']):
            for position in (['start'] if words==0 else ['start','middle','end']):
                text = (' '.join([filler_sentences[filler]]*(words//len(filler_sentences[filler].split())+1))).split()[:words]
                cut = {'start':0,'middle':len(text)//2,'end':len(text)}[position]
                state = ' '.join(text[:cut])+ '\nCURRENT TASK: '+BASE+'\n'+' '.join(text[cut:])
                for mode in ['direct','checks']:
                    exp = {'answer':'drive'} if mode=='direct' else {'bring':'yes','walk':'no'}
                    add(f'length-{words}-{filler}-{position}-{mode}','length',scenario_payload(state,mode),exp,8,
                        filler_words=words,filler=filler,position=position,mode=mode,state_words=len(state.split()))
    # Balanced counterexamples under scaled text: checks must not just answer yes/no by habit.
    for name,state,label in [scenarios[i] for i in [0,2,6,9]]:
        for words in [512,4096]:
            filler = (' '.join([filler_sentences['neutral']]*400)).split()[:words]
            for position in ['start','end']:
                longstate = state+'\n'+' '.join(filler) if position=='start' else ' '.join(filler)+'\n'+state
                for mode in ['direct','checks']:
                    exp = {'answer':label} if mode=='direct' else {'bring':'yes' if label=='drive' else 'no','walk':'no' if label=='drive' else 'yes'}
                    add(f'longtransfer-{name}-{words}-{position}-{mode}','long_transfer',scenario_payload(longstate,mode),exp,5,
                        scenario=name,label=label,filler_words=words,position=position,mode=mode)
    # Diverse exact counting, computed labels, no expected answer in the input.
    strings = ['straberry','strawberry','strawberries','raspberry','blueberry','cherry','banana','river','error','rrr','r','rrrrrr','abracadabra','qrzrpr','rrabr','RrR']
    for word in strings:
        for form in ['plain','spaced','algorithm']:
            rendered = ' '.join(word) if form=='spaced' else word
            instruction = 'How many occurrences of the letter r, ignoring case, are in the supplied text?'
            if form=='algorithm': instruction += ' Examine each character separately and count every r or R exactly once.'
            add(f'count-{word}-{form}','counting',payload(rendered,{'answer':q(instruction,{str(i):str(i) for i in range(11)})}),{'answer':str(word.lower().count('r'))},10,
                word=word,form=form,expected_count=word.lower().count('r'))
    assert len({c['id'] for c in out}) == len(out)
    return out


def run(suite_factory=cases, run_name='behavior-study', seed=20260916):
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    suite=suite_factory()
    counts=Counter()
    for c in suite: counts[c['group']]+=c['repetitions']
    print('Requests by group:',dict(counts),'Total:',sum(counts.values()),flush=True)
    if args.plan_only: return
    for line in ((ROOT/'.env').read_text().splitlines() if (ROOT/'.env').exists() else []):
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('\"\''))
    key=os.environ['TYPESAFE_API_KEY']
    out=ROOT/'results'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+run_name)
    out.mkdir()
    manifest={'model':MODEL,'seed':seed,'workers':args.workers,'cases':suite,
              'method':'Predeclared labels and cases; shuffled interleaved requests; fresh opener; no retries; no response reuse. Repetitions measure conditional stability, not independent task coverage.',
              'hypotheses':['Context placement changes direct-choice accuracy.','Goal-focused instructions improve choice.','Option order, uncertainty option or descriptions affect answers.','Batching alone does not fix a direct choice.','Prerequisite checking transfers to balanced new cases.','Length, irrelevant walking cues and fact position affect performance.','Explicit counting or spaced text improves exact letter counting.']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    schedule=[(c,r) for c in suite for r in range(c['repetitions'])]
    random.Random(manifest['seed']).shuffle(schedule)
    (out/'schedule.json').write_text(json.dumps([[c['id'],r] for c,r in schedule]))
    print('Saving:',out,flush=True)
    def trial(job):
        index,(case,rep)=job
        body=json.dumps(case['payload']).encode()
        row={'trial':index,'case_id':case['id'],'repetition':rep,'group':case['group'],
             'payload_sha256':hashlib.sha256(body).hexdigest(),'started_at':datetime.now(timezone.utc).isoformat()}
        req=urllib.request.Request('https://api.typesafe.ai/v1/systemone',data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Cache-Control':'no-cache'})
        start=time.perf_counter()
        try:
            with urllib.request.build_opener().open(req,timeout=90) as response:
                raw=response.read().decode(); row.update(http_status=response.status,raw_response=raw)
            parsed=json.loads(raw); row['response']=parsed
            checks={}
            for k,label in case['expected'].items():
                a=parsed.get('answers',{}).get(k,{})
                valid=a.get('type')=='choice' and a.get('choice') in case['payload']['questions'][k]['criteria']
                checks[k]={'selected':a.get('choice'),'expected':label,'valid':valid,'correct':valid and a.get('choice')==label}
            row['checks']=checks
            row['all_correct']=all(v['correct'] for v in checks.values())
        except urllib.error.HTTPError as e:
            row.update(http_status=e.code,error=e.read().decode(errors='replace').replace(key,'[REDACTED]'))
        except Exception as e:
            row['error']=str(e).replace(key,'[REDACTED]')
        row['latency_ms']=round((time.perf_counter()-start)*1000,2)
        return row
    completed=[]
    # Bounded submission prevents runaway requests after auth or repeated failures.
    with (out/'results.jsonl').open('w') as f, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for offset in range(0,len(schedule),40):
            batch=list(pool.map(trial,enumerate(schedule[offset:offset+40],start=offset+1)))
            for row in batch:
                completed.append(row); f.write(json.dumps(row)+'\n'); f.flush()
            print(f'{len(completed)}/{len(schedule)} requests; errors={sum("error" in r for r in completed)}',flush=True)
            if any(r.get('http_status') in [401,403] for r in batch) or sum('error' in r for r in batch)>=10:
                print('Stopped: authentication failure or >=10 errors in one block.',flush=True); break
    (out/'completion.json').write_text(json.dumps({'planned':len(schedule),'completed':len(completed),'errors':sum('error' in r for r in completed)},indent=2))
    print('Finished:',out,flush=True)


if __name__=='__main__': run()
