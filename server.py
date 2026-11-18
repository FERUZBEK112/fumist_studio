"""FUMIST Studio HTTP API. Python 3.12+, no web-framework dependency."""
import hashlib
import http.cookies
import json
import mimetypes
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.parse
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import core
import engine
import bots

STATIC=core.ROOT/'static'
RATE=defaultdict(deque)
RATE_LOCK=threading.Lock()

def rate(key,limit,window=60):
    with RATE_LOCK:
        queue=RATE[key]; cutoff=time.time()-window
        while queue and queue[0]<cutoff: queue.popleft()
        if len(queue)>=limit: raise core.Error('rate_limit',429)
        queue.append(time.time())
        if len(RATE)>10000:
            for k in list(RATE):
                if not RATE[k] or RATE[k][-1]<cutoff: del RATE[k]

def config():
    return {'name':'FUMIST Studio','version':core.VERSION,'plans':core.PLANS,
        'prices':{p:{'uzs':core.price(p,'UZS'),'stars':core.price(p,'STARS')} for p in ('plus','pro')},
        'billing':core.enabled('BILLING_ENABLED'),'bot':core.setting('BOT_USERNAME'),
        'card_ready':bool(core.setting('CARD_NUMBER') and core.setting('CARD_HOLDER') and core.admins() and core.setting('ADMIN_BOT_TOKEN')),
        'ai':core.enabled('ENABLE_AI_TRANSCRIPTION'),'support':core.setting('SUPPORT_USERNAME','ferapmg'),
        'max_upload_mb':int(core.setting('MAX_UPLOAD_MB','200')),'subscription_period':'calendar_month','approval_required':True}

class Server(HTTPServer):
    request_queue_size=64
    allow_reuse_address=True
    def __init__(self,*args,**kwargs):
        self.pool=ThreadPoolExecutor(max_workers=24)
        super().__init__(*args,**kwargs)
    def process_request(self,request,address): self.pool.submit(self.process,request,address)
    def process(self,request,address):
        try: self.finish_request(request,address)
        except (BrokenPipeError,ConnectionResetError,socket.timeout): pass
        except Exception as exc: print('HTTP request failed',type(exc).__name__)
        finally: self.shutdown_request(request)

def owner_dashboard(search):
    with core.db() as c:
        def rows(sql,args=()): return [dict(row) for row in c.execute(sql,args)]
        return {
            'users':rows("""SELECT username,telegram_id,CASE WHEN expires>? THEN plan ELSE 'free' END AS plan,
                expires,blocked FROM users WHERE instr(lower(username),lower(?)) OR instr(COALESCE(CAST(telegram_id AS TEXT),''),?) OR ?=''
                ORDER BY created DESC LIMIT 50""",(core.now(),search,search,search)),
            'totals':dict(c.execute("""SELECT (SELECT count(*) FROM users) AS users,
                (SELECT count(*) FROM users WHERE plan!='free' AND expires>?) AS active,
                (SELECT count(*) FROM projects) AS projects,
                (SELECT count(*) FROM orders WHERE status IN ('review','paid_review')) AS pending""",(core.now(),)).fetchone()),
            'orders':rows("""SELECT o.id,u.username,o.plan,o.amount,o.currency,o.status,o.receipt IS NOT NULL AS has_receipt
                FROM orders o JOIN users u ON u.id=o.user_id
                ORDER BY (o.status IN ('review','paid_review')) DESC,o.created DESC LIMIT 50"""),
            'jobs':rows('SELECT u.username,j.kind,j.status,j.progress FROM jobs j JOIN users u ON u.id=j.user_id ORDER BY j.created DESC LIMIT 30'),
            'audit':rows('SELECT action,target,created FROM audit ORDER BY id DESC LIMIT 30')
        }

