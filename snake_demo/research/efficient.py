"""Bounded certificates avoid fully solving strictly worse alternatives.

Find the optimum once, then ask whether each first move can achieve that optimum.
A failed bounded search certifies only `cannot reach within D`, not unreachability.
"""
from heapq import heappop,heappush
from itertools import count
from .oracle import transition,shortest
from ..engine import ACTIONS


def bounded(body,heading,food,size,blocked,limit,max_nodes=100000):
    if limit<1:return {'status':'beyond_bound','path':None,'expanded':0}
    body=tuple(body);serial=count();h=lambda b:abs(b[0][0]-food[0])+abs(b[0][1]-food[1])
    queue=[(h(body),0,next(serial),body,heading,())];best={(body,heading):0};expanded=0
    while queue:
        f,c,_,b,d,path=heappop(queue)
        if f>limit:break
        if best.get((b,d))!=c:continue
        expanded+=1
        if expanded>max_nodes:return {'status':'budget_exhausted','path':None,'expanded':expanded}
        for a in ACTIONS:
            result=transition(b,d,a,size,food,blocked)
            if result is None:continue
            nb,nd,ate=result;nc=c+1;np=path+(a,)
            if ate:return {'status':'solved','path':list(np),'expanded':expanded}
            key=(nb,nd)
            if nc+h(nb)<=limit and nc<best.get(key,10**9):best[key]=nc;heappush(queue,(nc+h(nb),nc,next(serial),nb,nd,np))
    return {'status':'beyond_bound','path':None,'expanded':expanded}


def certify(g):
    root=shortest(g.body,g.heading,g.food,g.size,g.obstacles)
    result={'distance':root['distance'],'optimal':[],'paths':{},'status':{},'lower_bounds':{},'resolved':root['status']=='solved','root_status':root['status'],'expanded':root['expanded'],'legal':g.legal()}
    if not result['resolved']:return result
    distance=root['distance']
    for a in ACTIONS:
        first=transition(tuple(g.body),g.heading,a,g.size,g.food,g.obstacles)
        if first is None:result['status'][a]='immediate_collision';result['paths'][a]=None;result['lower_bounds'][a]=None;continue
        b,d,ate=first
        r={'status':'solved','path':[],'expanded':0} if ate else bounded(b,d,g.food,g.size,g.obstacles,distance-1)
        result['expanded']+=r['expanded'];result['status'][a]=r['status'];result['paths'][a]=None if r['path'] is None else [a]+r['path']
        if r['status']=='budget_exhausted':result['resolved']=False;result['lower_bounds'][a]=None
        elif r['status']=='solved':
            assert len(result['paths'][a])==distance
            result['optimal'].append(a);result['lower_bounds'][a]=distance
        else:result['lower_bounds'][a]=distance+1
    if not result['resolved']:result['optimal']=[]
    return result
