"""Deterministic Snake rules. Coordinates: x right, y down; head first."""
from collections import deque
import random

LEVELS={'open':{'label':'Open','wrap':True,'obstacles':0},
 'classic':{'label':'Classic','wrap':False,'obstacles':0},
 'obstacles':{'label':'Obstacles','wrap':False,'obstacles':12},
 'dense':{'label':'Dense','wrap':False,'obstacles':24}}
VECTORS=[(0,-1),(1,0),(0,1),(-1,0)]
DIRECTIONS=['north','east','south','west']
ACTIONS={'left':-1,'straight':0,'right':1}

class Snake:
    def __init__(self,level='classic',seed=101,max_steps=200,target=8,starvation=50):
        if level not in LEVELS:raise ValueError('Unknown difficulty')
        self.level=level;self.seed=seed;self.size=12;self.wrap=LEVELS[level]['wrap']
        self.max_steps=max_steps;self.target=target;self.starvation=starvation
        self.rng=random.Random(seed);self.body=[(6,6),(6,7),(6,8)];self.heading=0
        self.obstacles=set();self.score=0;self.moves=0;self.since_food=0;self.status='playing';self.food=None
        candidates=[(x,y) for y in range(12) for x in range(12) if (x,y) not in self.body+[(6,5)]]
        rng=random.Random(seed+9000);rng.shuffle(candidates)
        for pos in candidates:
            if len(self.obstacles)==LEVELS[level]['obstacles']:break
            trial=self.obstacles|{pos}
            if len(self.reachable(self.body[0],trial))==144-len(trial):self.obstacles=trial
        assert len(self.obstacles)==LEVELS[level]['obstacles']
        self.spawn_food()
    def neighbor(self,p,heading):
        dx,dy=VECTORS[heading];x,y=p[0]+dx,p[1]+dy
        return (x%self.size,y%self.size) if self.wrap else (x,y)
    def in_bounds(self,p):return 0<=p[0]<self.size and 0<=p[1]<self.size
    def reachable(self,start,blocked):
        seen={start};queue=deque([start])
        while queue:
            p=queue.popleft()
            for d in range(4):
                n=self.neighbor(p,d)
                if self.in_bounds(n) and n not in blocked and n not in seen:seen.add(n);queue.append(n)
        return seen
    def spawn_food(self):
        free=[(x,y) for y in range(self.size) for x in range(self.size) if (x,y) not in self.obstacles and (x,y) not in self.body]
        if not free:self.food=None;self.status='board_filled'
        else:self.food=self.rng.choice(free)
    def destination(self,action):return self.neighbor(self.body[0],(self.heading+ACTIONS[action])%4)
    def safe(self,action):
        n=self.destination(action);occupied=self.body if n==self.food else self.body[:-1]
        return self.in_bounds(n) and n not in self.obstacles and n not in occupied
    def legal(self):return [a for a in ACTIONS if self.safe(a)]
    def step(self,action):
        if self.status!='playing':raise ValueError('Game is already over')
        if action not in ACTIONS:raise ValueError('Invalid action')
        n=self.destination(action);self.moves+=1
        if not self.safe(action):
            self.status='wall_collision' if not self.in_bounds(n) else 'obstacle_collision' if n in self.obstacles else 'body_collision'
            return self.snapshot()
        self.heading=(self.heading+ACTIONS[action])%4
        ate=n==self.food;self.body.insert(0,n)
        if ate:self.score+=1;self.since_food=0;self.spawn_food()
        else:self.body.pop();self.since_food+=1
        if self.status=='playing':
            if self.score>=self.target:self.status='target_reached'
            elif self.moves>=self.max_steps:self.status='step_limit'
            elif self.since_food>=self.starvation:self.status='no_food_limit'
        return self.snapshot()
    def snapshot(self):
        return {'level':self.level,'seed':self.seed,'size':self.size,'wrap':self.wrap,
            'snake':[list(p) for p in self.body],'obstacles':[list(p) for p in sorted(self.obstacles)],
            'food':list(self.food) if self.food else None,'heading':DIRECTIONS[self.heading],
            'score':self.score,'moves':self.moves,'since_food':self.since_food,'status':self.status,
            'max_steps':self.max_steps,'target':self.target,'starvation':self.starvation}
    def distance(self,start,goal,blocked):
        queue=deque([(start,0)]);seen={start}
        while queue:
            p,d=queue.popleft()
            if p==goal:return d
            for heading in range(4):
                n=self.neighbor(p,heading)
                if self.in_bounds(n) and n not in blocked and n not in seen:seen.add(n);queue.append((n,d+1))
        return 10000
    def baseline(self):
        legal=self.legal()
        if not legal:return 'straight'
        return min(legal,key=lambda a:(self.distance(self.destination(a),self.food,self.obstacles|set(self.body[:-1])),list(ACTIONS).index(a)))
