"""Local user demo. No network inference or credential access."""
import json
import pathlib
import sqlite3
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from continuation import prepare

ROOT = pathlib.Path(__file__).resolve().parents[1]

class Memory:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, kind TEXT, data TEXT)')
    def add(self, kind, data):
        if kind not in ('checkpoint', 'update') or not isinstance(data, str) or not data.strip() or len(data)>2000:
            raise ValueError('Enter 1–2000 characters')
        self.db.execute('INSERT INTO events(kind,data) VALUES (?,?)', (kind,data.strip()))
        self.db.commit()
    def resume(self):
        rows = self.db.execute('SELECT id,kind,data FROM events ORDER BY id').fetchall()
        checkpoints = [r for r in rows if r[1]=='checkpoint']
        checkpoint = checkpoints[-1] if checkpoints else None
        updates = [r for r in rows if r[1]=='update' and (not checkpoint or r[0]>checkpoint[0])]
        return {'checkpoint': checkpoint, 'updates': updates,
                'next_step': 'Review changes, then confirm your next action.' if updates else 'Continue from your saved checkpoint.' if checkpoint else 'Save a checkpoint first.',
                'events': rows, 'mode':'LOCAL_PERSISTENT_MEMORY'}

def handler(dbpath, live_once=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def reply(self, obj, status=200):
            body=json.dumps(obj,ensure_ascii=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path=='/api/model-preview':
                m=Memory(dbpath)
                try:
                    try: self.reply(prepare(m.resume()))
                    except ValueError as exc: self.reply({'error':str(exc)},400)
                finally: m.db.close()
            elif self.path=='/api/resume':
                m=Memory(dbpath)
                try: self.reply(m.resume())
                finally: m.db.close()
            elif self.path=='/api/provider-evidence':
                self.reply(json.loads((ROOT/'evidence/PA09_OLD_EVIDENCE_LIVE.json').read_text(encoding='utf-8')))
            elif self.path=='/':
                body=(ROOT/'index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(body)
            else: self.reply({'error':'Not found'},404)
        def do_POST(self):
            if self.path=='/api/live-once':
                if not live_once: return self.reply({'error':'Live inference disabled'},403)
                if self.headers.get('X-AWM-Local')!='1': return self.reply({'error':'Local UI required'},403)
                from live_once import run
                m=Memory(dbpath)
                try:
                    try: self.reply(run(m.resume(),ROOT/'evidence'))
                    except Exception as exc: self.reply({'error':'Preflight blocked or approved call consumed','type':type(exc).__name__},409)
                finally: m.db.close()
                return
            if self.path!='/api/event': return self.reply({'error':'Not found'},404)
            try:
                size=int(self.headers.get('Content-Length',0))
                if size>10000: raise ValueError('Too large')
                obj=json.loads(self.rfile.read(size)); m=Memory(dbpath)
                try: m.add(obj.get('kind'),obj.get('data')); self.reply(m.resume())
                finally: m.db.close()
            except (ValueError,TypeError): self.reply({'error':'Invalid event'},400)
    return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8765); p.add_argument('--db',default=str(ROOT/'local-memory.sqlite')); p.add_argument('--live-once',action='store_true',help='Only after explicit approval of one billable call'); a=p.parse_args()
    print('AWM: http://127.0.0.1:'+str(a.port),flush=True)
    HTTPServer(('127.0.0.1',a.port),handler(a.db,a.live_once)).serve_forever()
