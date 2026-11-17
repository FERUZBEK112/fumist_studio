"""Persistent state and authorization. No subscription can be granted by a client."""
import calendar
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA = Path(os.getenv('DATA_DIR', str(ROOT / 'data')))
PLANS = {
    'free': {'height': 720, 'seconds': 120, 'exports': 3, 'clips': 10, 'ai': 1},
    'plus': {'height': 1080, 'seconds': 600, 'exports': 15, 'clips': 30, 'ai': 5},
    'pro': {'height': 1080, 'seconds': 1200, 'exports': 40, 'clips': 60, 'ai': 15},
}

class Error(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status

def now(): return int(time.time())
def uid(): return secrets.token_hex(16)
def setting(key, default=''): return os.getenv(key, default)
def enabled(key): return setting(key).lower() == 'true'
def admins(): return {int(s.strip()) for s in setting('ADMIN_IDS').split(',') if s.strip().isdigit()}

@contextmanager
def db():
    conn = sqlite3.connect(DATA / 'studio.sqlite', timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally: conn.close()

def init():
    DATA.mkdir(parents=True, exist_ok=True)
    for folder in ['media', 'receipts', 'exports', 'work']: (DATA / folder).mkdir(exist_ok=True)
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE,password TEXT,
          telegram_id INTEGER UNIQUE,language TEXT DEFAULT 'uz',theme TEXT DEFAULT 'system',
          plan TEXT DEFAULT 'free',expires INTEGER DEFAULT 0,blocked INTEGER DEFAULT 0,created INTEGER);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),expires INTEGER,source TEXT);
        CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),name TEXT,kind TEXT,
          path TEXT,seconds REAL,width INTEGER,height INTEGER,has_audio INTEGER,size INTEGER,created INTEGER);
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),name TEXT,body TEXT,updated INTEGER);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),kind TEXT,body TEXT,
          status TEXT,progress INTEGER DEFAULT 0,result TEXT,error TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),plan TEXT,amount INTEGER,
          currency TEXT,method TEXT,status TEXT,receipt TEXT,charge_id TEXT UNIQUE,created INTEGER,reviewed INTEGER,
          reviewer INTEGER,expires INTEGER);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,target TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS links(token TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),expires INTEGER);
        CREATE TABLE IF NOT EXISTS bot_state(bot TEXT PRIMARY KEY,offset INTEGER);
        CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY,bot TEXT,method TEXT,body TEXT,attempts INTEGER DEFAULT 0);
        CREATE INDEX IF NOT EXISTS job_user ON jobs(user_id,created);
        ''')
        c.execute("UPDATE jobs SET status='failed',error='server_restarted' WHERE status='running'")

def user(row):
    if not row: raise Error('login_required', 401)
    d = dict(row)
    if d['blocked']: raise Error('account_blocked', 403)
    d.pop('password', None)
    if d['expires'] <= now(): d['plan'] = 'free'
    d['limits'] = PLANS[d['plan']]
    return d

def by_id(user_id):
    with db() as c: return user(c.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone())

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def verify_password(password, stored):
    return bool(stored) and hmac.compare_digest(password_hash(password, stored.split(':')[0]), stored)

def register(username, password):
    import re
    if not re.fullmatch(r'[a-zA-Z0-9_]{3,32}', username): raise Error('invalid_username')
    if not 8 <= len(password) <= 200: raise Error('password_length')
    identifier = uid()
    try:
        with db() as c:
            c.execute('INSERT INTO users(id,username,password,created) VALUES(?,?,?,?)',
                      (identifier, username.lower(), password_hash(password), now()))
    except sqlite3.IntegrityError: raise Error('username_taken', 409)
    return by_id(identifier)

def session_create(user_id, source='web'):
    token = secrets.token_urlsafe(40)
    with db() as c:
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',
                  (hashlib.sha256(token.encode()).hexdigest(), user_id, now()+7*86400, source))
    return token

def session_user(token):
    with db() as c:
        row = c.execute('SELECT u.*,s.source FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?',
            (hashlib.sha256(token.encode()).hexdigest(), now())).fetchone()
    return user(row)

def telegram_verify(data, token):
    from urllib.parse import parse_qsl
    fields = dict(parse_qsl(data, keep_blank_values=True))
    check = fields.pop('hash', '')
    key = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    digest = hmac.new(key, '\n'.join(f'{k}={v}' for k,v in sorted(fields.items())).encode(), hashlib.sha256).hexdigest()
    if not check or not hmac.compare_digest(check, digest): raise Error('invalid_telegram_auth', 401)
    stamp = int(fields.get('auth_date', 0))
    if not now()-3600 <= stamp <= now()+30: raise Error('telegram_auth_expired', 401)
    return json.loads(fields['user'])

def telegram_user(tg):
    with db() as c:
        row = c.execute('SELECT * FROM users WHERE telegram_id=?', (tg['id'],)).fetchone()
        if not row:
            c.execute('INSERT INTO users(id,username,telegram_id,created) VALUES(?,?,?,?)',
                      (uid(), 'tg_'+str(tg['id']), tg['id'], now()))
            row = c.execute('SELECT * FROM users WHERE telegram_id=?', (tg['id'],)).fetchone()
    return user(row)

def add_calendar_month(timestamp):
    date = datetime.fromtimestamp(timestamp, timezone.utc)
    month, year = (1, date.year+1) if date.month == 12 else (date.month+1, date.year)
    return int(date.replace(year=year, month=month, day=min(date.day, calendar.monthrange(year,month)[1])).timestamp())

def review_order(order_id, actor, approve):
    if int(actor) not in admins(): raise Error('admin_only', 403)
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        order = c.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
        if not order: raise Error('not_found', 404)
        if order['status'] not in ('review', 'paid_review'): raise Error('already_reviewed', 409)
        reviewed = now()
        expiry = add_calendar_month(reviewed) if approve else None
        c.execute('UPDATE orders SET status=?,reviewed=?,reviewer=?,expires=? WHERE id=?',
                  ('approved' if approve else 'rejected', reviewed, actor, expiry, order_id))
        if approve:
            c.execute('UPDATE users SET plan=?,expires=? WHERE id=?', (order['plan'], expiry, order['user_id']))
        c.execute('INSERT INTO audit(actor,action,target,created) VALUES(?,?,?,?)',
                  (str(actor), 'order_approved' if approve else 'order_rejected', order_id, reviewed))
        tg = c.execute('SELECT telegram_id FROM users WHERE id=?', (order['user_id'],)).fetchone()[0]
        if tg:
            text = f"FUMIST Studio: {order['plan'].upper()} " + ('? '+datetime.fromtimestamp(expiry,timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if approve else '?')
            c.execute('INSERT INTO outbox(bot,method,body) VALUES(?,?,?)', ('user','sendMessage',json.dumps({'chat_id':tg,'text':text})))
    return {'status': 'approved' if approve else 'rejected', 'expires': expiry}

def price(plan, currency):
    if plan not in ('plus','pro'): raise Error('invalid_plan')
    return int(setting(f'{plan.upper()}_PRICE_{currency}', '15000' if plan=='plus' and currency=='UZS' else '40000' if currency=='UZS' else '0'))

def create_order(u, plan, method):
    if not enabled('BILLING_ENABLED'): raise Error('billing_not_configured', 503)
    currency = 'UZS' if method=='card' else 'STARS'
    amount = price(plan, currency)
    if amount <= 0: raise Error('billing_not_configured', 503)
    if method=='card' and (not setting('CARD_NUMBER') or not setting('CARD_HOLDER') or not admins() or not setting('ADMIN_BOT_TOKEN')):
        raise Error('billing_not_configured', 503)
    identifier = uid()
    with db() as c:
        if c.execute("SELECT 1 FROM orders WHERE user_id=? AND status IN ('awaiting','review','paid_review') AND created>?",(u['id'],now()-86400)).fetchone():
            raise Error('pending_order_exists',409)
        c.execute('INSERT INTO orders(id,user_id,plan,amount,currency,method,status,created) VALUES(?,?,?,?,?,?,?,?)',
                  (identifier,u['id'],plan,amount,'UZS' if method=='card' else 'XTR',method,'awaiting',now()))
    return identifier

