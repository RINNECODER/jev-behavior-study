"""Jev actions; credentials are server-side environment variables only."""
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime,timezone
from .engine import ACTIONS,DIRECTIONS
MODEL='jev-1.13.0'

INSTRUCTIONS=('Play Snake. Maximize food collected while staying alive. Select one relative turn and advance one cell. '
 'x increases rightward; y increases downward. The snake list starts with the head and ends with the tail. '
 'The tail vacates its cell on a move unless food is eaten. Reverse turns are not permitted. '
 'Avoid body, obstacles, and solid boundaries; wrap only when wrap is true. '
 'Choose a route toward food without trapping the snake. Use the supplied board state.')

def make_payload(game,controller):
    allowed=game.legal() if controller=='jev_guarded' else list(ACTIONS)
    # Position-balanced rotation, fixed before testing; no scores or pathfinder hints.
    order=list(ACTIONS);offset=(game.seed+game.moves)%3;order=order[offset:]+order[:offset]
    criteria={}
    for action in order:
        if action in allowed:
            direction=DIRECTIONS[(game.heading+ACTIONS[action])%4];x,y=game.destination(action)
            criteria[action]=f'{action.title()} relative to current heading: move {direction} to x={x}, y={y}.'
    return {'model':MODEL,'state':game.snapshot(),'questions':{'move':{'type':'choice','instructions':INSTRUCTIONS,'criteria':criteria}}}

def choose(game,controller):
    if controller=='baseline':return {'action':game.baseline(),'source':'baseline','latency_ms':0}
    if controller not in ['jev_direct','jev_guarded']:raise ValueError('Unknown controller')
    if controller=='jev_guarded':
        legal=game.legal()
        if len(legal)==1:return {'action':legal[0],'source':'forced_safe','latency_ms':0}
        if not legal:return {'action':'straight','source':'no_safe_move','latency_ms':0}
    payload=make_payload(game,controller);body=json.dumps(payload).encode();key=os.environ.get('TYPESAFE_API_KEY')
    if not key:raise RuntimeError('TYPESAFE_API_KEY is not set on the local server')
    request=urllib.request.Request('https://api.typesafe.ai/v1/systemone',data=body,
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Cache-Control':'no-cache'})
    started=datetime.now(timezone.utc).isoformat();t=time.perf_counter()
    with urllib.request.build_opener().open(request,timeout=60) as response:raw=response.read().decode();status=response.status
    elapsed=round((time.perf_counter()-t)*1000,2);parsed=json.loads(raw)
    if parsed.get('model')!=MODEL:raise RuntimeError('Returned model version differs from pinned model')
    answer=parsed['answers']['move'];choice=answer['choice']
    if answer.get('type')!='choice' or choice not in payload['questions']['move']['criteria']:raise RuntimeError('Invalid model action')
    return {'action':choice,'source':'jev','latency_ms':elapsed,'started_at':started,'http_status':status,
        'payload':payload,'payload_sha256':hashlib.sha256(body).hexdigest(),'raw_response':raw,'response':parsed}

def load_env(path):
    from pathlib import Path
    p=Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip('\"\''))
