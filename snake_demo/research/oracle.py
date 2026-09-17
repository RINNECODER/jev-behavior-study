"""Exact shortest path to CURRENT food using A* over the moving body.

No future food is inspected. Reaching food ends the search, so survival after
that arrival and global multi-food optimality are deliberately not certified.
"""
from heapq import heappop,heappush
from itertools import count
from collections import deque
from ..engine import Snake,ACTIONS,DIRECTIONS,VECTORS


def restore(state):
    g=Snake(state['level'],state['seed'],state['max_steps'],state['target'],state['starvation'])
    g.size=state['size'];g.wrap=state['wrap'];g.body=list(map(tuple,state['snake']))
    g.heading=DIRECTIONS.index(state['heading']);g.food=tuple(state['food']) if state['food'] else None
    g.obstacles=set(map(tuple,state['obstacles']));g.score=state['score'];g.moves=state['moves']
    g.since_food=state['since_food'];g.status=state['status']
    return g  # RNG is not restored; use for analysis/search, not future spawns.


def transition(body,heading,action,size,food,blocked):
    direction=(heading+ACTIONS[action])%4;dx,dy=VECTORS[direction]
    dest=(body[0][0]+dx,body[0][1]+dy);ate=dest==food
    if not(0<=dest[0]<size and 0<=dest[1]<size) or dest in blocked or dest in (body if ate else body[:-1]):return None
    return ((dest,)+body if ate else (dest,)+body[:-1],direction,ate)


def shortest(body,heading,food,size=12,blocked=frozenset(),max_nodes=100000):
    """Return exact distance/path or explicitly unknown on search budget exhaustion."""
    body=tuple(body);serial=count();start=(body,heading)
    h=lambda b:abs(b[0][0]-food[0])+abs(b[0][1]-food[1])
    queue=[(h(body),0,next(serial),body,heading,())];best={start:0};expanded=0
    while queue:
        _,cost,_,b,d,path=heappop(queue)
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
                best[key]=nc;heappush(queue,(nc+h(nb),nc,next(serial),nb,nd,np))
    return {'distance':None,'path':None,'status':'unreachable','expanded':expanded}


def assess(g,max_nodes=100000):
    assert not g.wrap and g.food is not None
    costs={};paths={};status={}
    for a in ACTIONS:
        nxt=transition(tuple(g.body),g.heading,a,g.size,g.food,g.obstacles)
        if nxt is None:costs[a]=None;paths[a]=None;status[a]='immediate_collision';continue
        b,d,ate=nxt
        if ate:result={'distance':0,'path':[],'status':'solved'}
        else:result=shortest(b,d,g.food,g.size,g.obstacles,max_nodes)
        status[a]=result['status'];costs[a]=None if result['distance'] is None else 1+result['distance']
        paths[a]=None if result['path'] is None else [a]+result['path']
    resolved=all(s!='budget_exhausted' for s in status.values())
    finite=[x for x in costs.values() if x is not None];minimum=min(finite) if finite else None
    optimal=[a for a,c in costs.items() if c is not None and c==minimum] if resolved else []
    return {'costs':costs,'paths':paths,'status':status,'resolved':resolved,'distance':minimum,'optimal':optimal,'legal':g.legal()}


def bfs_reference(g,cap=200000):
    """Independent breadth-first oracle for small fixtures; no heuristic."""
    q=deque([(tuple(g.body),g.heading,0)]);seen={(tuple(g.body),g.heading)}
    while q:
        b,d,c=q.popleft()
        for a in ACTIONS:
            nd=(d+ACTIONS[a])%4;dx,dy=VECTORS[nd];p=(b[0][0]+dx,b[0][1]+dy);ate=p==g.food
            if not g.in_bounds(p) or p in g.obstacles or p in (b if ate else b[:-1]):continue
            if ate:return c+1
            nb=(p,)+b[:-1];key=(nb,nd)
            if key not in seen:
                seen.add(key);q.append((nb,nd,c+1))
                if len(seen)>cap:return None
    return None