class Handler(BaseHTTPRequestHandler):
    server_version='FUMIST'
    protocol_version='HTTP/1.1'
    def setup(self): super().setup(); self.connection.settimeout(60)
    def log_message(self,format,*args):
        # No query parameters or credentials in logs.
        print(self.command,urllib.parse.urlsplit(self.path).path,getattr(self,'status_code',''))
    def headers_common(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Permissions-Policy','camera=(),geolocation=()')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' https://telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors https://web.telegram.org https://*.telegram.org; object-src 'none'; base-uri 'self'")
    def json(self,data,status=200,cookie=None):
        raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.status_code=status; self.send_response(status); self.headers_common()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        if cookie is not None:
            secure='; Secure' if core.setting('PUBLIC_URL').startswith('https://') else ''
            self.send_header('Set-Cookie',f'fumist_session={cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age={604800 if cookie else 0}{secure}')
        self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def length(self,maximum):
        if self.headers.get('Transfer-Encoding'): raise core.Error('unsupported_transfer')
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError: raise core.Error('invalid_body')
        if not 0<size<=maximum: raise core.Error('file_too_large',413)
        return size
    def body(self):
        if 'application/json' not in self.headers.get('Content-Type',''): raise core.Error('invalid_body')
        try: value=json.loads(self.rfile.read(self.length(2*1024*1024)))
        except (ValueError,UnicodeError): raise core.Error('invalid_body')
        if not isinstance(value,dict): raise core.Error('invalid_body')
        return value
    def auth(self):
        cookies=http.cookies.SimpleCookie()
        try: cookies.load(self.headers.get('Cookie',''))
        except http.cookies.CookieError: raise core.Error('login_required',401)
        token=cookies.get('fumist_session')
        return core.session_user(token.value if token else '')
    def mutation(self):
        if self.headers.get('X-Fumist')!='1': raise core.Error('invalid_request',403)
        origin=self.headers.get('Origin')
        expected=core.setting('PUBLIC_URL').rstrip('/')
        if origin and origin != (expected or f'http://{self.headers.get("Host")}'): raise core.Error('invalid_origin',403)
    def do_GET(self): self.dispatch('GET')
    def do_POST(self): self.dispatch('POST')
    def do_DELETE(self): self.dispatch('DELETE')
    def dispatch(self,method):
        try:
            path=urllib.parse.urlsplit(self.path).path
            if method!='GET': self.mutation()
            if path=='/api/health': return self.json({'status':'ok','ffmpeg':bool(shutil.which(engine.FFMPEG))})
            if path=='/api/config': return self.json(config())
            if path.startswith('/api/auth/') and method=='POST':
                rate(('auth',self.client_address[0]),12,300)
                data=self.body(); action=path.rsplit('/',1)[1]
                if action=='register':
                    rate(('register_global',),100,3600)
                    u=core.register(str(data.get('username','')),str(data.get('password','')))
                elif action=='login':
                    with core.db() as c: row=c.execute('SELECT * FROM users WHERE username=?',(str(data.get('username','')).lower(),)).fetchone()
                    if not row or not core.verify_password(str(data.get('password','')),row['password']): raise core.Error('invalid_credentials',401)
                    u=core.user(row)
                elif action=='telegram-code':
                    u=core.consume_login_code(str(data.get('code','')))
                elif action=='telegram':
                    if not core.setting('BOT_TOKEN'): raise core.Error('bot_not_configured',503)
                    u=core.telegram_user(core.telegram_verify(str(data.get('initData','')),core.setting('BOT_TOKEN')))
                else: raise core.Error('not_found',404)
                source={'telegram':'telegram','telegram-code':'telegram_web'}.get(action,'web')
                session=core.session_create(u['id'],source)
                return self.json({'user':core.session_user(session)},cookie=session)
            if path=='/api/logout' and method=='POST':
                self.body()
                cookie=http.cookies.SimpleCookie(self.headers.get('Cookie','')); token=cookie.get('fumist_session')
                if token:
                    with core.db() as c: c.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(token.value.encode()).hexdigest(),))
                return self.json({'ok':True},cookie='')
            if path.startswith('/api/'):
                u=self.auth(); rate(('user',u['id']),180)
                if path.startswith('/api/owner/'):
                    if not u['is_owner']: raise core.Error('admin_only',403)
                    if path=='/api/owner/dashboard' and method=='GET':
                        query=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                        return self.json(owner_dashboard(query.get('search',[''])[0][:100]))
                    if path.startswith('/api/owner/receipt/') and method=='GET':
                        with core.db() as c: row=c.execute('SELECT receipt FROM orders WHERE id=?',(path.rsplit('/',1)[1],)).fetchone()
                        if not row or not row[0]: raise core.Error('not_found',404)
                        receipt=core.DATA/row[0]
                        return self.file(receipt,private=True,download='receipt'+receipt.suffix)
                    if path=='/api/owner/review' and method=='POST':
                        data=self.body()
                        if data.get('decision') not in ('approve','reject'): raise core.Error('invalid_body')
                        return self.json(core.review_order(data.get('order'),u['telegram_id'],data['decision']=='approve'))
                    raise core.Error('not_found',404)
                if path=='/api/me': return self.json({'user':u})
                if path=='/api/preferences' and method=='POST':
                    data=self.body(); lang=data.get('language',u['language']); theme=data.get('theme',u['theme'])
                    if lang not in ('uz','ru','en') or theme not in ('dark','light','system'): raise core.Error('invalid_preferences')
                    with core.db() as c: c.execute('UPDATE users SET language=?,theme=? WHERE id=?',(lang,theme,u['id']))
                    return self.json({'user':core.by_id(u['id'])})
                if path=='/api/telegram-link' and method=='POST':
                    self.body()
                    if not core.setting('BOT_USERNAME'): raise core.Error('bot_not_configured',503)
                    if u['telegram_id']: raise core.Error('already_linked',409)
                    token=core.uid()
                    with core.db() as c: c.execute('INSERT INTO links VALUES(?,?,?)',(token,u['id'],core.now()+600))
                    bot_name = core.setting('BOT_USERNAME').strip().lstrip('@')
                    return self.json({'url':f'https://t.me/{bot_name}?start=link_{token}'})
                if path=='/api/media' and method=='POST': return self.upload(u)
                if path=='/api/media':
                    with core.db() as c: rows=c.execute('SELECT * FROM media WHERE user_id=? ORDER BY created DESC',(u['id'],)).fetchall()
                    return self.json({'media':[self.media_json(r) for r in rows]})
                if path.startswith('/api/media/'):
                    parts=path.split('/'); m=engine.media_owned(parts[3],u['id'])
                    if method=='DELETE':
                        with core.db() as c:
                            if c.execute("SELECT 1 FROM jobs WHERE user_id=? AND status IN ('queued','running')",(u['id'],)).fetchone(): raise core.Error('job_pending',409)
                            c.execute('DELETE FROM media WHERE id=?',(m['id'],))
                        (core.DATA/m['path']).unlink(missing_ok=True)
                        return self.json({'ok':True})
                    if len(parts)==5 and parts[4]=='file': return self.file(core.DATA/m['path'],private=True)
                if path=='/api/projects' and method=='POST':
                    data=self.body(); name=str(data.get('name','Untitled'))[:100]; body=data.get('project',{})
                    # Empty drafts are allowed; actual render validation is always authoritative.
                    if not isinstance(body,dict): raise core.Error('invalid_project')
                    identifier=data.get('id') or core.uid()
                    if not re.fullmatch('[0-9a-f]{32}',identifier): raise core.Error('invalid_project')
                    with core.db() as c:
                        existing=c.execute('SELECT user_id FROM projects WHERE id=?',(identifier,)).fetchone()
                        if existing and existing[0]!=u['id']: raise core.Error('not_found',404)
                        if not existing and c.execute('SELECT COUNT(*) FROM projects WHERE user_id=?',(u['id'],)).fetchone()[0]>=100: raise core.Error('project_limit')
                        c.execute('INSERT INTO projects VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,body=excluded.body,updated=excluded.updated',
                                  (identifier,u['id'],name,json.dumps(body),core.now()))
                    return self.json({'id':identifier})
                if path=='/api/projects':
                    with core.db() as c: rows=c.execute('SELECT id,name,body,updated FROM projects WHERE user_id=? ORDER BY updated DESC',(u['id'],)).fetchall()
                    return self.json({'projects':[dict(r) for r in rows]})
                if path.startswith('/api/projects/') and method=='DELETE':
                    with core.db() as c: c.execute('DELETE FROM projects WHERE id=? AND user_id=?',(path.rsplit('/',1)[1],u['id']))
                    return self.json({'ok':True})
                if path=='/api/jobs' and method=='POST':
                    data=self.body(); return self.json(engine.enqueue(u,data.get('kind','render'),data.get('project',{})),202)
                if path=='/api/jobs':
                    with core.db() as c: rows=c.execute('SELECT id,kind,status,progress,result,error,created FROM jobs WHERE user_id=? ORDER BY created DESC LIMIT 50',(u['id'],)).fetchall()
                    return self.json({'jobs':[dict(r) for r in rows]})
                if path.startswith('/api/jobs/'):
                    with core.db() as c: row=c.execute('SELECT id,kind,status,progress,result,error,created FROM jobs WHERE id=? AND user_id=?',(path.rsplit('/',1)[1],u['id'])).fetchone()
                    if not row: raise core.Error('not_found',404)
                    return self.json(dict(row))
                if path.startswith('/api/download/'):
                    identifier=path.rsplit('/',1)[1]
                    with core.db() as c: row=c.execute("SELECT id FROM jobs WHERE id=? AND user_id=? AND kind='render' AND status='done'",(identifier,u['id'])).fetchone()
                    if not row: raise core.Error('not_found',404)
                    return self.file(core.DATA/'exports'/f'{identifier}.mp4',private=True,download='FUMIST-video.mp4')
                if path=='/api/orders' and method=='POST':
                    data=self.body(); method=data.get('method','card')
                    if data.get('terms') is not True: raise core.Error('accept_terms')
                    if method not in ('card','stars'): raise core.Error('invalid_payment_method')
                    if method=='card' and u.get('source')=='telegram': raise core.Error('telegram_stars_required',403)
                    if method=='stars' and (not u['telegram_id'] or not core.setting('BOT_TOKEN') or not core.setting('ADMIN_BOT_TOKEN') or not core.admins()): raise core.Error('bot_not_configured',503)
                    identifier=core.create_order(u,data.get('plan'),method)
                    if method=='stars':
                        try:
                            invoice=bots.api('user','createInvoiceLink',{'title':'FUMIST '+data['plan'].upper(),'description':bots.COPY[u['language']]['terms'],
                                'payload':identifier,'currency':'XTR','prices':[{'label':data['plan'].upper(),'amount':core.price(data['plan'],'STARS')}],'provider_token':''})
                        except Exception:
                            with core.db() as c: c.execute("UPDATE orders SET status='cancelled' WHERE id=?",(identifier,))
                            raise core.Error('telegram_error',502)
                        return self.json({'id':identifier,'invoice':invoice})
                    return self.json({'id':identifier,'card_number':core.setting('CARD_NUMBER'),'card_holder':core.setting('CARD_HOLDER')})
                if path=='/api/orders':
                    with core.db() as c: rows=c.execute('SELECT id,plan,amount,currency,method,status,created,reviewed,expires FROM orders WHERE user_id=? ORDER BY created DESC',(u['id'],)).fetchall()
                    return self.json({'orders':[dict(r) for r in rows]})
                if path.startswith('/api/orders/') and method=='GET':
                    with core.db() as c: row=c.execute('SELECT * FROM orders WHERE id=? AND user_id=?',(path.rsplit('/',1)[1],u['id'])).fetchone()
                    if not row: raise core.Error('not_found',404)
                    order=dict(row)
                    if order['status']!='awaiting': raise core.Error('already_reviewed',409)
                    if order['method']=='card':
                        if u.get('source')=='telegram': raise core.Error('telegram_stars_required',403)
                        order.update(card_number=core.setting('CARD_NUMBER'),card_holder=core.setting('CARD_HOLDER'))
                    else:
                        order['invoice']=bots.api('user','createInvoiceLink',{'title':'FUMIST '+order['plan'].upper(),
                            'description':bots.COPY[u['language']]['terms'],'payload':order['id'],'currency':'XTR',
                            'provider_token':'','prices':[{'label':order['plan'].upper(),'amount':order['amount']}]})
                    order.pop('charge_id',None); order.pop('receipt',None)
                    return self.json(order)
                if path.startswith('/api/receipt/') and method=='POST': return self.receipt(u,path.rsplit('/',1)[1])
                if path.startswith('/api/orders/') and method=='DELETE':
                    with core.db() as c: c.execute("UPDATE orders SET status='cancelled' WHERE id=? AND user_id=? AND status='awaiting'",(path.rsplit('/',1)[1],u['id']))
                    return self.json({'ok':True})
                raise core.Error('not_found',404)
            if method!='GET': raise core.Error('not_found',404)
            relative=urllib.parse.unquote(path).lstrip('/') or 'index.html'
            target=(STATIC/relative).resolve()
            if not target.is_relative_to(STATIC.resolve()) or not target.is_file(): raise core.Error('not_found',404)
            return self.file(target)
        except core.Error as exc: self.close_connection=True; self.json({'error':exc.code},exc.status)
        except (BrokenPipeError,ConnectionResetError,socket.timeout): self.close_connection=True
        except Exception as exc:
            self.close_connection=True
            print('API failed',type(exc).__name__)
            self.json({'error':'server_error'},500)
    def media_json(self,row):
        d=dict(row); d.pop('path',None); d['url']=f'/api/media/{d["id"]}/file'; return d
    def save_upload(self,destination,maximum):
        size=self.length(maximum); remaining=size
        try:
            with destination.open('xb') as file:
                while remaining:
                    chunk=self.rfile.read(min(1024*1024,remaining))
                    if not chunk: raise core.Error('incomplete_upload')
                    file.write(chunk); remaining-=len(chunk)
        except Exception: destination.unlink(missing_ok=True); raise
        return size
    def upload(self,u):
        name=Path(urllib.parse.unquote(self.headers.get('X-Filename','file')).replace('\\','/')).name[:200]
        ext=Path(name).suffix.lower()
        engine.demux(name)
        rate(('upload',u['id']),30,3600)
        maximum=int(core.setting('MAX_UPLOAD_MB','200'))*1024*1024
        size=self.length(maximum)
        quota=int(core.setting('STORAGE_QUOTA_MB','1000'))*1024*1024
        with core.db() as c: used=c.execute('SELECT COALESCE(SUM(size),0) FROM media WHERE user_id=?',(u['id'],)).fetchone()[0]
        if used+size>quota or shutil.disk_usage(core.DATA).free<size+500*1024*1024: raise core.Error('storage_limit',413)
        identifier=core.uid(); destination=core.DATA/'media'/f'{identifier}{ext}'
        self.save_upload(destination,maximum)
        try:
            info=engine.probe(destination)
            if info['kind']=='audio' and ext not in ('.mp3','.m4a','.wav','.aac'):
                converted=destination.with_suffix('.m4a')
                try:
                    engine.run(['-protocol_whitelist','file,pipe','-f',engine.demux(destination),'-i',str(destination),
                                '-vn','-map','0:a:0','-c:a','aac','-b:a','128k','-movflags','+faststart',str(converted)],timeout=120)
                    converted_size=converted.stat().st_size
                    info=engine.probe(converted)
                except (core.Error,subprocess.TimeoutExpired) as exc:
                    converted.unlink(missing_ok=True)
                    raise core.Error('invalid_media',422) from exc
                except Exception:
                    converted.unlink(missing_ok=True)
                    raise
                if used+converted_size>quota:
                    converted.unlink(missing_ok=True)
                    raise core.Error('storage_limit',413)
                destination.unlink()
                destination,ext,size=converted,'.m4a',converted_size
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        with core.db() as c:
            c.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?,?,?)',(identifier,u['id'],name,info['kind'],f'media/{identifier}{ext}',info['seconds'],info['width'],info['height'],info['has_audio'],size,core.now()))
            row=c.execute('SELECT * FROM media WHERE id=?',(identifier,)).fetchone()
        self.json(self.media_json(row),201)
    def receipt(self,u,identifier):
        if u.get('source')=='telegram': raise core.Error('telegram_stars_required',403)
        with core.db() as c: row=c.execute("SELECT * FROM orders WHERE id=? AND user_id=? AND method='card' AND status='awaiting'",(identifier,u['id'])).fetchone()
        if not row: raise core.Error('not_found',404)
        name=urllib.parse.unquote(self.headers.get('X-Filename','receipt'))
        ext=Path(name).suffix.lower()
        if ext not in ('.jpg','.jpeg','.png','.pdf'): raise core.Error('invalid_receipt')
        destination=core.DATA/'receipts'/f'{identifier}-{core.uid()}{ext}'
        self.save_upload(destination,10*1024*1024)
        magic=destination.read_bytes()[:16]
        if not (magic.startswith(b'%PDF-') or magic.startswith(b'\xff\xd8\xff') or magic.startswith(b'\x89PNG\r\n\x1a\n')):
            destination.unlink(missing_ok=True); raise core.Error('invalid_receipt')
        with core.db() as c:
            changed=c.execute("UPDATE orders SET status='review',receipt=? WHERE id=? AND status='awaiting'",(f'receipts/{destination.name}',identifier)).rowcount
        if not changed: destination.unlink(missing_ok=True); raise core.Error('already_reviewed',409)
        bots.notice_order(identifier)
        self.json({'status':'review'})
    def file(self,path,private=False,download=None):
        if not path.is_file(): raise core.Error('file_expired',404)
        size=path.stat().st_size; start=0; end=size-1; status=200
        byte_range=self.headers.get('Range')
        if byte_range:
            match=re.fullmatch(r'bytes=(\d+)-(\d*)',byte_range)
            if not match: raise core.Error('invalid_range',416)
            start=int(match[1]); end=min(int(match[2]) if match[2] else end,end)
            if start>end or start>=size: raise core.Error('invalid_range',416)
            status=206
        self.status_code=status; self.send_response(status); self.headers_common()
        media_types={'.mp3':'audio/mpeg','.m4a':'audio/mp4','.aac':'audio/aac','.wav':'audio/wav','.ogg':'audio/ogg'}
        self.send_header('Content-Type',media_types.get(path.suffix.lower()) or mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        self.send_header('Cache-Control','private, no-store' if private else 'no-cache')
        self.send_header('Accept-Ranges','bytes')
        if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        if download: self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.send_header('Content-Length',str(end-start+1)); self.end_headers()
        with path.open('rb') as file:
            file.seek(start); remaining=end-start+1
            while remaining>0:
                chunk=file.read(min(1024*1024,remaining))
                if not chunk: break
                self.wfile.write(chunk); remaining-=len(chunk)

def cleanup():
    while True:
        time.sleep(3600)
        try:
            cutoff=core.now()-int(core.setting('RETENTION_DAYS','30'))*86400
            with core.db() as c:
                c.execute('DELETE FROM sessions WHERE expires<?',(core.now(),))
                c.execute('DELETE FROM links WHERE expires<?',(core.now(),))
                c.execute("UPDATE orders SET status='expired' WHERE status='awaiting' AND created<?",(core.now()-86400,))
                rows=c.execute('SELECT id,path FROM media WHERE created<?',(cutoff,)).fetchall()
                for row in rows:
                    if c.execute("SELECT 1 FROM jobs WHERE status IN ('queued','running') AND body LIKE ?",('%'+row['id']+'%',)).fetchone(): continue
                    (core.DATA/row['path']).unlink(missing_ok=True)
                    c.execute('DELETE FROM media WHERE id=?',(row['id'],))
                for path in (core.DATA/'exports').glob('*.mp4'):
                    if path.stat().st_mtime<cutoff: path.unlink(missing_ok=True)
        except Exception as exc: print('Cleanup failed',type(exc).__name__)

def main():
    core.init()
    threading.Thread(target=engine.worker,daemon=True).start()
    threading.Thread(target=cleanup,daemon=True).start()
    bots.start()
    port=int(core.setting('PORT','8080'))
    print(f'FUMIST Studio: http://localhost:{port}')
    Server(('0.0.0.0',port),Handler).serve_forever()

if __name__=='__main__': main()
