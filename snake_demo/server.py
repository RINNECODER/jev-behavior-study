"""Local-only live demo. Static replay files never need credentials."""
import argparse
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
import threading
import uuid
from .controller import choose,load_env
from .engine import Snake
ROOT=Path(__file__).resolve().parent
SESSIONS={};SESSION_LOCK=threading.Lock()

def public_decision(d):
    answer=d.get('response',{}).get('answers',{}).get('move',{})
    return {'action':d['action'],'source':d['source'],'latency_ms':d['latency_ms'],
        'probabilities':answer.get('probabilities',{}),'confidence':answer.get('confidence'),
        'usage':d.get('response',{}).get('usage',{'input_tokens':0,'output_tokens':0})}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
    def translate_path(self,path):
        if path.startswith('/records/'):
            from urllib.parse import unquote,urlsplit
            requested=(ROOT/unquote(urlsplit(path).path.lstrip('/'))).resolve()
            if requested.is_relative_to((ROOT/'records').resolve()):return str(requested)
            return str(ROOT/'web'/'not-found')
        return super().translate_path(path)
    def reply(self,data,status=200):
        body=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/api/config':return self.reply({'live':bool(os.environ.get('TYPESAFE_API_KEY')),'model':'jev-1.13.0'})
        return super().do_GET()
    def do_POST(self):
        if self.headers.get('Origin') not in [None,'http://'+self.headers.get('Host','')]:return self.reply({'error':'Origin is not allowed'},403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply({'error':'JSON required'},415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<10000:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(length))
            if self.path=='/api/start':
                seed=int(data.get('seed',101));controller=data.get('controller','jev_direct')
                if not 0<=seed<2**32:raise ValueError('Seed is out of range')
                if controller not in ['jev_direct','jev_guarded','baseline']:raise ValueError('Unknown controller')
                if controller!='baseline' and not os.environ.get('TYPESAFE_API_KEY'):return self.reply({'error':'Set TYPESAFE_API_KEY on the local server to use live Jev.'},400)
                game=Snake(data.get('level','classic'),seed);ident=uuid.uuid4().hex
                path=ROOT/'records'/('live-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+ident[:6]);path.mkdir()
                (path/'initial.json').write_text(json.dumps({'controller':controller,'initial':game.snapshot()}))
                with SESSION_LOCK:
                    if len(SESSIONS)>=32:SESSIONS.pop(next(iter(SESSIONS)))
                    SESSIONS[ident]=(game,controller,threading.Lock(),path)
                return self.reply({'id':ident,'state':game.snapshot()})
            if self.path=='/api/step':
                with SESSION_LOCK:session=SESSIONS.get(data.get('id'))
                if not session:return self.reply({'error':'Game expired. Start a new game.'},404)
                game,controller,lock,path=session
                with lock:
                    if game.status!='playing':return self.reply({'error':'Game has ended'},409)
                    if data.get('moves')!=game.moves:return self.reply({'error':'Stale frame. Reload the game.'},409)
                    before=game.snapshot()
                    try:decision=choose(game,controller);game.step(decision['action'])
                    except Exception as error:
                        game.status='api_error'
                        with (path/'moves.jsonl').open('a') as f:f.write(json.dumps({'before':before,'error':type(error).__name__,'after':game.snapshot()})+'\n')
                        return self.reply({'error':'Decision request failed ('+type(error).__name__+'). Game stopped; no automatic retry.'},502)
                    with (path/'moves.jsonl').open('a') as f:f.write(json.dumps({'before':before,'decision':decision,'after':game.snapshot()})+'\n')
                    return self.reply({'state':game.snapshot(),'decision':public_decision(decision)})
            return self.reply({'error':'Unknown endpoint'},404)
        except (ValueError,TypeError,KeyError) as error:return self.reply({'error':str(error)},400)
    def log_message(self,format,*args):pass

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    load_env(ROOT.parent/'.env')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Snake Lab: http://127.0.0.1:{args.port} (live Jev {"enabled" if os.environ.get("TYPESAFE_API_KEY") else "disabled"})',flush=True)
    server.serve_forever()
if __name__=='__main__':main()
