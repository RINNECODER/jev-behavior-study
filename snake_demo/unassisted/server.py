"""Local live unassisted controllers: execute the model choice without correction."""
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer
import json
import os
import threading
import uuid
from ..server import Handler as BaseHandler
from ..controller import load_env
from ..engine import Snake,ACTIONS
from .policy import VARIANTS,decide,observation
from .run import ROOT
SESSIONS={};LOCK=threading.Lock()


def visible(d):
    last=d['calls'][-1]['record'];r=last.get('response',{})
    return {'action':d['action'],'first_action':d['first_action'],'answer':r.get('answers',{}).get('move'),
      'calls':[{'stage':c['stage'],'usage':c['record'].get('response',{}).get('usage'),'latency_ms':c['record']['latency_ms']} for c in d['calls']],
      'usage':r.get('usage'),'latency_ms':sum(c['record']['latency_ms'] for c in d['calls'])}

class Handler(BaseHandler):
    def do_GET(self):
        if self.path=='/':self.path='/unassisted.html'
        return super().do_GET()
    def do_POST(self):
        if self.headers.get('Origin') not in [None,'http://'+self.headers.get('Host','')]:return self.reply({'error':'Origin is not allowed'},403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply({'error':'JSON required'},415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<10000:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(length))
            if self.path=='/api/start':
                variant=data.get('variant');seed=int(data.get('seed',9101))
                if variant not in VARIANTS or not 0<=seed<2**32:raise ValueError('Invalid variant or seed')
                if not os.environ.get('TYPESAFE_API_KEY'):raise ValueError('Set TYPESAFE_API_KEY on the server')
                g=Snake(seed=seed);ident=uuid.uuid4().hex;path=ROOT.parent/'records'/('live-unassisted-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+ident[:6]);path.mkdir()
                (path/'initial.json').write_text(json.dumps({'variant':variant,'state':g.snapshot()}))
                with LOCK:
                    if len(SESSIONS)>=32:SESSIONS.pop(next(iter(SESSIONS)))
                    SESSIONS[ident]=(g,variant,[],threading.Lock(),path)
                return self.reply({'id':ident,'state':g.snapshot()})
            if self.path=='/api/step':
                with LOCK:session=SESSIONS.get(data.get('id'))
                if not session:return self.reply({'error':'Unknown game'},404)
                g,variant,history,lock,path=session
                with lock:
                    if g.status!='playing' or data.get('moves')!=g.moves:return self.reply({'error':'Ended game or stale frame'},409)
                    before=g.snapshot();order=list(ACTIONS);offset=(g.seed+g.moves)%3;order=order[offset:]+order[:offset]
                    d=decide(g,variant,history,order)
                    if d['action'] is None:g.status='api_error'
                    else:history.append({'observation':observation(g),'action':d['action']});g.step(d['action'])
                    row={'before':before,'decision':d,'after':g.snapshot()}
                    with (path/'moves.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                    if g.status=='api_error':return self.reply({'error':'Model request failed; game stopped without fallback.'},502)
                    return self.reply({'state':g.snapshot(),'decision':visible(d)})
            return self.reply({'error':'Unknown endpoint'},404)
        except (ValueError,TypeError,KeyError) as error:return self.reply({'error':str(error)},400)


def main():
    load_env(ROOT.parents[1]/'.env')
    server=ThreadingHTTPServer(('127.0.0.1',8767),Handler)
    print('Unassisted Snake: http://127.0.0.1:8767/ (live Jev '+str(bool(os.environ.get('TYPESAFE_API_KEY')))+')',flush=True);server.serve_forever()
if __name__=='__main__':main()
