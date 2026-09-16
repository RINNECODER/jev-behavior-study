import json
import re
import unittest
from collections import Counter,defaultdict
from limits_study import cases,scenarios

class LimitsTests(unittest.TestCase):
    def test_balanced_decisions(self):
        self.assertEqual(Counter(s['label'] for s in scenarios()),{'bring':24,'go_without':24})
        cs=[c for c in cases() if c['group']=='decision']
        self.assertEqual(len(cs),288)
        self.assertTrue(all(c['repetitions']==3 for c in cs))
    def test_permutations_and_math(self):
        groups=defaultdict(list)
        for c in cases():
            if c['group']!='permutation':continue
            groups[c['factors']['template']].append(c)
            a,b,d,e=map(int,re.findall(r'\d+',c['payload']['state']))
            opts=c['payload']['questions']['answer']['criteria']
            self.assertEqual(int(opts[c['expected']['answer']]),a*b-d+e)
            self.assertEqual(len(set(opts.values())),4)
            self.assertTrue(all(int(v)>=0 for v in opts.values()))
        for cs in groups.values():
            self.assertEqual(len(cs),24)
            self.assertEqual(len({tuple(c['factors']['order']) for c in cs}),24)
            self.assertEqual(Counter(c['factors']['correct_position'] for c in cs),{1:6,2:6,3:6,4:6})
    def test_logic_by_possible_worlds(self):
        # A true suffix (or no true nodes) enumerates every world for a one-way chain.
        for c in cases():
            if c['group']!='logic_depth':continue
            text=c['payload']['state'];d=c['factors']['depth']
            match=re.search(r'Object Z is (not )?in category K(\d+)\.$',text)
            neg=bool(match[1]);known=int(match[2]);target=int(re.search(r'category K(\d+)',c['payload']['questions']['answer']['instructions'])[1])
            possible={target>=start for start in range(d+2) if (known>=start)!=neg}
            expected='yes' if possible=={True} else 'no' if possible=={False} else 'cannot_be_determined'
            self.assertEqual(c['expected']['answer'],expected)
    def test_tracking_and_records(self):
        for c in cases():
            text=c['payload']['state'];question=c['payload']['questions']['answer']['instructions']
            if c['group']=='multi_tracking':
                loc=dict(re.findall(r'Item (I\d+) starts in the (\w+)',text))
                for item,source,dest in re.findall(r'moves item (I\d+) from the (\w+) to the (\w+)',text):
                    self.assertEqual(loc[item],source);loc[item]=dest
                target=re.search(r'item (I\d+)',question)[1]
                self.assertEqual(c['expected']['answer'],loc[target])
            elif c['group']=='competing_records':
                records=[(int(v),color) for v,color in re.findall(r'Asset TARGET, version (\d+), color (\w+)',text)]
                self.assertEqual(c['expected']['answer'],max(records)[1])

class PipelineTests(unittest.TestCase):
    def test_actual_answer_is_forwarded_without_correction(self):
        import tempfile
        from pathlib import Path
        from limits_study import pipeline_cases
        suite=cases()
        rows=[]
        for c in suite:
            if c['group']!='decision' or c['factors']['mode']!='check':continue
            for rep in range(3):
                rows.append(dict(trial=len(rows)+1,case_id=c['id'],repetition=rep,
                    response={'answers':{'answer':{'choice':'cannot_be_determined'}}},all_correct=False))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/'manifest.json').write_text(json.dumps({'cases':suite}))
            (path/'results.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
            derived=pipeline_cases(path)
        self.assertEqual(len(derived),288)
        self.assertEqual(len({c['factors']['source_trial'] for c in derived}),288)
        for c in derived:
            self.assertIn('selected answer was: cannot_be_determined.',c['payload']['state'])
            self.assertFalse(c['factors']['check_correct'])
            self.assertEqual(set(c['payload']),{'model','state','questions'})

class StressTests(unittest.TestCase):
    def test_independent_oracles(self):
        from stress_followup import cases as stress
        suite=stress()
        self.assertEqual(sum(c['repetitions'] for c in suite),126)
        for c in suite:
            state=c['payload']['state']; question=c['payload']['questions']['answer']['instructions']
            if c['group']=='scrambled_logic':
                edges=re.findall(r'If Z has (T\d+), then Z has (T\d+)',state)
                negative='Fact: Z does not have' in state
                fact=re.search(r'Fact: Z (?:has|does not have) (T\d+)',state)[1]
                target=re.search(r'have (T\d+)',question)[1]
                if negative:edges=[(b,a) for a,b in edges]
                known={fact}
                while True:
                    more=known|{b for a,b in edges if a in known}
                    if more==known:break
                    known=more
                expected=('no' if negative else 'yes') if target in known else 'cannot_be_determined'
                self.assertEqual(expected,c['expected']['answer'])
            elif c['group']=='carry_tracking':
                actor={};obj={};held={}
                for person,room,item in re.findall(r'Person (P\d+) is in the (\w+) holding item (I\d+)',state):
                    actor[person]=room;obj[item]=room;held[person]=item
                pattern=r'(P\d+) (?:goes to the (\w+)(?: and picks up (I\d+))?|puts down (I\d+) there)\.'
                for person,room,pick,drop in re.findall(pattern,state):
                    if room:
                        actor[person]=room
                        if held.get(person):obj[held[person]]=room
                    if pick:
                        self.assertEqual(obj[pick],actor[person]);held[person]=pick
                    if drop:
                        self.assertEqual(held[person],drop);held[person]=None
                target=re.search(r'item (I\d+)',question)[1]
                self.assertEqual(obj[target],c['expected']['answer'])
            else:
                records=[(int(v),color) for v,color in re.findall(r'Asset TARGET, version (\d+), color (\w+)',state)]
                self.assertEqual(max(records)[1],c['expected']['answer'])

if __name__=='__main__':unittest.main()
