"""Two isolated Telegram identities. Only configured admin IDs may review an order."""
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
import core

COPY={
 'uz':{'welcome':'FUMIST Studio — videolaringiz uchun ijodiy makon. 🎬','open':'🎬 Montajni ochish','plans':'💎 Tariflar','lang':'🌐 Til','theme':'◐ Mavzu','support':'Yordam: @','review':'To‘lov tasdiq kutilmoqda. Obuna faqat admin tasdiqlagach boshlanadi.','terms':'Obuna admin tasdiqlagan vaqtdan 1 kalendar oy ishlaydi. To‘lovdan oldin tarif va limitlarni tekshiring.','choose':'Tanlang:','linked':'✅ Saytdagi akkaunt Telegramga ulandi.','conflict':'Bu Telegram akkaunt allaqachon ishlatilgan. Yordamga murojaat qiling.','pending':'Tasdiq kutilmoqda','empty':'Hozircha yo‘q.','approve':'✅ Tasdiqlash','reject':'❌ Rad etish'},
 'ru':{'welcome':'FUMIST Studio — пространство для ваших видео. 🎬','open':'🎬 Открыть редактор','plans':'💎 Тарифы','lang':'🌐 Язык','theme':'◐ Тема','support':'Поддержка: @','review':'Платёж ожидает проверки. Подписка начнётся только после одобрения администратора.','terms':'Подписка действует 1 календарный месяц с момента одобрения администратором. Проверьте тариф и лимиты до оплаты.','choose':'Выберите:','linked':'✅ Аккаунт сайта связан с Telegram.','conflict':'Этот Telegram уже используется. Обратитесь в поддержку.','pending':'Ожидает проверки','empty':'Пока пусто.','approve':'✅ Подтвердить','reject':'❌ Отклонить'},
 'en':{'welcome':'FUMIST Studio — a creative space for your videos. 🎬','open':'🎬 Open editor','plans':'💎 Plans','lang':'🌐 Language','theme':'◐ Theme','support':'Support: @','review':'Payment awaiting review. Your subscription starts only after administrator approval.','terms':'Subscriptions last 1 calendar month from administrator approval. Review the plan and limits before paying.','choose':'Choose:','linked':'✅ Website account linked to Telegram.','conflict':'This Telegram account is already in use. Contact support.','pending':'Awaiting review','empty':'Nothing here yet.','approve':'✅ Approve','reject':'❌ Reject'}
}

def token(bot): return core.setting('ADMIN_BOT_TOKEN' if bot=='admin' else 'BOT_TOKEN')

def api(bot,method,body):
    if not token(bot): raise core.Error('bot_not_configured',503)
    request=urllib.request.Request('https://api.telegram.org/bot'+token(bot)+'/'+method,
        data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=40) as response: result=json.load(response)
    if not result.get('ok'): raise core.Error('telegram_error',502)
    return result.get('result')

def send(bot,chat,text,keyboard=None):
    body={'chat_id':chat,'text':text}
    if keyboard: body['reply_markup']={'inline_keyboard':keyboard}
    return api(bot,'sendMessage',body)

def queue(bot,method,body):
    with core.db() as c: c.execute('INSERT INTO outbox(bot,method,body) VALUES(?,?,?)',(bot,method,json.dumps(body)))

def notice_order(identifier):
    with core.db() as c:
        order=dict(c.execute('SELECT * FROM orders WHERE id=?',(identifier,)).fetchone())
        u=core.by_id(order['user_id'])
    for admin in core.admins():
        queue('admin','sendMessage',{'chat_id':admin,'text':f"FUMIST • {order['id']}\n@{u['username']} • {u['id']}\n{order['plan'].upper()} • {order['amount']} {order['currency']}\n{order['method']} • {order['status']}",
            'reply_markup':{'inline_keyboard':[[{'text':'✅ Tasdiqlash','callback_data':'approve:'+identifier},{'text':'❌ Rad etish','callback_data':'reject:'+identifier}]]}})
        if order['receipt']:
            queue('admin','receipt',{'chat_id':admin,'order_id':identifier})

