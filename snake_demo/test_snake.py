import unittest
from .engine import Snake,LEVELS
from .controller import choose,make_payload

class SnakeTests(unittest.TestCase):
    def test_deterministic_and_connected_obstacles(self):
        for level in LEVELS:
            for seed in [101,102,108]:
                a=Snake(level,seed);b=Snake(level,seed)
                self.assertEqual(a.snapshot(),b.snapshot())
                self.assertEqual(len(a.reachable(a.body[0],a.obstacles)),144-len(a.obstacles))
                self.assertNotIn(a.food,a.body);self.assertNotIn(a.food,a.obstacles)
    def test_relative_turns(self):
        g=Snake();self.assertEqual(g.destination('left'),(5,6));self.assertEqual(g.destination('right'),(7,6))
        g.step('right');self.assertEqual(g.heading,1);self.assertEqual(g.destination('left'),(7,5))
    def test_growth(self):
        g=Snake();g.food=(6,5);g.step('straight')
        self.assertEqual(g.score,1);self.assertEqual(len(g.body),4);self.assertEqual(g.body[0],(6,5))
        self.assertNotIn(g.food,g.body)
    def test_wall_and_wrap(self):
        for level in ['classic','open']:
            g=Snake(level);g.body=[(0,0),(0,1),(0,2)];g.heading=0;g.food=(9,9);g.step('straight')
            self.assertEqual(g.status,'wall_collision' if level=='classic' else 'playing')
            if level=='open':self.assertEqual(g.body[0],(0,11))
    def test_vacating_tail_is_legal(self):
        g=Snake();g.body=[(3,3),(3,4),(2,4),(2,3)];g.food=(10,10)
        self.assertTrue(g.safe('left'));g.step('left');self.assertEqual(g.status,'playing')
        self.assertEqual(g.body[0],(2,3));self.assertEqual(len(set(g.body)),4)
    def test_body_and_obstacle(self):
        g=Snake();g.body=[(3,3),(3,4),(2,4),(2,3),(2,2)];g.food=(10,10);g.step('left')
        self.assertEqual(g.status,'body_collision')
        g=Snake();g.obstacles.add((6,5));g.step('straight');self.assertEqual(g.status,'obstacle_collision')
    def test_limits(self):
        g=Snake(max_steps=1);g.food=(0,0);g.step('straight');self.assertEqual(g.status,'step_limit')
        g=Snake(starvation=1);g.food=(0,0);g.step('straight');self.assertEqual(g.status,'no_food_limit')
        g=Snake(target=1);g.food=(6,5);g.step('straight');self.assertEqual(g.status,'target_reached')
    def test_guarding_is_explicit(self):
        g=Snake();g.obstacles|={(5,6),(7,6)}
        self.assertEqual(choose(g,'jev_guarded')['source'],'forced_safe')
        self.assertEqual(choose(g,'jev_guarded')['action'],'straight')
        self.assertEqual(len(make_payload(g,'jev_direct')['questions']['move']['criteria']),3)
        self.assertEqual(set(make_payload(g,'jev_guarded')['questions']['move']['criteria']),{'straight'})
    def test_baseline_replay(self):
        for level in LEVELS:
            a=Snake(level,103);b=Snake(level,103)
            while a.status=='playing':
                move=a.baseline();self.assertEqual(move,b.baseline());a.step(move);b.step(move)
                self.assertEqual(a.snapshot(),b.snapshot())
            self.assertGreater(a.score,0)

if __name__=='__main__':unittest.main()
