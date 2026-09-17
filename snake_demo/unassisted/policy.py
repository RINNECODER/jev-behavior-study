"""Observation-only model policies. Deliberately contains no solver imports."""
from ..engine import ACTIONS,DIRECTIONS,VECTORS
from ..controller import make_payload,MODEL
from ..research.experiment import call
VARIANTS=['original','priority','narrative','ascii','egocentric','history','absolute','review']
PRIORITY=('Choose the next Snake move. Your priorities are: (1) do not collide on this move; '
 '(2) reach the CURRENT food using as few moves as possible; (3) do not circle indefinitely. '
 'Food is eaten only when the head enters its cell. Each turn advances exactly one cell. '
 'Solid edges kill; touching body kills. The tail cell vacates unless this move eats food. '
 'No reverse turn. Infer safety and the route yourself from the observation. '
 'All three offered actions are possible commands, not necessarily safe commands.')


def observation(g):
    return {'board':{'width':g.size,'height':g.size,'solid_edges':True,'coordinates':'x increases right, y increases down; indices 0 through 11'},
      'snake_head_to_tail':[list(p) for p in g.body],'heading':DIRECTIONS[g.heading],
      'food':list(g.food),'foods_eaten':g.score,'moves_without_food':g.since_food}


def relative_geometry(g):
    hx,hy=g.body[0];fx,fy=VECTORS[g.heading];rx,ry=VECTORS[(g.heading+1)%4]
    def point(p):
        dx,dy=p[0]-hx,p[1]-hy
        return [dx*rx+dy*ry,dx*fx+dy*fy]
    corners=[point(p) for p in [(0,0),(0,g.size-1),(g.size-1,0),(g.size-1,g.size-1)]]
    return {'coordinates':'Head is (0,0), facing positive y. Positive x is your right. Coordinates are cells, not distances or scores.',
      'board_bounds_inclusive':{'min_x':min(p[0] for p in corners),'max_x':max(p[0] for p in corners),'min_y':min(p[1] for p in corners),'max_y':max(p[1] for p in corners)},
      'solid_edges':True,'snake_head_to_tail':[point(p) for p in g.body],'food':point(g.food),'foods_eaten':g.score,'moves_without_food':g.since_food}


def payload(g,variant,history,order,proposal=None):
    if variant=='original':
        p=make_payload(g,'jev_direct');c=p['questions']['move']['criteria'];p['questions']['move']['criteria']={a:c[a] for a in order}
        return p,{a:a for a in order}
    state=observation(g);criteria={};mapping={}
    for a in order:
        direction=DIRECTIONS[(g.heading+ACTIONS[a])%4];x,y=g.destination(a);key=direction if variant=='absolute' else a
        mapping[key]=a;criteria[key]=f'Turn {a} relative to heading; advance {direction} to ({x}, {y}).' if a!='straight' else f'Continue straight; advance {direction} to ({x}, {y}).'
    if variant=='narrative':
        state=(f'The board is {g.size} by {g.size}, coordinates 0..{g.size-1}. x increases right and y down. '
         f'Edges are solid. The snake faces {DIRECTIONS[g.heading]}. '
         f'Its cells in order from head to tail are: '+', '.join(f'({x},{y})' for x,y in g.body)+'. '
         f'Food is at ({g.food[0]},{g.food[1]}). Foods eaten: {g.score}. Moves without food: {g.since_food}.')
    elif variant=='ascii':
        grid=[['.' for _ in range(g.size)] for _ in range(g.size)]
        for x,y in g.body:grid[y][x]='B'
        x,y=g.body[-1];grid[y][x]='T';x,y=g.body[0];grid[y][x]='H';x,y=g.food;grid[y][x]='F'
        state['grid_legend']='Rows top to bottom (y=0..11), columns left to right (x=0..11). H head, B body, T tail, F food, . empty. Use ordered body list for tail movement.'
        state['grid_rows']=[''.join(row) for row in grid]
    elif variant=='egocentric':
        state=relative_geometry(g);dest={'left':(-1,0),'straight':(0,1),'right':(1,0)}
        criteria={a:f'Advance one cell to {dest[a]} in the supplied head-relative coordinates.' for a in order}
    elif variant=='history':state['previous_observations_and_executed_moves']=history[-4:]
    elif variant=='review' and proposal is not None:state['your_previous_proposal']=proposal
    instruction=PRIORITY
    if variant=='review' and proposal is not None:
        instruction+=' A previous independent call proposed the supplied move. It may be wrong. Re-evaluate against the same board and rules; choose your final action. Keep it only if you judge it best. No external correctness feedback is available.'
    return {'model':MODEL,'state':state,'questions':{'move':{'type':'choice','instructions':instruction,'criteria':criteria}}},mapping


def decide(g,variant,history,order):
    calls=[];p,m=payload(g,variant,history,order);first=call(p);calls.append({'stage':'proposal','record':first})
    if not first['valid']:return {'calls':calls,'action':None,'first_action':None}
    action=m[first['response']['answers']['move']['choice']];first_action=action
    if variant=='review':
        p,m=payload(g,variant,history,order,action);second=call(p);calls.append({'stage':'review','record':second})
        if not second['valid']:return {'calls':calls,'action':None,'first_action':first_action}
        action=m[second['response']['answers']['move']['choice']]
    return {'calls':calls,'first_action':first_action,'action':action}