def send_receipt(chat,identifier):
    with core.db() as c: row=c.execute('SELECT receipt FROM orders WHERE id=?',(identifier,)).fetchone()
    if not row or not row['receipt']: return
    path=core.DATA/row['receipt']
    if not path.is_file(): return
    boundary='Fumist'+core.uid()
    data=(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat}\r\n--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="receipt{path.suffix}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
    req=urllib.request.Request('https://api.telegram.org/bot'+token('admin')+'/sendDocument',data=data,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req,timeout=40) as response: result=json.load(response)
    if not result.get('ok'): raise core.Error('telegram_error')

def menu(u):
    copy=COPY[u['language']]
    projects, exports, support = {
        'uz': ('Loyihalarim', 'Eksportlarim', 'Yordam'),
        'ru': ('Мои проекты', 'Мои экспорты', 'Поддержка'),
        'en': ('My projects', 'My exports', 'Support')
    }[u['language']]
    website=core.setting('PUBLIC_URL').rstrip('/')+'/'
    website_label={'uz':'🌐 Saytni ochish','ru':'🌐 Открыть сайт','en':'🌐 Open website'}[u['language']]
    url=website+'?lang='+u['language']+'&theme='+u['theme']
    support_name = core.setting('SUPPORT_USERNAME','ferapmg').strip().lstrip('@')
    owner_row = [[{'text':'⚙️ Admin','web_app':{'url':url+'&view=admin'}}]] if u.get('telegram_id')==core.owner_id() else []
    return owner_row + [[{'text':copy['open'],'web_app':{'url':url+'&view=editor'}}],
            [{'text':projects,'web_app':{'url':url+'&view=projects'}},
             {'text':exports,'web_app':{'url':url+'&view=exports'}}],
            [{'text':copy['plans'],'web_app':{'url':url+'&view=plans'}},
             {'text':support,'url':'https://t.me/'+support_name}],
            [{'text':website_label,'url':website}],
            [{'text':copy['lang'],'callback_data':'language'},{'text':copy['theme'],'callback_data':'theme'}]]

def configure_menu(u,chat):
    if not core.setting('PUBLIC_URL').startswith('https://'): return
    api('user','setChatMenuButton',{'chat_id':chat,'menu_button':{'type':'web_app',
        'text':COPY[u['language']]['open'],'web_app':{'url':core.setting('PUBLIC_URL').rstrip('/')+'/?view=editor'}}})

