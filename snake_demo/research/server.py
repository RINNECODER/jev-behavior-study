"""Local live Classic experiment viewer; keys and raw calls stay server-side."""
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer
import json
import os
import threading
import uuid
from ..server import Handler as BaseHandler
from ..controller import load_env
from ..engine import Snake
from .experiment import ROOT
from .gameplay import decision
SESSIONS={};LOCK=threading.Lock()
PROFILES={'unassisted':'original','assisted':'exact','verified':'exact','oracle':None}


def visible(d):
    c=d.get('call');r=c.get('response') if c and c.get('valid') else None
    return {k:d[k] for k in ['action','proposal','overridden','oracle','planner_ms']}|{'answer':r['answers']['move'] if r else None,'usage':r['usage'] if r else {'input_tokens':0,'output_tokens':0},'latency_ms':c['latency_ms'] if c else 0}

class Handler(BaseHandler):
    def do_GET(self):
        if self.path=='/':self.path='/classic.html'
        return super().do_GET()
    def do_POST(self):
        if self.headers.get('Origin') not in [None,'http://'+self.headers.get('Host','')]:return self.reply({'error':'Origin is not allowed'},403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply({'error':'JSON required'},415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<10000:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(length))
            if self.path=='/api/start':
                profile=data.get('profile');seed=int(data.get('seed',1001))
                if profile not in PROFILES or not 0<=seed<2**32:raise ValueError('Invalid profile or seed')
                if profile!='oracle' and not os.environ.get('TYPESAFE_API_KEY'):raise ValueError('Set TYPESAFE_API_KEY on the local server')
                ident=uuid.uuid4().hex;g=Snake(seed=seed)
                path=ROOT.parent/'records'/('live-research-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+ident[:6]);path.mkdir()
                (path/'initial.json').write_text(json.dumps({'profile':profile,'state':g.snapshot()}))
                with LOCK:
                    if len(SESSIONS)>=32:SESSIONS.pop(next(iter(SESSIONS)))
                    SESSIONS[ident]=(g,profile,threading.Lock(),path)
                return self.reply({'id':ident,'state':g.snapshot()})
            if self.path=='/api/step':
                with LOCK:session=SESSIONS.get(data.get('id'))
                if not session:return self.reply({'error':'Unknown game'},404)
                g,profile,lock,path=session
                with lock:
                    if g.status!='playing' or data.get('moves')!=g.moves:return self.reply({'error':'Ended game or stale frame'},409)
                    before=g.snapshot()
                    try:
                        d=decision(g,profile,PROFILES[profile])
                        if d['action'] is None:
                            g.status='api_error';row={'before':before,'decision':d,'after':g.snapshot()}
                        else:g.step(d['action']);row={'before':before,'decision':d,'after':g.snapshot()}
                    except Exception as error:
                        g.status='planner_error';row={'before':before,'error':type(error).__name__,'after':g.snapshot()}
                    with (path/'moves.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                    if 'error' in row or g.status=='api_error':return self.reply({'error':'Decision failed; game stopped. See local log.'},502)
                    return self.reply({'state':g.snapshot(),'decision':visible(d)})
            return self.reply({'error':'Unknown endpoint'},404)
        except (ValueError,TypeError,KeyError) as error:return self.reply({'error':str(error)},400)


def main():
    load_env(ROOT.parents[1]/'.env')
    server=ThreadingHTTPServer(('127.0.0.1',8766),Handler)
    print('Classic research lab: http://127.0.0.1:8766/ (live Jev '+str(bool(os.environ.get('TYPESAFE_API_KEY')))+')',flush=True)
    server.serve_forever()
if __name__=='__main__':main()
