"""Local-only Jev proxy. The shared JS simulator owns physics; credentials stay here."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'records' / ('live-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
GATE = threading.BoundedSemaphore(2)
WRITE = threading.Lock()
MODEL = 'jev-1.13.0'


def load_env():
    path = ROOT.parent / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('\"\''))


def call(payload):
    body = json.dumps(payload).encode()
    row = {'payload': payload, 'payload_sha256': hashlib.sha256(body).hexdigest(),
           'started_at': datetime.now(timezone.utc).isoformat()}
    start = time.perf_counter()
    try:
        req = urllib.request.Request('https://api.typesafe.ai/v1/systemone', data=body,
          headers={'Authorization': 'Bearer ' + os.environ['TYPESAFE_API_KEY'], 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=20) as response:
            row['http_status'] = response.status
            row['raw_response'] = response.read().decode()
        r = json.loads(row['raw_response'])
        row['response'] = r
        qid = next(iter(payload['questions']))
        a = r['answers'][qid]
        if r['model'] != MODEL or a['type'] != 'choice' or a['choice'] not in payload['questions'][qid]['criteria']:
            raise ValueError('Invalid model response')
        row['valid'] = True
    except Exception as error:
        row['valid'] = False
        row['error'] = type(error).__name__
        if isinstance(error, urllib.error.HTTPError):
            row['http_status'] = error.code
            row['raw_response'] = error.read().decode(errors='replace')
    row['latency_ms'] = round((time.perf_counter() - start) * 1000, 2)
    return row


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def reply(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def allowed(self):
        return self.headers.get('Host') in ('127.0.0.1:8768', 'localhost:8768') and self.headers.get('Origin') in (None, 'http://' + self.headers.get('Host', ''))

    def do_GET(self):
        if not self.allowed():
            return self.reply({'error': 'Local origin required'}, 403)
        path = urlsplit(self.path).path
        if path == '/api/status':
            return self.reply({'live': bool(os.environ.get('TYPESAFE_API_KEY')), 'model': MODEL, 'native_vision': False})
        # Serve only the demo directory; hidden files and server code are not public assets.
        if any(p.startswith('.') for p in path.split('/') if p) or path.endswith('.py'):
            return self.reply({'error': 'Not found'}, 404)
        return super().do_GET()

    def do_POST(self):
        if not self.allowed():
            return self.reply({'error': 'Local origin required'}, 403)
        if self.path != '/api/decide':
            return self.reply({'error': 'Unknown endpoint'}, 404)
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply({'error': 'JSON required'}, 415)
        if not os.environ.get('TYPESAFE_API_KEY'):
            return self.reply({'error': 'Server has no TYPESAFE_API_KEY'}, 503)
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size < 30000:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(size))
            payloads = data['payloads']
            if not isinstance(payloads, list) or len(payloads) != 2:
                raise ValueError('Exactly two single-question calls required')
            for p in payloads:
                if p.get('model') != MODEL or len(p['questions']) != 1:
                    raise ValueError('Invalid model or question count')
                q = next(iter(p['questions'].values()))
                if q['type'] != 'choice' or not 2 <= len(q['criteria']) <= 5:
                    raise ValueError('Invalid choice question')
        except (ValueError, KeyError, TypeError) as error:
            return self.reply({'error': str(error)}, 400)
        if not GATE.acquire(blocking=False):
            return self.reply({'error': 'Two decisions already in flight'}, 429)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                rows = list(pool.map(call, payloads))
            ident = uuid.uuid4().hex
            result = {'id': ident, 'calls': rows, 'valid': all(r['valid'] for r in rows)}
            RUN.mkdir(parents=True, exist_ok=True)
            with WRITE, (RUN / 'calls.jsonl').open('a') as f:
                f.write(json.dumps(result) + '\n')
            return self.reply(result)
        finally:
            GATE.release()


if __name__ == '__main__':
    load_env()
    print('City lab: http://127.0.0.1:8768/ | live Jev configured: ' + str(bool(os.environ.get('TYPESAFE_API_KEY'))), flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8768), Handler).serve_forever()