def handle_user(update):
    callback=update.get('callback_query')
    if callback:
        u=core.telegram_user(callback['from']); data=callback['data']; chat=callback['message']['chat']['id']
        if data=='language': send('user',chat,'🌐',[[{'text':'O‘zbekcha','callback_data':'lang:uz'},{'text':'Русский','callback_data':'lang:ru'},{'text':'English','callback_data':'lang:en'}]])
        elif data=='theme':
            labels={'uz':['Qorong‘i','Yorug‘','Tizimga mos'],'ru':['Тёмная','Светлая','Системная'],'en':['Dark','Light','System']}[u['language']]
            send('user',chat,'◐',[[{'text':label,'callback_data':'theme:'+value} for label,value in zip(labels,['dark','light','system'])]])
        elif data.startswith(('lang:','theme:')):
            field,value=data.split(':')
            if (field=='lang' and value in COPY) or (field=='theme' and value in ('dark','light','system')):
                column='language' if field=='lang' else 'theme'
                with core.db() as c: c.execute(f'UPDATE users SET {column}=? WHERE id=?',(value,u['id']))
                u=core.by_id(u['id']); send('user',chat,COPY[u['language']]['welcome'],menu(u));configure_menu(u,chat)
        api('user','answerCallbackQuery',{'callback_query_id':callback['id']})
        return
    pre=update.get('pre_checkout_query')
    if pre:
        with core.db() as c:
            row=c.execute("SELECT o.* FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=? AND u.telegram_id=? AND o.status='awaiting' AND o.method='stars'",
                          (pre['invoice_payload'],pre['from']['id'])).fetchone()
        ok=bool(row and row['amount']==pre['total_amount'] and pre['currency']=='XTR' and core.enabled('BILLING_ENABLED') and row['created']>core.now()-86400)
        api('user','answerPreCheckoutQuery',{'pre_checkout_query_id':pre['id'],'ok':ok,**({} if ok else {'error_message':'Order expired / Buyurtma eskirgan'})})
        return
    message=update.get('message',{})
    if not message or message.get('chat',{}).get('type')!='private': return
    tg=message.get('from',{}); chat=message['chat']['id']
    if not tg.get('id'): return
    payment=message.get('successful_payment')
    if payment:
        with core.db() as c:
            c.execute('BEGIN IMMEDIATE')
            order=c.execute('SELECT * FROM orders WHERE id=?',(payment['invoice_payload'],)).fetchone()
            owner=c.execute('SELECT telegram_id FROM users WHERE id=?',(order['user_id'],)).fetchone() if order else None
            if not (order and owner and owner[0]==tg['id'] and order['status']=='awaiting' and order['method']=='stars' and order['amount']==payment['total_amount'] and payment['currency']=='XTR'): return
            c.execute("UPDATE orders SET status='paid_review',charge_id=? WHERE id=?",(payment['telegram_payment_charge_id'],order['id']))
        notice_order(order['id'])
        send('user',chat,COPY[core.telegram_user(tg)['language']]['review'])
        return
    text=message.get('text','')
    if text.strip()=='/id':
        send('user',chat,'Telegram ID: '+str(tg['id']))
        return
    if text.strip() in ('/login','/start login'):
        u=core.telegram_user(tg)
        hint={'uz':'Saytga kirish kodi. 5 daqiqa amal qiladi. Uni faqat FUMIST saytiga kiriting.',
              'ru':'Код входа на сайт действует 5 минут. Введите его только на сайте FUMIST.',
              'en':'Website sign-in code. Valid for 5 minutes. Enter only on the FUMIST website.'}
        send('user',chat,hint[u['language']]+'\n\n'+core.issue_login_code(u))
        return
    if text.startswith('/start link_'):
        link=text.split('link_',1)[1].strip()
        with core.db() as c:
            c.execute('BEGIN IMMEDIATE')
            record=c.execute('SELECT * FROM links WHERE token=? AND expires>?',(link,core.now())).fetchone()
            existing=c.execute('SELECT id FROM users WHERE telegram_id=?',(tg['id'],)).fetchone()
            if record and not existing:
                c.execute('UPDATE users SET telegram_id=? WHERE id=? AND telegram_id IS NULL',(tg['id'],record['user_id']))
                c.execute('DELETE FROM links WHERE token=?',(link,))
                linked=True
            else: linked=False
        send('user',chat,COPY['uz']['linked' if linked else 'conflict'])
        return
    u=core.telegram_user(tg); copy=COPY[u['language']]
    if text.startswith(('/support','/paysupport')): send('user',chat,copy['support']+core.setting('SUPPORT_USERNAME','ferapmg'))
    elif text.startswith('/terms'): send('user',chat,copy['terms'])
    else:
        send('user',chat,copy['welcome']+'\n\n'+u['plan'].upper()+('\n'+datetime.fromtimestamp(u['expires'],timezone.utc).isoformat() if u['expires'] else ''),menu(u))
        configure_menu(u,chat)

