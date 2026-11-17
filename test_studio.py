import hashlib
import hmac
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parent))
import core
import engine
import bots
import server

class MemorySocket:
    def __init__(self,request): self.reader=io.BytesIO(request); self.writer=io.BytesIO()
    def makefile(self,mode,*args): return self.reader if 'r' in mode else self.writer
    def sendall(self,bytes): self.writer.write(bytes)
    def settimeout(self,*args): pass

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.old_data=core.DATA;core.DATA=Path(self.tmp.name)
        self.env=patch.dict(os.environ,{'ADMIN_IDS':'12345','BILLING_ENABLED':'true','CARD_NUMBER':'0000000000000000','CARD_HOLDER':'TEST HOLDER','ADMIN_BOT_TOKEN':'test','PLUS_PRICE_STARS':'100','PRO_PRICE_STARS':'200'})
        self.env.start();core.init();self.u=core.register('test_user','secure-test-password');self.other=core.register('other_user','another-password')
        self.token=core.session_create(self.u['id']); self.other_token=core.session_create(self.other['id'])
    def tearDown(self): core.DATA=self.old_data;self.env.stop();self.tmp.cleanup()
    def request(self,path,method='GET',data=None,token=None,raw=None,headers=None):
        body=raw if raw is not None else json.dumps(data).encode() if data is not None else b''
        h={'Host':'localhost','Connection':'close','X-Fumist':'1','Content-Type':'application/json','Content-Length':str(len(body))}
        if token:h['Cookie']='fumist_session='+token
        h.update(headers or {})
        request=f'{method} {path} HTTP/1.1\r\n'+''.join(f'{k}: {v}\r\n' for k,v in h.items())+'\r\n'
        sock=MemorySocket(request.encode()+body)
        server.Handler(sock,('127.0.0.1',10000),None)
        response=sock.writer.getvalue();head,body=response.split(b'\r\n\r\n',1)
        status=int(head.split(b' ')[1]);
        try: content=json.loads(body)
        except ValueError: content=body
        return status,content,head
    def image(self,owner=None):
        identifier=core.uid()
        with core.db() as c:c.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?,?,?)',(identifier,owner or self.u['id'],'test.png','image','media/test.png',0,640,360,0,123,core.now()))
        return identifier
    def project(self,media=None):
        return {'ratio':'16:9','resolution':720,'fps':30,'clips':[{'media':media or self.image(),'in':0,'out':3,'speed':1}],'texts':[],'audio':[],'subtitles':[]}
    def test_password_hash_and_sessions(self):
        with core.db() as c:stored=c.execute('SELECT password FROM users WHERE id=?',(self.u['id'],)).fetchone()[0]
        self.assertNotIn('secure-test-password',stored)
        self.assertTrue(core.verify_password('secure-test-password',stored));self.assertFalse(core.verify_password('wrong',stored))
        self.assertEqual(core.session_user(self.token)['id'],self.u['id'])
        with self.assertRaises(core.Error):core.session_user('forged')
    def test_http_register_login_and_logout_flow(self):
        status,body,head=self.request('/api/auth/register','POST',{'username':'new_creator','password':'strong-password-2026'})
        self.assertEqual(status,200);self.assertEqual(body['user']['username'],'new_creator')
        cookie=head.split(b'Set-Cookie: fumist_session=',1)[1].split(b';',1)[0].decode()
        self.assertEqual(self.request('/api/me',token=cookie)[1]['user']['username'],'new_creator')
        self.assertEqual(self.request('/api/auth/register','POST',{'username':'new_creator','password':'another-password'})[0],409)
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'new_creator','password':'wrong-password'})[0],401)
        status,body,head=self.request('/api/auth/login','POST',{'username':'NEW_CREATOR','password':'strong-password-2026'})
        self.assertEqual(status,200);self.assertEqual(body['user']['username'],'new_creator')
        login_cookie=head.split(b'Set-Cookie: fumist_session=',1)[1].split(b';',1)[0].decode()
        self.assertEqual(self.request('/api/logout','POST',{},login_cookie)[0],200)
        self.assertEqual(self.request('/api/me',token=login_cookie)[0],401)
    def test_calendar_month_and_month_end(self):
        for start,end in [('2026-11-17T15:15:30','2026-12-17T15:15:30'),('2027-01-31T15:15:30','2027-02-28T15:15:30'),('2028-01-31T15:15:30','2028-02-29T15:15:30'),('2026-12-31T15:15:30','2027-01-31T15:15:30')]:
            a=int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp());b=int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp())
            self.assertEqual(core.add_calendar_month(a),b)
    def order(self,status='review',method='card'):
        identifier=core.create_order(self.u,'plus',method)
        with core.db() as c:c.execute('UPDATE orders SET status=? WHERE id=?',(status,identifier))
        return identifier
    def test_manual_approval_is_only_activation(self):
        order=self.order();self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
        with self.assertRaises(core.Error) as caught:core.review_order(order,9999,True)
        self.assertEqual(caught.exception.status,403)
        self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
        stamp=core.now()
        with patch('core.now',return_value=stamp):result=core.review_order(order,12345,True)
        self.assertEqual(result['expires'],core.add_calendar_month(stamp))
        self.assertEqual(core.by_id(self.u['id'])['plan'],'plus')
        with self.assertRaises(core.Error):core.review_order(order,12345,True)
        self.assertEqual(core.by_id(self.u['id'])['expires'],result['expires'])
        with patch('core.now',return_value=result['expires']):self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
    def test_rejection_and_unpaid_orders_never_grant(self):
        order=self.order('awaiting')
        with self.assertRaises(core.Error):core.review_order(order,12345,True)
        with core.db() as c:c.execute("UPDATE orders SET status='review' WHERE id=?",(order,))
        core.review_order(order,12345,False);self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
    def test_concurrent_approval_has_one_winner(self):
        order=self.order();results=[]
        def approve():
            try:core.review_order(order,12345,True);results.append(True)
            except core.Error:results.append(False)
        threads=[threading.Thread(target=approve) for _ in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertEqual(sorted(results),[False,True])
        with core.db() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM audit').fetchone()[0],1)
    def test_entitlements_and_media_ownership(self):
        project=self.project();self.assertEqual(engine.validate(project,self.u)['duration'],3)
        with self.assertRaises(core.Error):engine.validate(project,self.other)
        project['resolution']=1080
        with self.assertRaises(core.Error):engine.validate(project,self.u)
        project['resolution']=720;project['clips'][0]['out']=120;project['clips']*=2
        with self.assertRaises(core.Error):engine.validate(project,self.u)
    def test_invalid_numeric_and_filter_injection(self):
        project=self.project();project['clips'][0]['speed']=float('nan')
        with self.assertRaises(core.Error):engine.validate(project,self.u)
        project['clips'][0]['speed']=1;project['clips'][0]['filter']='movie=/etc/passwd'
        with self.assertRaises(core.Error):engine.validate(project,self.u)
        project['clips'][0]['filter']='none';project['texts']=[{'text':'test','start':0,'end':2,'color':"white:fontfile=/etc/passwd"}]
        with self.assertRaises(core.Error):engine.validate(project,self.u)
    def test_http_login_csrf_and_preferences(self):
        self.assertEqual(self.request('/api/me')[0],401)
        self.assertEqual(self.request('/api/me',token=self.token)[1]['user']['username'],'test_user')
        self.assertEqual(self.request('/api/preferences','POST',{'language':'ru','theme':'light'},self.token)[0],200)
        self.assertEqual(core.by_id(self.u['id'])['language'],'ru')
        self.assertEqual(self.request('/api/preferences','POST',{'language':'en','theme':'dark'},self.token,headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/api/preferences','POST',{'language':'bad','theme':'light'},self.token)[0],400)
    def test_http_orders_receipts_and_isolation(self):
        self.assertEqual(self.request('/api/orders','POST',{'plan':'plus','method':'card','terms':True},self.token)[0],200)
        order=self.request('/api/orders',token=self.token)[1]['orders'][0]
        self.assertEqual(order['amount'],15000);self.assertEqual(order['status'],'awaiting')
        self.assertEqual(self.request('/api/orders/'+order['id'],token=self.other_token)[0],404)
        status,body,_=self.request('/api/receipt/'+order['id'],'POST',token=self.token,raw=b'%PDF-1.5\n test receipt',headers={'X-Filename':'receipt.pdf'})
        self.assertEqual((status,body['status']),(200,'review'))
        self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
        core.review_order(order['id'],12345,True)
        self.assertEqual(self.request('/api/me',token=self.token)[1]['user']['plan'],'plus')
    def test_telegram_card_checkout_is_rejected(self):
        token=core.session_create(self.u['id'],'telegram')
        self.assertEqual(self.request('/api/orders','POST',{'plan':'plus','method':'card','terms':True},token)[0],403)
    def test_stars_payment_also_requires_admin(self):
        tg=core.telegram_user({'id':9876});identifier=core.create_order(tg,'plus','stars')
        update={'message':{'chat':{'id':9876,'type':'private'},'from':{'id':9876},'successful_payment':{'invoice_payload':identifier,'currency':'XTR','total_amount':100,'telegram_payment_charge_id':'charge-unique'}}}
        with patch('bots.send'):
            bots.handle_user(update);bots.handle_user(update)
        self.assertEqual(core.by_id(tg['id'])['plan'],'free')
        with core.db() as c:self.assertEqual(c.execute('SELECT status FROM orders WHERE id=?',(identifier,)).fetchone()[0],'paid_review')
        core.review_order(identifier,12345,True);self.assertEqual(core.by_id(tg['id'])['plan'],'plus')
    def test_telegram_signature_and_expiry(self):
        token='test-token';fields={'auth_date':str(core.now()),'query_id':'query','user':json.dumps({'id':123})}
        key=hmac.new(b'WebAppData',token.encode(),hashlib.sha256).digest()
        fields['hash']=hmac.new(key,'\n'.join(f'{k}={v}' for k,v in sorted(fields.items())).encode(),hashlib.sha256).hexdigest()
        self.assertEqual(core.telegram_verify(urlencode(fields),token)['id'],123)
        fields['user']=json.dumps({'id':999})
        with self.assertRaises(core.Error):core.telegram_verify(urlencode(fields),token)
    def test_upload_probe_and_file_authorization(self):
        fake={'kind':'image','seconds':0,'width':640,'height':360,'has_audio':0}
        with patch('engine.probe',return_value=fake):
            response=self.request('/api/media','POST',token=self.token,raw=b'fake-test-image',headers={'X-Filename':'test.png'})
        self.assertEqual(response[0],201);media=response[1]
        self.assertEqual(self.request(media['url'],token=self.other_token)[0],404)
        self.assertEqual(self.request(media['url'],token=self.token)[1],b'fake-test-image')
    def test_no_admin_review_http_endpoint(self):
        order=self.order()
        status,_,_=self.request('/api/admin/approve','POST',{'id':order,'admin':12345},self.token)
        self.assertEqual(status,404);self.assertEqual(core.by_id(self.u['id'])['plan'],'free')
    def test_original_and_project_isolation(self):
        identifier=core.uid()
        self.assertEqual(self.request('/api/projects','POST',{'id':identifier,'name':'my edit','project':{}},self.token)[0],200)
        self.assertEqual(self.request('/api/projects','POST',{'id':identifier,'name':'stolen','project':{}},self.other_token)[0],404)
        self.assertEqual(self.request('/api/projects',token=self.other_token)[1]['projects'],[])

if __name__=='__main__':unittest.main()

