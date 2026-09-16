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

if __name__=='__main__':unittest.main()