def handle_admin(update):
    callback=update.get('callback_query'); message=update.get('message',{})
    actor=(callback or message).get('from',{}).get('id')
    if message.get('text','').strip()=='/id' and actor:
        send('admin',message['chat']['id'],'Telegram ID: '+str(actor))
        return
    if actor not in core.admins(): return
    if callback:
        data=callback.get('data','')
        try:
            action,identifier=data.split(':',1)
            if action not in ('approve','reject'): return
            result=core.review_order(identifier,actor,action=='approve')
            api('admin','answerCallbackQuery',{'callback_query_id':callback['id'],'text':result['status'],'show_alert':True})
            api('admin','editMessageReplyMarkup',{'chat_id':callback['message']['chat']['id'],'message_id':callback['message']['message_id'],'reply_markup':{'inline_keyboard':[]}})
        except core.Error as exc:
            api('admin','answerCallbackQuery',{'callback_query_id':callback['id'],'text':exc.code,'show_alert':True})
        return
    chat=message.get('chat',{}).get('id'); text=message.get('text','')
    with core.db() as c:
        if text.startswith('/pending'):
            rows=c.execute("SELECT id FROM orders WHERE status IN ('review','paid_review') ORDER BY created LIMIT 20").fetchall()
            if not rows: send('admin',chat,'Pending: 0')
            for row in rows: notice_order(row['id'])
        elif text.startswith('/stats'):
            users=c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            active=c.execute("SELECT COUNT(*) FROM users WHERE expires>?",(core.now(),)).fetchone()[0]
            jobs=c.execute("SELECT status,COUNT(*) n FROM jobs GROUP BY status").fetchall()
            pending=c.execute("SELECT COUNT(*) FROM orders WHERE status IN ('review','paid_review')").fetchone()[0]
            send('admin',chat,f'FUMIST Studio\nUsers: {users}\nActive: {active}\nPending: {pending}\nJobs: '+', '.join(f'{r["status"]}={r["n"]}' for r in jobs))
        elif text.startswith('/refund '):
            identifier=text.split(maxsplit=1)[1]
            order=c.execute("SELECT o.*,u.telegram_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=? AND o.method='stars'",(identifier,)).fetchone()
            if not order or not order['charge_id'] or order['status']=='refunded': send('admin',chat,'Order not refundable'); return
            api('user','refundStarPayment',{'user_id':order['telegram_id'],'telegram_payment_charge_id':order['charge_id']})
            c.execute("UPDATE orders SET status='refunded' WHERE id=?",(identifier,))
            # Only revoke this order's entitlement, never a later independently approved purchase.
            c.execute("UPDATE users SET plan='free',expires=0 WHERE id=? AND expires=?",(order['user_id'],order['expires']))
            c.execute('INSERT INTO audit(actor,action,target,created) VALUES(?,?,?,?)',(str(actor),'refund',identifier,core.now()))
            send('admin',chat,'✅ Refunded')
        elif text.startswith(('/block ','/unblock ')):
            parts=text.split()
            if len(parts)!=2: return
            c.execute('UPDATE users SET blocked=? WHERE id=?',(int(parts[0]=='/block'),parts[1]))
            c.execute('INSERT INTO audit(actor,action,target,created) VALUES(?,?,?,?)',(str(actor),parts[0],parts[1],core.now()))
            send('admin',chat,'✅')
        elif text in ('/start','/admin') and actor==core.owner_id():
            username=core.setting('BOT_USERNAME').strip().lstrip('@')
            send('admin',chat,'FUMIST Admin\n/stats · /pending · /refund',[[{'text':'⚙️ Admin kabinet','url':'https://t.me/'+username+'?start=admin'}]])
        else: send('admin',chat,'FUMIST Admin\n/stats — statistika\n/pending — cheklar\n/block USER_ID\n/unblock USER_ID\n/refund ORDER_ID — Stars qaytarish\n\nFaqat ADMIN_IDS dagi akkauntlar tasdiqlaydi. Obuna tasdiqlangan vaqtdan 1 kalendar oy ishlaydi.')

def poll(bot):
    with core.db() as c:
        row=c.execute('SELECT offset FROM bot_state WHERE bot=?',(bot,)).fetchone()
        offset=row[0] if row else 0
    while True:
        try:
            updates=api(bot,'getUpdates',{'offset':offset,'timeout':25,'allowed_updates':['message','callback_query','pre_checkout_query']})
            for update in updates:
                try: (handle_admin if bot=='admin' else handle_user)(update)
                except Exception as exc: print('Bot update failed',bot,type(exc).__name__)
                offset=update['update_id']+1
                with core.db() as c: c.execute('INSERT OR REPLACE INTO bot_state VALUES(?,?)',(bot,offset))
        except Exception as exc:
            print('Bot polling unavailable',bot,type(exc).__name__)
            time.sleep(5)

def delivery():
    while True:
        time.sleep(2)
        with core.db() as c: rows=c.execute('SELECT * FROM outbox WHERE attempts<5 ORDER BY id LIMIT 10').fetchall()
        for row in rows:
            if not token(row['bot']): continue
            try:
                body=json.loads(row['body'])
                if row['method']=='receipt': send_receipt(body['chat_id'],body['order_id'])
                else: api(row['bot'],row['method'],body)
                with core.db() as c: c.execute('DELETE FROM outbox WHERE id=?',(row['id'],))
            except Exception:
                with core.db() as c: c.execute('UPDATE outbox SET attempts=attempts+1 WHERE id=?',(row['id'],))

def start():
    for bot in ('user','admin'):
        if token(bot): threading.Thread(target=poll,args=(bot,),daemon=True).start()
    threading.Thread(target=delivery,daemon=True).start()
