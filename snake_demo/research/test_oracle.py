import random
import unittest
from ..engine import Snake,ACTIONS
from .oracle import assess,shortest,bfs_reference,restore

class OracleTests(unittest.TestCase):
    def test_against_independent_bfs(self):
        for seed in range(20):
            g=Snake(seed=seed);g.size=5;g.body=[(2,2),(2,3),(2,4)];g.heading=0
            cells=[(x,y) for y in range(5) for x in range(5) if (x,y) not in g.body]
            g.food=random.Random(seed).choice(cells)
            result=assess(g)
            self.assertTrue(result['resolved']);self.assertEqual(result['distance'],bfs_reference(g))
            for a,path in result['paths'].items():
                if path is None:continue
                h=restore(g.snapshot())
                for turn in path:h.step(turn)
                self.assertEqual(h.score,1);self.assertEqual(len(path),result['costs'][a])
    def test_tail_moves_and_collision(self):
        g=Snake();g.size=4;g.body=[(1,1),(1,2),(2,2),(2,1)];g.heading=0;g.food=(3,1)
        r=assess(g);self.assertEqual(r['costs']['right'],2)
        self.assertEqual(r['distance'],bfs_reference(g))
    def test_budget_is_unknown(self):
        g=Snake();self.assertEqual(shortest(g.body,g.heading,g.food,max_nodes=0)['status'],'budget_exhausted')
    def test_wall_and_one_step(self):
        g=Snake();g.body=[(0,0),(0,1),(0,2)];g.heading=0;g.food=(1,0)
        r=assess(g);self.assertEqual(r['optimal'],['right']);self.assertEqual(r['costs']['right'],1)
        self.assertEqual(r['status']['straight'],'immediate_collision')

if __name__=='__main__':unittest.main()
