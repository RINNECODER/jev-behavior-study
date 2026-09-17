import json
import unittest
from unittest.mock import patch
from ..engine import Snake,ACTIONS,VECTORS
from .policy import VARIANTS,payload,relative_geometry,decide

class PolicyTests(unittest.TestCase):
    def test_no_quality_functions_and_all_actions_present(self):
        g=Snake();g.body=[(0,0),(0,1),(0,2)];g.heading=0;g.food=(4,5)
        for name in ['safe','legal','baseline','distance','reachable']:
            setattr(g,name,lambda *a: (_ for _ in ()).throw(AssertionError('Quality function used')))
        for v in VARIANTS:
            p,m=payload(g,v,[],list(ACTIONS))
            self.assertEqual(set(m.values()),set(ACTIONS));self.assertEqual(len(p['questions']['move']['criteria']),3)
            text=json.dumps(p)
            for forbidden in ['verified_routes','candidate_facts','safe_next_move','total_moves_to_food','optimal_actions','oracle']:
                self.assertNotIn(forbidden,text)
    def test_relative_geometry_invertible_for_all_headings(self):
        g=Snake()
        for heading in range(4):
            g.heading=heading;r=relative_geometry(g);fx,fy=VECTORS[heading];rx,ry=VECTORS[(heading+1)%4];hx,hy=g.body[0]
            for original,relative in zip(g.body+[g.food],r['snake_head_to_tail']+[r['food']]):
                x,y=relative;self.assertEqual(original,(hx+x*rx+y*fx,hy+x*ry+y*fy))
                self.assertLessEqual(r['board_bounds_inclusive']['min_x'],x);self.assertLessEqual(x,r['board_bounds_inclusive']['max_x'])
    def test_review_uses_only_own_proposal_and_executes_revision(self):
        def response(a):return {'valid':True,'response':{'answers':{'move':{'choice':a}}}}
        with patch('snake_demo.unassisted.policy.call',side_effect=[response('left'),response('right')]) as caller:
            r=decide(Snake(),'review',[],list(ACTIONS))
            self.assertEqual(r['first_action'],'left');self.assertEqual(r['action'],'right')
            self.assertEqual(caller.call_args_list[1].args[0]['state']['your_previous_proposal'],'left')
    def test_failed_review_does_not_silently_fallback(self):
        first={'valid':True,'response':{'answers':{'move':{'choice':'left'}}}}
        with patch('snake_demo.unassisted.policy.call',side_effect=[first,{'valid':False,'error':'HTTPError'}]):
            r=decide(Snake(),'review',[],list(ACTIONS));self.assertIsNone(r['action']);self.assertEqual(len(r['calls']),2)

if __name__=='__main__':unittest.main()
