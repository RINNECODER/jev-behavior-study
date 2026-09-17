"""Adaptive A* equal-f tie break favors deeper states; same admissible heuristic."""
from heapq import heappop,heappush
from itertools import count
from .oracle import transition
from ..engine import ACTIONS

def shortest_deep(body,heading,food,size=12,blocked=frozenset(),max_nodes=100000):
    """Return exact distance/path or explicitly unknown on search budget exhaustion."""
    body=tuple(body);serial=count();start=(body,heading)
    h=lambda b:abs(b[0][0]-food[0])+abs(b[0][1]-food[1])
    queue=[(h(body),0,next(serial),body,heading,())];best={start:0};expanded=0
    while queue:
        _,negative_cost,_,b,d,path=heappop(queue)
        cost=-negative_cost
        if best.get((b,d))!=cost:continue
        expanded+=1
        if expanded>max_nodes:return {'distance':None,'path':None,'status':'budget_exhausted','expanded':expanded}
        for a in ACTIONS:
            result=transition(b,d,a,size,food,blocked)
            if result is None:continue
            nb,nd,ate=result;nc=cost+1;np=path+(a,)
            if ate:
                # A goal generated from a popped state is optimal here: all
                # goal predecessors have h=1, so its f is exactly nc.
                return {'distance':nc,'path':list(np),'status':'solved','expanded':expanded}
            key=(nb,nd)
            if nc<best.get(key,10**9):
                best[key]=nc;heappush(queue,(nc+h(nb),-nc,next(serial),nb,nd,np))
    return {'distance':None,'path':None,'status':'unreachable','expanded':expanded}

