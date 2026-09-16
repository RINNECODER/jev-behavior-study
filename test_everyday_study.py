"""Offline checks for labels, paired controls and ground-truth construction."""
import unittest
from collections import defaultdict
from itertools import product
from everyday_study import cases

class SuiteTests(unittest.TestCase):
    def test_design(self):
        suite=cases()
        self.assertEqual(len(suite),279)
        self.assertEqual(sum(c['repetitions'] for c in suite),837)
        grouped=defaultdict(list)
        for c in suite: grouped[c['group'],c['factors']['item']].append(c)
        self.assertEqual(len(grouped),93)
        for variants in grouped.values():
            plain,reverse,explicit=variants
            self.assertEqual(plain['expected'],reverse['expected'])
            self.assertEqual(plain['expected'],explicit['expected'])
            self.assertEqual(plain['payload']['state'],explicit['payload']['state'])
            a=plain['payload']['questions']['answer']['criteria']
            b=reverse['payload']['questions']['answer']['criteria']
            self.assertEqual(list(a),list(reversed(b)))
    def test_conditional_labels(self):
        for c in cases():
            if c['group']!='conditional': continue
            f=c['factors']
            worlds=[dict(p=p,q=q) for p,q in product([False,True],repeat=2) if not (p and not q)]
            values={w[f['target']] for w in worlds if w[f['observed']]==f['value']}
            label={frozenset([True]):'yes',frozenset([False]):'no',frozenset([True,False]):'cannot_be_determined'}[frozenset(values)]
            self.assertEqual(c['expected']['answer'],label)
    def test_retrieval_labels(self):
        import re
        for c in cases():
            if c['group']!='retrieval': continue
            records=dict(re.findall(r'Record (R\d+) has code (C\d+)\.',c['payload']['state']))
            target=re.search(r'record (R\d+)',c['payload']['questions']['answer']['instructions'])[1]
            self.assertEqual(len(records),c['factors']['records'])
            self.assertEqual(records[target],c['expected']['answer'])
    def test_arithmetic_labels(self):
        import re
        for c in cases():
            if c['group']!='arithmetic': continue
            a,b,d=map(int,re.findall(r'\d+',c['payload']['state'])[:3])
            self.assertEqual(int(c['expected']['answer']),a-b+d)
            self.assertGreaterEqual(a-b+d,5)


class FollowupTests(unittest.TestCase):
    def test_ground_truth_from_prompts(self):
        import re
        from reasoning_followup import cases as followup
        suite=followup()
        self.assertEqual(len(suite),318)
        self.assertEqual(sum(c['repetitions'] for c in suite),954)
        for c in suite:
            text=c['payload']['state']; label=c['expected']['answer']
            if c['group']=='multistep_math':
                boxes,each,sold,received=map(int,re.findall(r'\d+',text)[:4])
                self.assertEqual(int(label),boxes*each-sold+received)
            elif c['group']=='exact_count':
                shown=text.removeprefix('Text: ')
                self.assertEqual(int(label),sum(ch in 'rR' for ch in shown))
            elif c['group']=='long_tracking':
                location=re.search(r'starts in the (\w+)',text)[1]
                for source,dest in re.findall(r'moves the key from the (\w+) to the (\w+)',text):
                    self.assertEqual(source,location)
                    location=dest
                self.assertEqual(label,location)
            elif c['group']=='conditional_truth':
                f=c['factors']
                known=f['observed']==f['target']
                if known: expected='yes' if f['value'] else 'no'
                elif f['observed']=='p' and f['value']: expected='yes'
                elif f['observed']=='q' and not f['value']: expected='no'
                else: expected='cannot_be_determined'
                self.assertEqual(label,expected)
                self.assertIn('if either truth value remains possible',c['payload']['questions']['answer']['instructions'])

if __name__=='__main__': unittest.main()
