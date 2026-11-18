import {t,errorText,languages} from './i18n.js?v=1.3.2';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths={home:'M3 10 12 3l9 7v10H3z M9 20v-7h6v7',film:'M4 3h16v18H4z M4 8h16M4 16h16M8 3v18M16 3v18',folder:'M3 7h7l2-3h9v16H3z',grid:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',spark:'m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z M20 2v4M18 4h4',download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',crown:'m3 6 4 5 5-7 5 7 4-5-2 14H5z',settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M4 4l3 1 2-2h6l2 2 3-1 1 5-2 3 2 3-1 5-3-1-2 2H9l-2-2-3 1-1-5 2-3-2-3z',arrow:'M5 12h14m-6-6 6 6-6 6',plus:'M12 4v16M4 12h16',upload:'M12 16V3m-5 5 5-5 5 5M3 16v5h18v-5',play:'m8 4 12 8-12 8z',pause:'M7 4v16M17 4v16',back:'M7 5v14m11-14-9 7 9 7z',next:'M17 5v14M6 5l9 7-9 7z',scissors:'m7 7 13 13M7 17 20 4M7 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6M7 13a3 3 0 1 0 0 6 3 3 0 0 0 0-6',music:'M9 18V5l11-2v13M4 16h5v5H4zM15 14h5v5h-5z',text:'M4 5h16M12 5v15M8 20h8',caption:'M3 5h18v14H3zM6 10h4M6 14h5M14 10h4M14 14h4',sliders:'M4 3v18M12 3v18M20 3v18M1 8h6M9 16h6M17 10h6',resize:'M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6',undo:'M8 4 3 9l5 5M3 9h11a6 6 0 0 1 0 12',redo:'m16 4 5 5-5 5M21 9H10a6 6 0 0 0 0 12',copy:'M8 8h13v13H8zM16 8V3H3v13h5',trash:'M3 6h18M9 6V3h6v3M6 6v15h12V6M10 10v7M14 10v7',left:'m15 4-8 8 8 8',right:'m9 4 8 8-8 8',rotate:'M3 11a9 9 0 1 1 3 8M3 3v8h8',flip:'M12 2v20M9 5 3 19h6zM15 5l6 14h-6z',mic:'M9 3h6v11H9zM5 10v3a7 7 0 0 0 14 0v-3M12 20v3M8 23h8',close:'m5 5 14 14M5 19 19 5',check:'m4 12 5 5L20 6',help:'M9 8a3 3 0 1 1 5 2c-2 1-2 2-2 4M12 18h.01M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20',save:'M4 3h13l4 4v14H3V3zM7 3v6h9V3M7 21v-8h10v8',link:'m10 14 4-4M8 16l-2 2a4 4 0 0 1-5-5l5-5a4 4 0 0 1 5 0M16 8l2-2a4 4 0 0 1 5 5l-5 5a4 4 0 0 1-5 0',external:'M14 3h7v7m0-7L10 14M10 4H3v17h17v-7',clock:'M12 8v5l4 2M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20'};
const icon=name=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name]||paths.film}"/></svg>`;
const btn=(action,label,ico='',cls='',extra='')=>`<button class="btn ${cls}" data-action="${action}" ${extra}>${ico?icon(ico):''}${label}</button>`;
const ib=(action,label,ico)=>`<button class="icon-btn" data-action="${action}" title="${esc(label)}" aria-label="${esc(label)}">${icon(ico)}</button>`;
const time=s=>`${String(Math.floor(Math.max(0,s)/60)).padStart(2,'0')}:${String(Math.floor(Math.max(0,s)%60)).padStart(2,'0')}`;
const date=s=>s?new Date(s*1000).toLocaleString(({uz:'uz-UZ',ru:'ru-RU',en:'en-GB'})[localStorage.getItem('fumist-language')||'uz']):'—';
const clone=o=>structuredClone(o);
const blank=()=>({clips:[],texts:[],subtitles:[],audio:[],ratio:'16:9',resolution:720,fps:30});
let app={view:'home',tab:'media',user:null,config:null,media:[],projects:[],jobs:[],orders:[],project:blank(),projectId:null,name:'',selected:-1,textSelected:-1,audioSelected:-1,cursor:0,playing:false,zoom:45,history:[],future:[],busy:false,uploadPct:null,recording:false,order:null};
let playback=null,raf=0,lastFrame=0,recorder=null,recordParts=[],recordStream=null,recordTimer=null,pollTimer=null,dirty=false,saveTimer=null,previewClip=-1,previewSource='',trackAudio=[];
const STUDIO_VERSION='1.3.2';
const query=new URLSearchParams(location.search);
if(languages.includes(query.get('lang')))localStorage.setItem('fumist-language',query.get('lang'));
if(['dark','light','system'].includes(query.get('theme')))localStorage.setItem('fumist-theme',query.get('theme'));
function setTheme(){const pref=localStorage.getItem('fumist-theme')||'system';document.documentElement.dataset.theme=pref==='system'?(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'):pref;document.documentElement.lang=localStorage.getItem('fumist-language')||'uz';}
setTheme();matchMedia('(prefers-color-scheme:dark)').addEventListener('change',setTheme);
function toast(message){const el=document.createElement('div');el.className='toast';el.textContent=message;$('#toasts').append(el);setTimeout(()=>el.remove(),6000);}
async function api(url,method='GET',data){let result;try{result=await fetch(url,{method,headers:{'X-Fumist':'1',...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});}catch{throw new Error('network_error');}const response=await result.json();if(!result.ok)throw new Error(response.error||'server_error');return response;}
function fail(error){if(error?.message==='login_required')authDialog();else toast(errorText(error?.message));}
function duration(){return app.project.clips.reduce((sum,c)=>sum+(c.out-c.in)/c.speed,0);}
function clipAt(cursor){let before=0;for(let i=0;i<app.project.clips.length;i++){const c=app.project.clips[i],d=(c.out-c.in)/c.speed;if(cursor<before+d-.001||i===app.project.clips.length-1)return{i,clip:c,local:Math.max(0,cursor-before),before};before+=d;}return null;}
function mById(id){return app.media.find(m=>m.id===id);}
function plan(){return app.user?.plan||'free';}
function history(){app.history.push(clone(app.project));if(app.history.length>50)app.history.shift();app.future=[];dirty=true;}
function draft(){localStorage.setItem('fumist-draft-'+(app.user?.id||'guest'),JSON.stringify({project:app.project,id:app.projectId,name:app.name}));dirty=true;clearTimeout(saveTimer);if(app.user)saveTimer=setTimeout(()=>saveProject(true).catch(()=>{}),4000);}
function normalizeTimes(){const d=duration();for(const field of ['texts','subtitles'])app.project[field]=app.project[field].filter(x=>x.start<d).map(x=>({...x,end:Math.min(x.end,d)}));if(d)app.project.audio=app.project.audio.filter(x=>x.offset<d);app.cursor=Math.min(app.cursor,Math.max(0,d-.001));}
function changed(){normalizeTimes();draft();render();}
function newProject(preset=null){pause();app.project=preset||blank();app.projectId=null;app.name=t('untitled');app.selected=-1;app.textSelected=-1;app.audioSelected=-1;app.cursor=0;app.history=[];app.future=[];dirty=false;app.view='editor';render();}
function navigate(view){if(view!==app.view)pause();app.view=view;if(view==='editor'&&!app.name)app.name=t('untitled');render();loadView().catch(fail);}
async function loadView(){if(!app.user)return;if(app.view==='projects'||app.view==='home')app.projects=(await api('/api/projects')).projects;if(app.view==='exports'||app.view==='profile')app.jobs=(await api('/api/jobs')).jobs;if(app.view==='profile')app.projects=(await api('/api/projects')).projects;if(app.view==='plans')app.orders=(await api('/api/orders')).orders;render();}
function themeControls(){return `<select data-setting="language" aria-label="${t('language')}">${[['uz','UZ'],['ru','RU'],['en','EN']].map(([value,label])=>`<option value="${value}" ${value===(localStorage.getItem('fumist-language')||'uz')?'selected':''}>${label}</option>`).join('')}</select><select class="theme-control" data-setting="theme" aria-label="${t('theme')}">${['dark','light','system'].map(v=>`<option value="${v}" ${v===(localStorage.getItem('fumist-theme')||'system')?'selected':''}>${t(v)}</option>`).join('')}</select>`;}
function telegramMode(){return Boolean(window.Telegram?.WebApp?.initData);}
function channelLink(){
 const inBot=telegramMode();
 const bot=(app.config?.bot||'').replace(/^@/,'');
 if(!inBot&&!/^[A-Za-z0-9_]+$/.test(bot))return '';
 const label=t(inBot?'openWebsite':'openBot');
 return `<a class="nav-item" href="${inBot?location.origin+'/':'https://t.me/'+bot}" ${inBot?'data-action="open-site"':''} target="_blank" rel="noopener" title="${label}" aria-label="${label}">${icon('external')}<span class="nav-text">${label}</span></a>`;
}
const tr=(uz,ru,en)=>({uz,ru,en}[localStorage.getItem('fumist-language')]||uz);
let inspectorOpen=window.innerWidth>900;
let ownerTab='orders',ownerSearch='';
async function ownerPanel(search=ownerSearch){
 ownerSearch=search;
 const data=await api('/api/owner/dashboard?search='+encodeURIComponent(search));
 const list=(items,format)=>items.length?items.map(format).join(''):'<p class="dashboard-empty">'+t('dashboardEmpty')+'</p>';
 const stats=[[t('dashboardUsers'),data.totals.users],['Plus / Pro',data.totals.active],[t('projects'),data.totals.projects],[t('review'),data.totals.pending]];
 const tabs=[['orders',t('paymentHistory')],['users',t('dashboardUsers')],['jobs',t('exports')],['audit',t('dashboardActivity')]];
 const entries={
   orders:()=>list(data.orders,o=>`<article class="dashboard-row"><div><strong>${esc(o.username)} · ${esc(o.plan.toUpperCase())}</strong><p>${esc(t(o.status))} · ${o.amount} ${esc(o.currency)}</p></div><div class="row wrap">${o.has_receipt?`<a class="btn tiny" href="/api/owner/receipt/${encodeURIComponent(o.id)}">${t('dashboardReceipt')}</a>`:''}${['paid_review','review'].includes(o.status)?btn('owner-review:approve:'+o.id,tr('Tasdiqlash','Одобрить','Approve'),'','tiny primary')+btn('owner-review:reject:'+o.id,tr('Rad etish','Отклонить','Reject'),'','tiny'):''}</div></article>`),
   users:()=>`<form class="dashboard-search" id="owner-search"><input name="search" aria-label="Login / Telegram ID" placeholder="Login / Telegram ID" value="${esc(search)}"><button class="btn" type="submit">${tr('Qidirish','Искать','Search')}</button></form>`+list(data.users,u=>`<article class="dashboard-row"><div><strong>${esc(u.username)}</strong><p>${u.telegram_id?'Telegram '+esc(u.telegram_id):'—'}</p></div><span class="pill">${esc(u.plan.toUpperCase())}${u.expires?' · '+date(u.expires):''}</span></article>`),
   jobs:()=>list(data.jobs,j=>`<article class="dashboard-row"><div><strong>${esc(j.username)}</strong><p>${esc(j.kind)}</p></div><span class="pill">${esc(t(j.status))} · ${j.progress}%</span></article>`),
   audit:()=>list(data.audit,a=>`<article class="dashboard-row"><div><strong>${esc(a.action)}</strong><p>${date(a.created)}</p></div><span class="muted small">${esc(a.target)}</span></article>`)
 };
 modal(modalHead('FUMIST Admin')+`<div class="dashboard-metrics">${stats.map(([label,value])=>`<div><span>${esc(label)}</span><strong>${value}</strong></div>`).join('')}</div><div class="dashboard-tabs">${tabs.map(([id,label])=>`<button type="button" data-action="owner-tab:${id}" aria-pressed="${ownerTab===id}">${esc(label)}</button>`).join('')}</div><div class="dashboard-list">${entries[ownerTab]()}</div>`);
 $('#modal').classList.add('owner-dashboard');
}

function render(){
 previewObserver?.disconnect();
 const previousInspector=$('.inspector');
 if(previousInspector)inspectorOpen=previousInspector.open;
 const previousScroll=$('.timeline-scroll')?.scrollLeft||0;
 const oldVideo=$('#preview-video');pauseMedia();if(oldVideo)releaseSound(oldVideo);previewClip=-1;previewSource='';
 const editor=app.view==='editor';
 $('#app').innerHTML=`<div class="shell ${editor?'editor-shell':''}"><aside class="sidebar"><button class="logo" data-action="home"><img src="/mark.svg" alt=""><span class="logo-text">FUMIST<small>STUDIO · v${STUDIO_VERSION}</small></span></button><div class="side-label caps">${t('menu')}</div><nav>${[['home','workspace','home'],['projects','projects','folder'],['templates','templates','grid'],['ai','aiTools','spark'],['exports','exports','download'],['plans','plans','crown']].map(([v,key,ico])=>`<button class="nav-item ${app.view===v?'active':''}" data-action="nav:${v}" title="${t(key)}" aria-label="${t(key)}">${icon(ico)}<span class="nav-text">${t(key)}</span>${v==='ai'?'<span class="pill">AI</span>':''}</button>`).join('')}${channelLink()}${app.user?.is_owner?btn('owner-panel','Admin','settings','tiny'):''}</nav><div class="side-bottom"><div class="upgrade">${icon('spark')}<h3>${t('upgradeTitle')}</h3><p>${t('upgradeDesc')}</p>${btn('nav:plans',t('seePlans'),'arrow','tiny')}</div><button class="nav-item" data-action="settings" title="${t('settings')}">${icon('settings')}<span class="nav-text">${t('settings')}</span></button><div class="profile-mini row"><div class="avatar">${esc((app.user?.username||'F')[0].toUpperCase())}</div><div class="spacer"><strong class="small">${esc(app.user?.username||t('guest'))}</strong><div class="muted small">${plan().toUpperCase()}</div></div>${ib('nav:profile',t('account'),'settings')}</div></div></aside><main class="main"><header class="topbar">${editor?`<input class="project-name" id="project-name" aria-label="${t('projects')}" value="${esc(app.name)}"><span class="cloud-status">${dirty?t('savedDraft'):app.projectId?t('saved'):''}</span>`:`<div class="mobile-logo"><img src="/mark.svg" alt="">FUMIST</div><div class="crumb">FUMIST Studio <span> / ${t(({home:'workspace',ai:'aiTools',profile:'account'})[app.view]||app.view)}</span></div>`}<span class="spacer"></span>${themeControls()}${editor?`${ib('save',t('save'),'save')}${btn('export',t('export'),'download','primary')}`:app.user?`<button class="avatar" data-action="nav:profile" aria-label="${t('account')}">${esc(app.user.username[0].toUpperCase())}</button>`:btn('login',t('login'),'','ghost tiny')}</header>${editor?editorView():`<div class="content">${({home:homeView,projects:projectsView,templates:templatesView,plans:plansView,exports:exportsView,ai:aiView,profile:profileView}[app.view]||homeView)()}</div>`}</main></div>`;
 if(editor){$('.timeline-scroll').scrollLeft=previousScroll;bindPreview();paintPreview(true);}if(app.playing){lastFrame=performance.now();cancelAnimationFrame(raf);raf=requestAnimationFrame(tick);}
}
const launchFormats = [
  ['16:9', 'YouTube', 'wide'],
  ['9:16', 'Reels / Shorts', 'portrait'],
  ['1:1', 'Instagram', 'square'],
  ['4:5', 'Feed', 'feed']
];
let launchRatio = '16:9';

function homeView() {
  const format = launchFormats.find(([ratio]) => ratio === launchRatio);
  const choices = launchFormats.map(([ratio, platform]) =>
    `<button type="button" data-action="format:${ratio}" aria-pressed="${ratio === launchRatio}" aria-label="${platform} ${ratio}">${ratio}</button>`
  ).join('');
  return `<section class="launchpad">
    <div class="launch-copy">
      <h1>${t('newProject')}</h1>
      <fieldset class="format-picker"><legend>${t('format')}</legend>${choices}</fieldset>
      <div class="row wrap">${btn('launch', t('startEditing'), 'plus', 'primary')}
      ${app.project.clips.length ? btn('nav:editor', t('resumeDraft'), 'play') : ''}</div>
    </div>
    <div class="format-stage" aria-live="polite">
      <div class="monitor-frame ${format[2]}"><img src="/scene.svg" alt=""><span class="frame-grid"></span></div>
      <div class="monitor-meta"><strong>${format[1]}</strong><span>${format[0]}</span></div>
    </div>
  </section><div class="section-head"><h2>${t('quickTools')}</h2></div><div class="tools-grid">${[['trim','trimTool','trimDesc','scissors'],['captions','captionTool','captionDesc','caption'],['audio','audioTool','audioDesc','music'],['resize','formatTool','formatDesc','resize']].map(([a,h,p,i])=>`<button class="tool-card" data-action="quick:${a}"><div class="tool-icon">${icon(i)}</div><h3>${t(h)}</h3><p>${t(p)}</p></button>`).join('')}</div><div class="section-head"><h2>${t('recent')}</h2>${btn('nav:projects',t('viewAll'),'arrow','tiny ghost')}</div><div class="project-grid"><button class="new-card" data-action="new">${icon('plus')}${t('newProject')}</button>${app.projects.slice(0,2).map(projectCard).join('')}</div><div class="footer-note">FUMIST Studio · @fera_coder · ${t('retention')}</div>`;}
function projectCard(p){let body={};try{body=JSON.parse(p.body);}catch{}const first=mById(body.clips?.[0]?.media);return `<article class="project-card"><button class="project-cover" style="width:100%" data-action="open-project:${p.id}" aria-label="${esc(p.name)}">${first&&first.kind==='image'?`<img src="${first.url}" alt="">`:icon('film')}<span>${esc(body.ratio||'16:9')}</span></button><div class="project-info row"><div class="spacer" style="min-width:0"><h3>${esc(p.name)}</h3><span class="muted small">${date(p.updated)}</span></div>${ib('delete-project:'+p.id,t('remove'),'trash')}</div></article>`;}
function projectsView(){return `<div class="section-head"><h2>${t('projects')}</h2><div class="row">${btn('import-json',t('importProject'),'upload','tiny')}${btn('new',t('newProject'),'plus','primary tiny')}</div></div>${app.projects.length?'<div class="field"><input type="search" id="project-search" aria-label="'+tr('Loyihani qidirish','Поиск проекта','Search projects')+'" placeholder="'+tr('Loyihani nomi bilan qidirish','Найти проект по названию','Search projects by name')+'"></div>':''}${app.projects.length?`<div class="project-grid">${app.projects.map(p=>'<div data-project-name="'+esc(p.name.toLowerCase())+'">'+projectCard(p)+'</div>').join('')}</div>`:`<div class="empty">${icon('folder')}<h3>${t('noProjects')}</h3><p>${t('noProjectsDesc')}</p>${btn('new',t('newProject'),'plus','primary')}</div>`}`;}
const presets=[{key:'travel',title:'WANDER<br>MORE.',sub:'A MOMENT OUTSIDE',ratio:'16:9',filter:'warm',text:'WANDER MORE.',position:'center',size:64},{key:'school',title:'OUR<br>STORY.',sub:'THE DAYS WE REMEMBER',ratio:'16:9',filter:'none',text:'OUR STORY',position:'center',size:64},{key:'minimal',title:'less,<br>but better.',sub:'A DIFFERENT PERSPECTIVE',ratio:'9:16',filter:'mono',text:'less, but better.',position:'bottom',size:50},{key:'birthday',title:'MAKE<br>A WISH.',sub:'YOUR NEXT CHAPTER',ratio:'9:16',filter:'warm',text:'MAKE A WISH',position:'center',size:60},{key:'sport',title:'NEVER<br>SETTLE.',sub:'ONE MORE REP',ratio:'9:16',filter:'vivid',text:'NEVER SETTLE',position:'center',size:64},{key:'portfolio',title:'BUILT<br>BY ME.',sub:'IDEAS INTO REALITY',ratio:'16:9',filter:'cinema',text:'BUILT BY ME',position:'bottom',size:60}];
function templatesView(){return `<div class="page-intro"><div class="eyebrow caps">FUMIST COLLECTION</div><h1>${t('templateIntro')}</h1><p class="muted">${t('templateHelp')}</p></div><div class="template-grid">${presets.map((p,i)=>`<article class="project-card template-card"><div class="templates-cover"><span class="pill">${p.filter==='cinema'?'PLUS':p.ratio}</span><div class="sub">${p.sub}</div><div class="big">${p.title}</div></div><div class="project-info row"><h3 class="spacer" style="margin:0">${t(p.key)}</h3>${btn('template:'+i,t('useTemplate'),'arrow','tiny')}</div></article>`).join('')}</div>`;}
function planPrice(p){
 if(p==='free')return t('freePrice');
 const stars=telegramMode(), price=app.config?.prices?.[p]?.[stars?'stars':'uzs'];
 if(!price)return stars?t('starsUnavailable'):'—';
 return price.toLocaleString()+' <span class="small muted">'+(stars?'⭐ Stars':'so‘m')+'</span>';
}
function plansView(){return `<div class="page-intro"><div class="eyebrow caps">FREE / PLUS / PRO</div><h1>${t('planIntro')}</h1><p class="muted">${t('planHelp')}</p></div>${app.user?.expires>Math.floor(Date.now()/1000)?`<div class="plan-current row between"><strong>${t('currentPlan')}: ${plan().toUpperCase()}</strong><span class="muted">${t('expires')}: ${date(app.user.expires)}</span></div>`:''}<div class="plans-grid">${['free','plus','pro'].map(p=>{const l=app.config?.plans[p]||{height:720,seconds:120,exports:3,clips:10,ai:1};return `<article class="plan-card ${p==='plus'?'featured':''}"><span class="caps ${p==='plus'?'accent':'muted'}">${p==='plus'?t('mostPopular'):'FUMIST '+p.toUpperCase()}</span><h2>${p.toUpperCase()}</h2><p class="muted small">${t(p+'Desc')}</p><div class="plan-price">${planPrice(p)}</div><span class="muted small">${p==='free'?'—':t('month')}</span><ul><li>${l.height}p MP4</li><li>${t('minutes',{n:l.seconds/60})}</li><li>${t('dailyExports',{n:l.exports})}</li><li>${t('clipLimit',{n:l.clips})}</li><li>${t('dailyAi',{n:l.ai})}</li><li>${t(p==='free'?'watermark':'noWatermark')}</li><li>${t(p==='free'?'basicFilters':'allFilters')}</li></ul>${btn(p==='free'?'new':'buy:'+p,plan()===p?t('currentPlan'):p==='free'?t('freeStart'):t('choosePlan'),p==='free'?'plus':'crown',p==='plus'?'primary':'',p!=='free'&&(plan()===p||(telegramMode()&&!app.config?.prices?.[p]?.stars))?'disabled':'')}</article>`;}).join('')}</div><div class="note">${t('approvalNote')}</div>${!app.config?.billing?`<p class="muted small" style="margin-top:15px">${t('billingSetup')}</p>`:''}<div class="section-head"><h2>${t('paymentHistory')}</h2>${btn('refresh',t('refresh'),'rotate','tiny')}</div>${app.orders.length?app.orders.map(o=>`<div class="list-row">${icon('crown')}<div class="spacer"><h3>${o.plan.toUpperCase()} · ${o.amount.toLocaleString()} ${o.currency}</h3><span class="muted small">${date(o.created)} ${o.expires?' · '+t('expires')+': '+date(o.expires):''}</span></div><span class="badge ${o.status}">${t(o.status)}</span>${o.status==='awaiting'?btn('resume-order:'+o.id,t('continue'),'arrow','tiny'):''}${o.status==='awaiting'?ib('cancel-order:'+o.id,t('cancel'),'close'):''}</div>`).join(''):`<div class="empty small">${t('noOrders')}</div>`}<div class="footer-note"><button data-action="terms">${t('terms')}</button> · <button data-action="privacy">${t('privacy')}</button></div>`;}
function exportsView(){return `<div class="section-head"><h2>${t('exports')}</h2>${btn('refresh',t('refresh'),'rotate','tiny')}</div><p class="muted small">${t('retention')}</p>${app.jobs.filter(j=>j.kind==='render').length?app.jobs.filter(j=>j.kind==='render').map(j=>`<div class="list-row">${icon('film')}<div class="spacer"><h3>FUMIST · ${j.id.slice(0,8)}</h3><div class="muted small">${date(j.created)}</div>${['running','queued'].includes(j.status)?`<progress max="100" value="${j.progress}"></progress>`:''}${j.error?`<p class="danger small" style="margin:5px 0 0">${errorText(j.error)}</p>`:''}</div><span class="badge ${j.status}">${t(j.status)} ${j.status==='running'?j.progress+'%':''}</span>${j.status==='done'?`<a class="btn tiny primary" href="/api/download/${j.id}" download>${icon('download')}${t('download')}</a>`:''}</div>`).join(''):`<div class="empty">${icon('download')}<h3>${t('noExports')}</h3><p>${t('noExportsDesc')}</p>${btn('new',t('startEditing'),'plus','primary')}</div>`}`;}
function aiView(){return `<div class="page-intro"><div class="eyebrow caps">FUMIST INTELLIGENCE</div><h1>${t('aiIntro')}</h1><p class="muted">${t('aiHelp')}</p></div><div class="ai-grid">${[['captions','captionTool','autoCaptionHelp','caption'],['silence','silence','silenceHelp','scissors'],['srt','srtTool','srtHelp','text'],['resize','formatTool','formatHelp','resize']].map(([a,h,p,i])=>`<article class="ai-card"><div class="tool-icon">${icon(i)}</div><h3>${t(h)}</h3><p>${t(p)}</p>${a==='captions'&&!app.config?.ai?`<p class="small muted">${t('aiDisabled')}</p>`:''}${btn('quick:'+a,t('open'),'arrow','tiny')}</article>`).join('')}</div>`;}
function editorView(){const c=app.project.clips[app.selected];return `<div class="editor ${c?'has-selected-clip':''}"><section class="library"><div class="library-tabs">${['media','text','audio','subtitles','filters','ai'].map(tab=>`<button class="${app.tab===tab?'active':''}" data-action="tab:${tab}">${tab==='ai'?'AI':t(tab)}</button>`).join('')}</div><div class="library-body">${libraryView()}</div></section><section class="viewer"><div class="viewer-head row"><span>${t('preview')}</span><span class="spacer"></span><span>${app.project.ratio} · ${app.project.resolution}p</span></div><div class="preview-area"><div class="preview-frame" id="preview-frame" style="aspect-ratio:${app.project.ratio.replace(':','/')}"><video id="preview-video" playsinline preload="metadata"></video><img id="preview-image" alt="" hidden><div class="preview-empty" id="preview-empty">${icon('film')}<strong>${t('emptyPreview')}</strong>${t('emptyPreviewDesc')}</div><div id="preview-overlays"></div></div></div><div class="viewer-controls"><span><span id="current-time">${time(app.cursor)}</span> / ${time(duration())}</span><div class="transport">${ib('prev',t('moveLeft'),'back')}<button class="icon-btn play" data-action="play" aria-label="${t('preview')}">${icon(app.playing?'pause':'play')}</button>${ib('next',t('moveRight'),'next')}</div><span class="muted small">${app.project.fps} FPS</span></div></section><details class="inspector" ${inspectorOpen?'open':''}><summary>${t('clipSettings')}</summary>${c?inspectorView(c):`<p class="muted small">${t('selectClip')}</p>`}</details><section class="timeline"><div class="timeline-tools">${ib('undo',t('undo'),'undo')}${ib('redo',t('redo'),'redo')}<span style="height:18px;border-right:1px solid var(--line);margin:0 6px"></span>${ib('split',t('split'),'scissors')}${ib('duplicate',t('duplicate'),'copy')}${ib('remove-clip',t('remove'),'trash')}${ib('move-left',t('moveLeft'),'left')}${ib('move-right',t('moveRight'),'right')}<select id="ratio" aria-label="${t('format')}">${['16:9','9:16','1:1','4:5'].map(r=>`<option ${r===app.project.ratio?'selected':''}>${r}</option>`).join('')}</select><span class="duration">${time(duration())} · ${app.project.clips.length} ${t('videoTrack')}</span><input type="range" id="zoom" aria-label="Zoom" min="10" max="100" value="${app.zoom}" style="width:65px"></div><div class="timeline-scroll"><div id="timeline-inner" style="position:relative;width:${Math.max(550,duration()*app.zoom+100)}px"><div class="ruler" id="ruler">${Array.from({length:Math.ceil(Math.max(duration(),12)/5)+1},(_,i)=>`<span style="left:${i*5*app.zoom}px">${time(i*5)}</span>`).join('')}</div><div class="track"><span class="track-label">${icon('film')}${t('videoTrack')}</span>${app.project.clips.length?app.project.clips.map((clip,i)=>`<button class="clip ${app.selected===i?'selected':''}" draggable="true" data-clip="${i}" data-action="select-clip:${i}" style="width:${Math.max(25,(clip.out-clip.in)/clip.speed*app.zoom-3)}px">${esc(mById(clip.media)?.name||'Media')}<small>${((clip.out-clip.in)/clip.speed).toFixed(1)}s · ${clip.speed}×</small></button>`).join(''):`<div class="timeline-empty">${t('dragHint')}</div>`}</div><div class="track"><span class="track-label">${icon('text')}${t('textTrack')}</span>${app.project.texts.map((text,i)=>`<button class="clip text-clip" data-action="select-text:${i}" style="position:absolute;left:${text.start*app.zoom}px;width:${Math.max(25,(text.end-text.start)*app.zoom)}px;height:36px">${esc(text.text)}</button>`).join('')}${app.project.subtitles.length?`<button class="clip text-clip" data-action="tab:subtitles" style="opacity:.65;left:0;min-width:120px">${t('subtitles')} · ${app.project.subtitles.length}</button>`:''}</div><div class="track"><span class="track-label">${icon('music')}${t('audioTrack')}</span>${app.project.audio.map((audio,i)=>`<button class="clip audio-clip" data-action="select-audio:${i}" style="position:absolute;left:${audio.offset*app.zoom}px;width:${Math.max(30,Math.min(duration()-audio.offset,audio.maxLength||Infinity,audio.loop?Infinity:Math.max(0,(mById(audio.media)?.seconds||0)-audio.in))*app.zoom)}px;height:36px">♫ ${esc(mById(audio.media)?.name||'Audio')}</button>`).join('')}</div><div class="playhead" id="playhead" style="left:${app.cursor*app.zoom}px"></div></div></div></section></div>`;}
function field(key,value,type='number',extra='',target='clip'){return `<div class="field"><label>${t(key)}</label><input type="${type}" data-${target}-field="${key}" value="${esc(value)}" ${extra}></div>`;}
function range(key,value,min,max,step){return `<div class="field"><label>${t(key)} <span>${value}</span></label><input type="range" data-clip-field="${key}" value="${value}" min="${min}" max="${max}" step="${step}"></div>`;}
function inspectorView(c){return `<div class="inspector-grid"><div><div class="field-row">${field('start',c.in,'number',`min="0" max="${c.out-.1}" step=".1"`)}${field('end',c.out,'number',`min="${c.in+.1}" max="${mById(c.media)?.kind==='image'?120:mById(c.media)?.seconds||7200}" step=".1"`)}</div><div class="field"><label>${t('speed')}</label><select data-clip-field="speed">${[.25,.5,.75,1,1.25,1.5,2,3,4].map(v=>`<option value="${v}" ${v===c.speed?'selected':''}>${v}×</option>`).join('')}</select></div>${range('volume',c.volume,0,2,.05)}${mById(c.media)?.has_audio?btn('mute-clip',c.volume?t('muteClip'):t('unmuteClip'),'music','tiny')+btn('extract-audio',t('extractAudio'),'music','tiny'):''}</div><div>${range('brightness',c.brightness,-.5,.5,.01)}${range('contrast',c.contrast,.5,2,.05)}${range('saturation',c.saturation,0,2,.05)}</div><div>${range('fade',c.fade,0,Math.min(2,(c.out-c.in)/c.speed/2),.1)}<div class="field"><label>${t('fit')}</label><select data-clip-field="fit"><option value="contain" ${c.fit==='contain'?'selected':''}>${t('contain')}</option><option value="cover" ${c.fit==='cover'?'selected':''}>${t('cover')}</option></select></div><div class="row">${ib('rotate',t('rotate'),'rotate')}${ib('flip',t('flip'),'flip')}${ib('reset-clip',t('reset'),'rotate')}</div></div><div><div class="field"><label>${t('filters')}</label><select data-clip-field="filter">${['none','warm','cool','mono','vivid','cinema','vintage'].map(v=>`<option value="${v}" ${v===c.filter?'selected':''}>${t(v)} ${['cinema','vintage'].includes(v)?'· PLUS':''}</option>`).join('')}</select></div><p class="editor-footnote">${t('previewHint')}</p></div></div>`;}
function libraryView(){
 if(app.tab==='media')return `${btn('upload',t('import'),'upload','primary tiny','style="width:100%"')}<p class="muted small">${t('uploadHint')}</p>${app.uploadPct!==null?`<div class="upload-progress">${t('uploading')} ${app.uploadPct}%<progress max="100" value="${app.uploadPct}"></progress></div>`:''}<div class="media-grid">${app.media.map(m=>`<div class="media-item"><button class="media-thumb" data-action="add-media:${m.id}" title="${esc(m.name)}">${m.kind==='image'?`<img src="${m.url}" alt="">`:m.kind==='video'?`<video src="${m.url}#t=0.1" muted preload="metadata"></video>`:icon('music')}</button><button class="delete-media" data-action="delete-media:${m.id}" aria-label="${t('remove')}">×</button><div class="media-name">${esc(m.name)}</div></div>`).join('')}</div>${!app.media.length?`<button class="upload-zone" data-action="upload" style="margin-top:15px">${icon('upload')}<span>${t('uploadHelp')}</span><span class="small">≤ ${app.config?.max_upload_mb||200} MB</span></button>`:''}`;
 if(app.tab==='filters')return `<h3>${t('filters')}</h3><div class="filter-grid">${['none','warm','cool','mono','vivid','cinema','vintage'].map(f=>`<button class="filter-button ${app.project.clips[app.selected]?.filter===f?'active':''}" data-action="filter:${f}">${t(f)}${['cinema','vintage'].includes(f)?'<br><span class="caps muted" style="font-size:8px">PLUS</span>':''}</button>`).join('')}</div>`;
 if(app.tab==='text'){const text=app.project.texts[app.textSelected];return `${btn('add-text',t('addText'),'plus','tiny primary','style="width:100%"')}${app.project.texts.map((x,i)=>`<button class="subtitle-row" style="display:block;width:100%;text-align:left;margin-top:10px" data-action="select-text:${i}">${esc(x.text.slice(0,60))}</button>`).join('')}${text?`<div class="divider"></div><div class="field"><label>${t('textContent')}</label><textarea data-text-field="text" rows="3">${esc(text.text)}</textarea></div><div class="field-row">${field('start',text.start,'number','step=".1" min="0"','text')}${field('end',text.end,'number','step=".1" min=".1"','text')}</div><div class="field-row">${field('fontSize',text.size,'number','min="16" max="120"','text')}${field('color',text.color,'color','','text')}</div><div class="field"><label>${t('position')}</label><select data-text-field="position">${['top','center','bottom'].map(v=>`<option value="${v}" ${v===text.position?'selected':''}>${t(v)}</option>`).join('')}</select></div>${btn('remove-text',t('remove'),'trash','tiny')}`:''}`;}
 if(app.tab==='audio'){const track=app.project.audio[app.audioSelected],source=track&&mById(track.media);return `${btn('upload',t('import'),'upload','tiny','style="width:100%"')}<div style="margin-top:10px">${btn(app.recording?'record-stop':'record',t(app.recording?'stopRecord':'record'),'mic',app.recording?'primary':'tiny','style="width:100%"')}</div><p class="form-help">${t(app.recording?'micRecording':'recordHelp')}</p>${app.project.audio.map((x,i)=>`<button class="subtitle-row" style="display:block;width:100%;text-align:left" data-action="select-audio:${i}">♫ ${esc(mById(x.media)?.name)}</button>`).join('')}${track?`<div class="divider"></div>${source?`<audio class="audio-audition" controls preload="none" src="${source.url}"></audio>`:''}${field('offset',track.offset,'number','min="0" step=".1"','audio')}${field('start',track.in,'number','min="0" step=".1"','audio')}${field('volume',track.volume,'number','min="0" max="2" step=".05"','audio')}${field('musicFadeIn',track.fadeIn||0,'number','min="0" max="10" step=".1"','audio')}${field('musicFadeOut',track.fadeOut||0,'number','min="0" max="10" step=".1"','audio')}${btn('align-audio',t('alignAudio'),'play','tiny')}<label class="check-label"><input type="checkbox" data-audio-field="loop" ${track.loop?'checked':''}>${t('loop')}</label>${btn('remove-audio',t('remove'),'trash','tiny')}`:`<p class="muted small">${t('noAudio')}</p>`}`;}
 if(app.tab==='subtitles')return `<div class="row wrap">${btn('import-srt',t('importSrt'),'upload','tiny')}${btn('download-srt','SRT','download','tiny')}${btn('add-caption',t('addCaption'),'plus','tiny')}</div><p class="form-help">${t('captionHelp')}</p>${btn('analyze:transcribe',t('runAi'),'spark','tiny primary','style="width:100%"')}<p class="form-help">${app.config?.ai?t('autoCaptionHelp'):t('aiDisabled')}</p>${app.project.subtitles.map((s,i)=>`<div class="subtitle-row"><textarea data-subtitle="${i}" data-sub-field="text" aria-label="${t('text')}">${esc(s.text)}</textarea><div class="row"><input type="number" data-subtitle="${i}" data-sub-field="start" aria-label="${t('start')}" value="${s.start}" min="0" step=".1"><span>→</span><input type="number" data-subtitle="${i}" data-sub-field="end" aria-label="${t('end')}" value="${s.end}" min=".1" step=".1"><button class="icon-btn" data-action="remove-caption:${i}" aria-label="${t('remove')}">${icon('trash')}</button></div></div>`).join('')||`<p class="muted small">${t('noCaptions')}</p>`}`;
 return `<h3>${t('aiTools')}</h3><p class="form-help">${t('autoCaptionHelp')}</p>${btn('analyze:transcribe',t('runAi'),'caption','tiny primary','style="width:100%"')}${!app.config?.ai?`<p class="form-help">${t('aiDisabled')}</p>`:''}<div class="divider"></div><h3>${t('silence')}</h3><p class="form-help">${t('silenceHelp')}</p>${btn('analyze:silence',t('analyze'),'scissors','tiny','style="width:100%"')}${app.busy?`<p class="processing">${t('processing')}</p>`:''}`;
}

function modal(html){$('#modal').classList.remove('owner-dashboard');$('#modal-content').innerHTML=`<div class="modal-inner">${html}</div>`;if(!$('#modal').open)$('#modal').showModal();}
function modalHead(title){return `<div class="modal-head row between"><h2>${title}</h2>${ib('close',t('close'),'close')}</div>`;}
document.addEventListener('input',e=>{
 if(e.target.id!=='project-search')return;
 const value=e.target.value.trim().toLowerCase();
 for(const card of $('[data-project-name]'))card.hidden=!card.dataset.projectName.includes(value);
});
let authResolve=null,authMode='login';
function authDialog(mode='login'){
 authMode=mode;drawAuth();
 return new Promise(resolve=>{authResolve=resolve;});
}
function drawAuth(){
 if(authMode==='telegram-code'){
   const bot=(app.config?.bot||'').replace(/^@/,'');
   modal(modalHead(tr('Telegram orqali kirish','Вход через Telegram','Sign in with Telegram'))+
     '<p>'+tr('Botdan kod oling va shu yerga kiriting.','Получите код в боте и введите его здесь.','Get a code from the bot and enter it here.')+'</p>'+
     '<a class="btn full" target="_blank" rel="noopener" href="https://t.me/'+esc(bot)+'?start=login">'+t('openBot')+'</a>'+
     '<form id="auth-form" class="stack"><label>Telegram · '+tr('Kirish kodi','Код входа','Sign-in code')+'<input id="tg-code" required minlength="12" maxlength="12" autocomplete="one-time-code"></label><div id="auth-error" role="alert"></div><button class="btn full primary" type="submit">'+t('login')+'</button></form>'+btn('login',t('login'),'','tiny'));return;
 }
 modal(`${modalHead(t(authMode))}<p class="muted small">${t('accountHelp')}</p><form id="auth-form"><div class="field"><label for="auth-username">${t('username')}</label><input id="auth-username" name="username" pattern="[a-zA-Z0-9_]{3,32}" autocomplete="username" required minlength="3" maxlength="32"></div><div class="field"><label for="auth-password">${t('password')}</label><input id="auth-password" name="password" type="password" autocomplete="${authMode==='register'?'new-password':'current-password'}" required minlength="8" maxlength="200"><span class="form-help">${t('passwordHelp')}</span></div><div id="auth-error" class="error" role="alert"></div><button class="btn primary full" type="submit">${t(authMode)}</button></form><div class="switch">${t(authMode==='login'?'noAccount':'hasAccount')}<button data-action="auth-mode">${t(authMode==='login'?'register':'login')}</button></div>${app.config?.bot?btn('tg-login',tr('Telegram orqali kirish','Войти через Telegram','Sign in with Telegram'),'external','full'):''}`);}
async function ensureAuth(){return app.user||await authDialog();}
async function loadUserData(){app.media=(await api('/api/media')).media;app.projects=(await api('/api/projects')).projects;app.orders=(await api('/api/orders')).orders;}
async function afterLogin(user){app.user=user;
 const explicit=query.has('lang')||query.has('theme');
 if(explicit)await api('/api/preferences','POST',{language:localStorage.getItem('fumist-language')||'uz',theme:localStorage.getItem('fumist-theme')||'system'});
 else{localStorage.setItem('fumist-language',user.language);localStorage.setItem('fumist-theme',user.theme);setTheme();}
 await loadUserData();restoreDraft();render();
}
function profileView(){
 const user=app.user;
 return `<div class="account-hero"><div class="avatar">${esc((user?.username||'F')[0].toUpperCase())}</div><div><p class="muted small">${t('account')}</p><h1>${esc(user?.username||t('guest'))}</h1></div><span class="pill">${plan().toUpperCase()}</span></div>
 <div class="account-grid">
 <section class="account-card"><h2>${t('projects')}</h2><strong>${app.projects.length}</strong>${btn('nav:projects',t('viewAll'),'arrow','tiny')}</section>
 <section class="account-card"><h2>${t('exports')}</h2><strong>${app.jobs.filter(job=>job.status==='done').length}</strong>${btn('nav:exports',t('viewAll'),'arrow','tiny')}</section>
 <section class="account-card"><h2>${t('plans')}</h2><strong>${plan().toUpperCase()}</strong>${user?.expires?`<p class="muted small">${date(user.expires)}</p>`:''}${btn('nav:plans',t('seePlans'),'arrow','tiny')}</section>
 </div><section class="account-card account-options"><h2>${t('settings')}</h2><div class="row wrap">${themeControls()}${user?btn('link-telegram',t(user.telegram_id?'telegramLinked':'telegramLink'),'link','tiny',user.telegram_id?'disabled':'')+btn('settings',t('settings'),'settings','tiny'):btn('login',t('login'),'external','primary tiny')}</div></section>`;
}
function settingsDialog(){modal(`${modalHead(t('settings'))}${app.config?.version?`<p class="small muted">FUMIST Studio v${esc(app.config.version)}</p>`:''}<div class="row" style="margin-bottom:20px"><div class="avatar">${esc((app.user?.username||'F')[0].toUpperCase())}</div><div><strong>${esc(app.user?.username||t('guest'))}</strong><div class="small muted">${plan().toUpperCase()} ${app.user?.expires?' · '+date(app.user.expires):''}</div></div></div><div class="row wrap">${themeControls()}</div><div class="divider"></div><div class="stack">${app.user?`${btn('link-telegram',t(app.user.telegram_id?'telegramLinked':'telegramLink'),'link','',app.user.telegram_id?'disabled':'')}${btn('download-json',t('projectJson'),'download')}${btn('logout',t('logout'),'external')}`:btn('login',t('login'),'external','primary')}${btn('terms',t('terms'),'help')}${btn('privacy',t('privacy'),'help')}<a class="btn" href="https://t.me/${esc(app.config?.support||'ferapmg')}" target="_blank" rel="noopener">${t('support')} @${esc(app.config?.support||'ferapmg')}</a></div><p class="form-help">${t('retention')}</p>`);}
function policyDialog(kind){modal(`${modalHead(t(kind))}<p class="muted">${t(kind==='privacy'?'privacyText':'termsText')}</p><div class="note">${t('approvalNote')}</div><p class="muted small" style="margin-top:18px">${t('retention')}</p><a href="https://t.me/${esc(app.config?.support||'ferapmg')}" target="_blank" rel="noopener">${t('support')}: @${esc(app.config?.support||'ferapmg')}</a>`);}
function exportDialog(){if(!app.project.clips.length){toast(t('emptyPreview'));return;}modal(`${modalHead(t('exportSettings'))}<p class="muted small">${t('exportHelp')}</p><div class="field-row"><div class="field"><label>${t('resolution')}</label><select id="export-resolution"><option value="720">720p</option><option value="1080" ${plan()==='free'?'disabled':''} ${app.project.resolution===1080?'selected':''}>1080p ${plan()==='free'?'· PLUS':''}</option></select></div><div class="field"><label>${t('fps')}</label><select id="export-fps"><option value="24" ${app.project.fps===24?'selected':''}>24</option><option value="30" ${app.project.fps===30?'selected':''}>30</option></select></div></div><div class="row between"><span class="muted">${t('duration')}</span><strong>${time(duration())}</strong></div><div class="row between" style="margin-top:12px"><span class="muted">${t('format')}</span><strong>MP4 · ${app.project.ratio}</strong></div><div class="divider"></div>${plan()==='free'?`<p class="muted small">${t('watermark')} · 2 min · 720p</p>`:''}${btn('start-export',t('startExport'),'download','primary full')}`);}
function openStarsInvoice(url){
 const tg=window.Telegram?.WebApp;
 if(!tg?.openInvoice || (tg.isVersionAtLeast&&!tg.isVersionAtLeast('6.1'))){location.assign(url);return;}
 tg.openInvoice(url,status=>{
   if(status==='paid')toast(t('review'));
   if(status==='pending')toast(t('paymentPending'));
   if(status==='failed')toast(t('paymentFailed'));
   $('#modal').close();navigate('plans');
 });
}
async function checkout(planName){if(!await ensureAuth())return;if(!app.config?.billing){toast(t('billingSetup'));return;}
 const tg=window.Telegram?.WebApp?.initData;
 const method=tg?'stars':'card';const price=app.config.prices[planName];
 if((method==='card'&&!app.config.card_ready)||(method==='stars'&&!price.stars)){toast(t('billingSetup'));return;}
 modal(`${modalHead(t('checkout'))}<div class="row between"><strong>FUMIST ${planName.toUpperCase()}</strong><span class="pill lime">${t('month')}</span></div><div class="plan-price">${(method==='card'?price.uzs:price.stars).toLocaleString()} <span class="small muted">${method==='card'?'so‘m':'Stars'}</span></div><p class="muted small">${method==='stars'?t('telegramPayment'):t('cardTransfer')}</p><div class="note">${t('approvalNote')}</div><label class="check-label"><input id="terms-check" type="checkbox">${t('acceptTerms')}</label>${btn('create-order:'+planName+':'+method,t('continue'),'arrow','primary full')}`);
}
function receiptDialog(order){app.order=order;modal(`${modalHead(t('checkout'))}<span class="pill">FUMIST ${order.plan?.toUpperCase()||''}</span><p class="muted small" style="margin-top:18px">${t('cardTransfer')}</p><div class="card-number">${esc(order.card_number)}</div><p>${t('cardHolder')}: <strong>${esc(order.card_holder)}</strong></p><p class="muted">${Number(order.amount||0).toLocaleString()} so‘m</p><div class="note">${t('approvalNote')}</div><div class="receipt-box"><p class="small muted">${t('receiptHint')}</p>${btn('upload-receipt',t('paid'),'upload','primary full')}</div><p class="small muted">#${order.id.slice(0,8)}</p>`);}
function makeClip(m){return {media:m.id,in:0,out:m.kind==='image'?5:Math.min(m.seconds,30),speed:1,volume:1,rotation:0,flip:false,filter:app.project.templateFilter||'none',brightness:0,contrast:1,saturation:1,fade:0,fit:'contain'};}
function addMedia(identifier){const m=mById(identifier);if(!m)return;history();if(m.kind==='audio'){if(app.project.audio.length>=3){toast(errorText('audio_limit'));return;}app.project.audio.push({media:m.id,in:0,offset:0,volume:.7,loop:false,fadeIn:0,fadeOut:0});app.audioSelected=app.project.audio.length-1;app.tab='audio';}else{app.project.clips.push(makeClip(m));app.selected=app.project.clips.length-1;}changed();}
async function saveProject(quiet=false){draftLocal();if(!app.user){if(quiet)return; if(!await ensureAuth())return;}
 const result=await api('/api/projects','POST',{id:app.projectId,name:app.name||t('untitled'),project:app.project});app.projectId=result.id;dirty=false;draftLocal();$('.cloud-status')?.replaceChildren(document.createTextNode(t('saved')));if(!quiet)toast(t('saved'));app.projects=(await api('/api/projects')).projects;
}
function draftLocal(){localStorage.setItem('fumist-draft-'+(app.user?.id||'guest'),JSON.stringify({project:app.project,id:app.projectId,name:app.name}));}
function cleanProject(raw){
 if(!raw||typeof raw!=='object'||!Array.isArray(raw.clips)||raw.clips.length>60)throw new Error('invalid_project');
 const p=blank();p.ratio=['16:9','9:16','1:1','4:5'].includes(raw.ratio)?raw.ratio:'16:9';p.resolution=[720,1080].includes(raw.resolution)?raw.resolution:720;p.fps=[24,30].includes(raw.fps)?raw.fps:30;
 const numeric=(n,fallback=0)=>Number.isFinite(Number(n))?Number(n):fallback;
 p.clips=raw.clips.map(c=>({media:/^[a-f0-9]{32}$/.test(c.media)?c.media:'',in:Math.max(0,numeric(c.in)),out:Math.min(7200,Math.max(.1,numeric(c.out,5))),speed:Math.min(4,Math.max(.25,numeric(c.speed,1))),volume:Math.min(2,Math.max(0,numeric(c.volume,1))),rotation:[0,90,180,270].includes(c.rotation)?c.rotation:0,flip:!!c.flip,filter:['none','warm','cool','mono','vivid','cinema','vintage'].includes(c.filter)?c.filter:'none',brightness:Math.min(.5,Math.max(-.5,numeric(c.brightness))),contrast:Math.min(2,Math.max(.5,numeric(c.contrast,1))),saturation:Math.min(2,Math.max(0,numeric(c.saturation,1))),fade:Math.min(2,Math.max(0,numeric(c.fade))),fit:c.fit==='cover'?'cover':'contain'})).filter(c=>c.out>c.in);
 for(const field of ['texts','subtitles'])p[field]=(Array.isArray(raw[field])?raw[field]:[]).slice(0,150).map(x=>({text:String(x.text||'').slice(0,500),start:Math.max(0,numeric(x.start)),end:Math.max(.1,numeric(x.end,5)),size:Math.min(120,Math.max(16,numeric(x.size,40))),color:/^#[a-f0-9]{6}$/i.test(x.color)?x.color:'#ffffff',position:['top','center','bottom'].includes(x.position)?x.position:'bottom'}));
 p.audio=(Array.isArray(raw.audio)?raw.audio:[]).slice(0,3).map(x=>({media:/^[a-f0-9]{32}$/.test(x.media)?x.media:'',offset:Math.max(0,numeric(x.offset)),in:Math.max(0,numeric(x.in)),volume:Math.min(2,Math.max(0,numeric(x.volume,.5))),loop:!!x.loop,...(x.maxLength>0?{maxLength:numeric(x.maxLength)}:{}),fadeIn:Math.min(10,Math.max(0,numeric(x.fadeIn))),fadeOut:Math.min(10,Math.max(0,numeric(x.fadeOut)))}));
 return p;
}
function restoreDraft(){try{const d=JSON.parse(localStorage.getItem('fumist-draft-'+(app.user?.id||'guest'))||'null');if(d){app.project=cleanProject(d.project);app.projectId=/^[a-f0-9]{32}$/.test(d.id)?d.id:null;app.name=String(d.name||t('untitled')).slice(0,100);}}catch{app.project=blank();}}
async function uploadFiles(files){if(!await ensureAuth())return;for(const file of files){if(file.size>(app.config?.max_upload_mb||200)*1024*1024){toast(errorText('file_too_large'));continue;}app.uploadPct=0;app.tab='media';render();try{const media=await new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open('POST','/api/media');xhr.setRequestHeader('X-Fumist','1');xhr.setRequestHeader('X-Filename',encodeURIComponent(file.name));xhr.upload.onprogress=e=>{if(e.lengthComputable){app.uploadPct=Math.round(e.loaded/e.total*100);const el=$('.upload-progress');if(el)el.innerHTML=`${t('uploading')} ${app.uploadPct}%<progress max="100" value="${app.uploadPct}"></progress>`;}};xhr.onload=()=>{let data;try{data=JSON.parse(xhr.responseText);}catch{reject(new Error(xhr.status===413?'file_too_large':xhr.status===429?'rate_limit':'upload_failed'));return;}xhr.status>=200&&xhr.status<300?resolve(data):reject(new Error(data.error||'upload_failed'));};xhr.onerror=()=>reject(new Error('network_error'));xhr.send(file);});app.media.unshift(media);addMedia(media.id);}catch(e){fail(e);}finally{app.uploadPct=null;render();}}}
async function recordVoice(){if(!navigator.mediaDevices||!window.MediaRecorder){toast(t('recordUnsupported'));return;}try{recordStream=await navigator.mediaDevices.getUserMedia({audio:true});recordParts=[];recorder=new MediaRecorder(recordStream);recorder.ondataavailable=e=>{if(e.data.size)recordParts.push(e.data);};recorder.onstop=async()=>{clearTimeout(recordTimer);recordStream.getTracks().forEach(t=>t.stop());app.recording=false;const mime=recorder.mimeType,ext=mime.includes('mp4')?'m4a':'webm';const file=new File(recordParts,['voiceover',ext].join('.'),{type:mime});await uploadFiles([file]);app.tab='audio';render();};recorder.start();app.recording=true;app.tab='audio';render();recordTimer=setTimeout(()=>{if(recorder?.state==='recording')recorder.stop();},120000);}catch{toast(t('recordDenied'));}}
function downloadText(filename,content,type='application/json'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function parseSrt(text){const toSec=v=>{const [h,m,s]=v.replace(',','.').split(':').map(Number);return h*3600+m*60+s;};return text.replace(/\r/g,'').trim().split(/\n\s*\n/).map(block=>{const lines=block.split('\n'),i=lines.findIndex(l=>l.includes('-->'));if(i<0)return null;const times=lines[i].match(/(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})/);if(!times)return null;return{start:toSec(times[1]),end:toSec(times[2]),text:lines.slice(i+1).join('\n').replace(/<[^>]*>/g,''),color:'#ffffff',size:40,position:'bottom'};}).filter(x=>x&&x.end>x.start).slice(0,150);}
function toSrt(){const stamp=n=>{const ms=Math.round(n*1000),h=Math.floor(ms/3600000),m=Math.floor(ms%3600000/60000),s=Math.floor(ms%60000/1000);return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(ms%1000).padStart(3,'0')}`;};return app.project.subtitles.map((s,i)=>`${i+1}\n${stamp(s.start)} --> ${stamp(s.end)}\n${s.text}\n`).join('\n');}
async function analyze(kind){const c=app.project.clips[app.selected],m=c&&mById(c.media);if(!c||!m?.has_audio){toast(t('selectMediaFirst'));return;}if(kind==='transcribe'&&!app.config.ai){toast(t('aiDisabled'));return;}if(app.busy)return;if(!await ensureAuth())return;pause();app.busy=true;render();try{const snapshot=clone(c),target=app.selected;const job=await api('/api/jobs','POST',{kind,project:{media:c.media,in:c.in,out:c.out}});let result;while(true){await new Promise(r=>setTimeout(r,1800));const state=await api('/api/jobs/'+job.id);if(state.status==='failed')throw new Error(state.error);if(state.status==='done'){result=JSON.parse(state.result);break;}}
 if(JSON.stringify(app.project.clips[target])!==JSON.stringify(snapshot)){toast(t('saved'));return;}
 if(kind==='transcribe' && !result.subtitles.length){toast(t('noSpeechFound'));return;}
 history();if(kind==='transcribe'){let before=app.project.clips.slice(0,target).reduce((s,c)=>s+(c.out-c.in)/c.speed,0);app.project.subtitles.push(...result.subtitles.map(s=>({...s,start:before+s.start/c.speed,end:before+s.end/c.speed})));app.tab='subtitles';}else if(result.ranges.length){const replacements=result.ranges.map(r=>({...c,in:r.in,out:r.out}));app.project.clips.splice(target,1,...replacements);toast(t('silenceApplied'));}else toast(t('noSilence'));changed();}catch(e){fail(e);}finally{app.busy=false;render();}}
async function action(action){
 if(action==='open-site'){window.Telegram.WebApp.openLink(location.origin+'/');return;}
 const [name,...parts]=action.split(':');const value=parts.join(':');
 if(name==='close'){$('#modal').close();return;}
 if(name==='home'||name==='nav'){navigate(name==='home'?'home':value);return;}
 if(name==='new'){if(dirty&&app.user)await saveProject(true);newProject();return;}
 if(name==='format' && launchFormats.some(([ratio]) => ratio === value)){
   launchRatio=value;
   render();
   document.querySelector(`[data-action="format:${value}"]`)?.focus();
   return;
 }
 if(name==='launch'){
   if(dirty && app.user) await saveProject(true);
   app.tab='media';
   newProject({...blank(),ratio:launchRatio});
   return;
 }
 if(name==='owner-panel'){await ownerPanel();return;}
 if(name==='owner-tab'){ownerTab=value;await ownerPanel();return;}
 if(name==='owner-review'){
   const [decision,order]=parts;
   if(!confirm(tr('Qarorni tasdiqlaysizmi?','Подтвердить решение?','Confirm this decision?')))return;
   await api('/api/owner/review','POST',{decision,order});await ownerPanel();return;
 }
 if(name==='tg-login'){authMode='telegram-code';drawAuth();return;}
 if(name==='login'){await authDialog();return;}
 if(name==='auth-mode'){authMode=authMode==='login'?'register':'login';drawAuth();return;}
 if(name==='logout'){await api('/api/logout','POST',{});pause();app.user=null;app.media=[];app.projects=[];app.orders=[];app.project=blank();app.projectId=null;app.name='';app.view='home';$('#modal').close();render();return;}
 if(name==='settings'){settingsDialog();return;}
 if(name==='terms'||name==='privacy'){policyDialog(name);return;}
 if(name==='refresh'){if(app.user)app.user=(await api('/api/me')).user;await loadView();return;}
 if(name==='quick'){if(!app.project.clips.length)newProject();else app.view='editor';app.tab=({captions:'ai',silence:'ai',audio:'audio',srt:'subtitles'})[value]||'media';render();return;}
 if(name==='template'){const preset=presets[Number(value)];if(!preset)return;if(preset.filter==='cinema'&&plan()==='free'){toast(t('planLocked'));navigate('plans');return;}if(dirty&&app.user)await saveProject(true);const p=blank();p.ratio=preset.ratio;p.templateFilter=preset.filter;p.texts=[{text:preset.text,start:0,end:5,size:preset.size,color:'#ffffff',position:preset.position}];newProject(p);app.name=t(preset.key);toast(t('templateApplied'));render();return;}
 if(name==='open-project'){const p=app.projects.find(p=>p.id===value);if(p){pause();app.project=cleanProject(JSON.parse(p.body));app.projectId=p.id;app.name=p.name;app.cursor=0;app.selected=app.project.clips.length?0:-1;app.history=[];app.future=[];app.view='editor';render();}return;}
 if(name==='delete-project'){modal(`${modalHead(t('confirmDelete'))}${btn('confirm-delete-project:'+value,t('remove'),'trash','primary full')}`);return;}
 if(name==='confirm-delete-project'){await api('/api/projects/'+value,'DELETE');app.projects=app.projects.filter(p=>p.id!==value);$('#modal').close();render();return;}
 if(name==='upload'){$('#media-input').click();return;}
 if(name==='add-media'){addMedia(value);return;}
 if(name==='delete-media'){if(app.project.clips.some(c=>c.media===value)||app.project.audio.some(a=>a.media===value)){toast(t('confirmDelete'));return;}await api('/api/media/'+value,'DELETE');app.media=app.media.filter(m=>m.id!==value);render();return;}
 if(name==='tab'){app.tab=value;render();return;}
 if(name==='select-clip'){if(window.innerWidth<=900){const details=$('.inspector');if(details)details.open=true;}app.selected=Number(value);app.cursor=app.project.clips.slice(0,app.selected).reduce((s,c)=>s+(c.out-c.in)/c.speed,0);pause();render();return;}
 if(name==='undo'){if(app.history.length){app.future.push(clone(app.project));app.project=app.history.pop();app.selected=Math.min(app.selected,app.project.clips.length-1);changed();}return;}
 if(name==='redo'){if(app.future.length){app.history.push(clone(app.project));app.project=app.future.pop();changed();}return;}
 if(name==='play'){app.playing?pause():play();return;}
 if(name==='prev'){seek(Math.max(0,app.cursor-5));return;}
 if(name==='next'){seek(Math.min(duration(),app.cursor+5));return;}
 if(['split','duplicate','remove-clip','move-left','move-right','rotate','flip','reset-clip','filter'].includes(name)){
  const c=app.project.clips[app.selected];if(!c)return;
  if(name==='filter'&&['cinema','vintage'].includes(value)&&plan()==='free'){toast(t('planLocked'));return;}
  history();
  if(name==='split'){const at=clipAt(app.cursor);if(!at||at.i!==app.selected||at.local<.1||(c.out-c.in)/c.speed-at.local<.1)return;const cut=c.in+at.local*c.speed;app.project.clips.splice(app.selected,1,{...c,out:cut},{...c,in:cut});}
  if(name==='duplicate')app.project.clips.splice(app.selected+1,0,clone(c));
  if(name==='remove-clip'){app.project.clips.splice(app.selected,1);app.selected=Math.min(app.selected,app.project.clips.length-1);}
  if(name==='move-left'&&app.selected>0){[app.project.clips[app.selected-1],app.project.clips[app.selected]]=[c,app.project.clips[app.selected-1]];app.selected--;}
  if(name==='move-right'&&app.selected<app.project.clips.length-1){[app.project.clips[app.selected+1],app.project.clips[app.selected]]=[c,app.project.clips[app.selected+1]];app.selected++;}
  if(name==='rotate')c.rotation=(c.rotation+90)%360;
  if(name==='flip')c.flip=!c.flip;
  if(name==='filter')c.filter=value;
  if(name==='reset-clip')Object.assign(c,{speed:1,volume:1,rotation:0,flip:false,filter:'none',brightness:0,contrast:1,saturation:1,fade:0,fit:'contain'});
  changed();return;
 }
 if(name==='add-text'||name==='add-caption'){if(duration()<=0){toast(t('emptyPreview'));return;}history();const list=name==='add-text'?'texts':'subtitles';app.project[list].push({text:t('yourText'),start:app.cursor,end:Math.min(duration(),app.cursor+5),size:40,color:'#ffffff',position:name==='add-text'?'center':'bottom'});if(list==='texts'){app.textSelected=app.project.texts.length-1;app.tab='text';}else app.tab='subtitles';changed();return;}
 if(name==='select-text'){app.textSelected=Number(value);app.tab='text';render();return;}
 if(name==='remove-text'){history();app.project.texts.splice(app.textSelected,1);app.textSelected=-1;changed();return;}
 if(name==='extract-audio'){
   const index=app.selected,clip=app.project.clips[index],source=clip&&mById(clip.media);
   if(!source?.has_audio)return;
   if(app.project.audio.length>=3){toast(errorText('audio_limit'));return;}
   if(clip.speed!==1){toast(t('extractNormalSpeed'));return;}
   const offset=app.project.clips.slice(0,index).reduce((sum,c)=>sum+(c.out-c.in)/c.speed,0);
   history();
   app.project.audio.push({media:clip.media,in:clip.in,offset,volume:clip.volume||1,loop:false,fadeIn:0,fadeOut:0,maxLength:clip.out-clip.in});
   clip.volume=0;app.audioSelected=app.project.audio.length-1;app.tab='audio';changed();return;
 }
 if(name==='mute-clip'){const clip=app.project.clips[app.selected];if(!clip)return;history();clip.volume=clip.volume?0:1;changed();return;}
 if(name==='align-audio'){const track=app.project.audio[app.audioSelected];if(!track||!duration())return;history();track.offset=Math.min(app.cursor,Math.max(0,duration()-.01));changed();return;}
 if(name==='select-audio'){app.audioSelected=Number(value);app.tab='audio';render();return;}
 if(name==='remove-audio'){history();app.project.audio.splice(app.audioSelected,1);app.audioSelected=-1;changed();return;}
 if(name==='remove-caption'){history();app.project.subtitles.splice(Number(value),1);changed();return;}
 if(name==='record'){if(await ensureAuth())await recordVoice();return;}
 if(name==='record-stop'){if(recorder?.state==='recording')recorder.stop();return;}
 if(name==='import-srt'){$('#srt-input').click();return;}
 if(name==='download-srt'){downloadText('FUMIST-captions.srt',toSrt(),'text/plain');return;}
 if(name==='download-json'){downloadText('FUMIST-project.json',JSON.stringify({name:app.name,project:app.project},null,2));return;}
 if(name==='import-json'){$('#project-input').click();return;}
 if(name==='analyze'){await analyze(value);return;}
 if(name==='save'){await saveProject();return;}
 if(name==='export'){exportDialog();return;}
 if(name==='start-export'){if(!await ensureAuth())return;app.project.resolution=Number($('#export-resolution')?.value||720);app.project.fps=Number($('#export-fps')?.value||30);await saveProject(true);await api('/api/jobs','POST',{kind:'render',project:app.project});$('#modal').close();toast(t('exportStarted'));navigate('exports');return;}
 if(name==='buy'){await checkout(value);return;}
 if(name==='create-order'){
  if(!$('#terms-check').checked){toast(errorText('accept_terms'));return;}
  const [p,method]=parts;const data=await api('/api/orders','POST',{plan:p,method,terms:true});
  if(method==='stars')openStarsInvoice(data.invoice);
  else receiptDialog({...data,plan:p,amount:app.config.prices[p].uzs});return;
 }
 if(name==='upload-receipt'){$('#receipt-input').click();return;}
 if(name==='resume-order'){const order=await api('/api/orders/'+value);if(order.method==='card')receiptDialog(order);else if(order.invoice)openStarsInvoice(order.invoice);return;}
 if(name==='cancel-order'){await api('/api/orders/'+value,'DELETE');await loadView();return;}
 if(name==='link-telegram'){const result=await api('/api/telegram-link','POST',{});window.open(result.url,'_blank','noopener');return;}
}

document.addEventListener('click',async e=>{const el=e.target.closest('[data-action]');if(!el)return;const a=el.dataset.action;if(a==='open-site')e.preventDefault();el.disabled=true;try{await action(a);}catch(error){fail(error);}finally{if(el.isConnected)el.disabled=false;}});
$('#modal').addEventListener('close',()=>{if(authResolve){authResolve(null);authResolve=null;}});
document.addEventListener('submit',async e=>{if(e.target.id==='owner-search'){e.preventDefault();ownerPanel(new FormData(e.target).get('search')).catch(fail);return;}if(e.target.id!=='auth-form')return;e.preventDefault();const submit=$('button[type=submit]',e.target);submit.disabled=true;try{const result=await api('/api/auth/'+authMode,'POST',authMode==='telegram-code'?{code:$('#tg-code').value}:{username:$('#auth-username').value,password:$('#auth-password').value});await afterLogin(result.user);const resolve=authResolve;authResolve=null;$('#modal').close();resolve?.(result.user);}catch(error){$('#auth-error').textContent=errorText(error.message);}finally{submit.disabled=false;}});
document.addEventListener('change',async e=>{const el=e.target;
 try{
  if(el.dataset.setting){const key=el.dataset.setting;localStorage.setItem('fumist-'+key,el.value);setTheme();if(app.user)app.user=(await api('/api/preferences','POST',{language:localStorage.getItem('fumist-language')||'uz',theme:localStorage.getItem('fumist-theme')||'system'})).user;render();if($('#modal').open&&$('#modal-content').textContent.includes('FUMIST'))settingsDialog();return;}
  if(el.id==='project-name'){app.name=el.value.slice(0,100);draft();return;}
  if(el.id==='ratio'){history();app.project.ratio=el.value;changed();return;}
  if(el.id==='zoom'){app.zoom=Number(el.value);render();return;}
  if(el.dataset.clipField){const c=app.project.clips[app.selected];if(!c)return;const key=({start:'in',end:'out'})[el.dataset.clipField]||el.dataset.clipField;const value=['filter','fit'].includes(key)?el.value:Number(el.value);if(!['filter','fit'].includes(key)&&(!Number.isFinite(value)||!el.checkValidity())){render();return;}if(key==='filter'&&['cinema','vintage'].includes(value)&&plan()==='free'){toast(t('planLocked'));render();return;}history();c[key]=value;c.fade=Math.min(c.fade,(c.out-c.in)/c.speed/2);changed();return;}
  if(el.dataset.textField){const x=app.project.texts[app.textSelected];if(!x)return;const key=el.dataset.textField==='fontSize'?'size':el.dataset.textField;const val=['text','color','position'].includes(key)?el.value:Number(el.value);if(typeof val==='number'&&!Number.isFinite(val))return;history();x[key]=val;changed();return;}
  if(el.dataset.audioField){const x=app.project.audio[app.audioSelected];if(!x)return;const key=({start:'in',musicFadeIn:'fadeIn',musicFadeOut:'fadeOut'})[el.dataset.audioField]||el.dataset.audioField;history();x[key]=key==='loop'?el.checked:Number(el.value);changed();return;}
  if(el.dataset.subtitle!==undefined){const x=app.project.subtitles[Number(el.dataset.subtitle)];if(!x)return;history();x[el.dataset.subField]=el.dataset.subField==='text'?el.value:Number(el.value);changed();return;}
  if(el.id==='media-input'){const files=[...el.files];el.value='';await uploadFiles(files);return;}
  if(el.id==='srt-input'){const f=el.files[0];el.value='';if(!f||f.size>1024*1024)throw new Error('file_too_large');if(!duration()){toast(t('emptyPreview'));return;}history();app.project.subtitles=parseSrt(await f.text());changed();return;}
  if(el.id==='project-input'){const f=el.files[0];el.value='';if(!f||f.size>2*1024*1024)throw new Error('file_too_large');let data;try{data=JSON.parse(await f.text());}catch{throw new Error('invalid_project');}newProject(cleanProject(data.project||data));app.name=String(data.name||t('untitled')).slice(0,100);toast(t('projectImported'));render();return;}
  if(el.id==='receipt-input'){const f=el.files[0];el.value='';if(!f||f.size>10*1024*1024)throw new Error('file_too_large');const response=await fetch('/api/receipt/'+app.order.id,{method:'POST',headers:{'X-Fumist':'1','X-Filename':encodeURIComponent(f.name)},body:f});const data=await response.json();if(!response.ok)throw new Error(data.error);$('#modal').close();toast(t('receiptSent'));navigate('plans');return;}
 }catch(error){fail(error);}
});
document.addEventListener('input',e=>{if(e.target.matches('input[type=range][data-clip-field]'))e.target.previousElementSibling?.querySelector('span')?.replaceChildren(document.createTextNode(e.target.value));});
document.addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select')||$('#modal').open||app.view!=='editor')return;if(e.code==='Space'){e.preventDefault();app.playing?pause():play();}if((e.ctrlKey||e.metaKey)&&e.key==='z'){e.preventDefault();action(e.shiftKey?'redo':'undo');}if((e.ctrlKey||e.metaKey)&&e.key==='s'){e.preventDefault();saveProject().catch(fail);}if(e.key==='Delete')action('remove-clip');if(e.key==='ArrowLeft')seek(Math.max(0,app.cursor-.5));if(e.key==='ArrowRight')seek(Math.min(duration(),app.cursor+.5));});
document.addEventListener('dragstart',e=>{const el=e.target.closest('[data-clip]');if(el){e.dataTransfer.setData('text/plain','clip:'+el.dataset.clip);}});
document.addEventListener('dragover',e=>{if(e.target.closest('.timeline,.upload-zone,.library'))e.preventDefault();});
document.addEventListener('drop',e=>{const target=e.target.closest('[data-clip]');if(e.dataTransfer.files.length&&e.target.closest('.timeline,.upload-zone,.library')){e.preventDefault();uploadFiles([...e.dataTransfer.files]).catch(fail);return;}if(target){e.preventDefault();const data=e.dataTransfer.getData('text/plain');if(data.startsWith('clip:')){const from=Number(data.slice(5)),to=Number(target.dataset.clip);if(Number.isInteger(from)&&app.project.clips[from]&&from!==to){history();const[c]=app.project.clips.splice(from,1);app.project.clips.splice(to,0,c);app.selected=to;changed();}}}});
document.addEventListener('pointerdown',e=>{const ruler=e.target.closest('#ruler');if(ruler)seek(Math.max(0,Math.min(duration(),(e.clientX-ruler.getBoundingClientRect().left)/app.zoom)));});

let lastOverlay=null,lastTime=null,previewHeight=0,previewObserver;
let audioContext, mediaGains=new WeakMap();
function unlockSound(){
 const AudioContext=window.AudioContext||window.webkitAudioContext;
 if(!AudioContext)return;
 if(!audioContext)audioContext=new AudioContext();
 if(audioContext.state!=='running')audioContext.resume().catch(()=>{});
}
function setGain(media,volume){
 if(!audioContext){media.volume=Math.min(1,volume);return;}
 let entry=mediaGains.get(media);
 if(!entry){
   const node=audioContext.createMediaElementSource(media), gain=audioContext.createGain();
   node.connect(gain);gain.connect(audioContext.destination);
   entry={node,gain};mediaGains.set(media,entry);
 }
 if(Math.abs(entry.gain.gain.value-volume)>.005)entry.gain.gain.value=volume;
}
function releaseSound(media){
 const entry=mediaGains.get(media);
 if(entry){entry.node.disconnect();entry.gain.disconnect();mediaGains.delete(media);}
}
function pauseMedia(){
 const v=$('#preview-video');if(v)v.pause();
 for(const a of trackAudio){a.pause();releaseSound(a);}
 trackAudio=[];
}
function pause(){app.playing=false;cancelAnimationFrame(raf);pauseMedia();const button=$('[data-action="play"]');if(button)button.innerHTML=icon('play');}
function play(){if(!duration())return;const audition=$('.audio-audition');if(audition)audition.pause();unlockSound();if(app.cursor>=duration()-.01)app.cursor=0;app.playing=true;lastFrame=performance.now();const button=$('[data-action="play"]');if(button)button.innerHTML=icon('pause');paintPreview(true);cancelAnimationFrame(raf);raf=requestAnimationFrame(tick);}
function seek(cursor){app.cursor=cursor;paintPreview(true);}
function tick(stamp){if(!app.playing)return;const dt=Math.min(.15,(stamp-lastFrame)/1000);lastFrame=stamp;const v=$('#preview-video');if(v&&!v.hidden&&v.readyState<2){raf=requestAnimationFrame(tick);return;}app.cursor=Math.min(duration(),app.cursor+dt);paintPreview();if(app.cursor>=duration()){pause();return;}raf=requestAnimationFrame(tick);}

function bindPreview(){
 const frame=$('#preview-frame');lastOverlay=null;lastTime=null;previewHeight=frame.clientHeight;
 previewObserver?.disconnect();
 if(window.ResizeObserver){previewObserver=new ResizeObserver(entries=>{previewHeight=entries[0].contentRect.height;if(!app.playing&&frame.isConnected)paintPreview();});previewObserver.observe(frame);}
 playback=$('#preview-video');if(playback){playback.addEventListener('loadedmetadata',()=>paintPreview(true));playback.addEventListener('error',()=>{if(app.playing)pause();});}}
function paintPreview(force=false){
 const video=$('#preview-video'),image=$('#preview-image'),frame=$('#preview-frame');if(!frame)return;
 const at=clipAt(app.cursor),m=at&&mById(at.clip.media),empty=$('#preview-empty');
 empty.hidden=!!m;video.hidden=!m||m.kind!=='video';image.hidden=!m||m.kind!=='image';
 if(m){const c=at.clip,src=m.url,newClip=at.i!==previewClip||src!==previewSource;const el=m.kind==='video'?video:image;
  if(newClip){video.pause();if(m.kind==='video'){video.src=src;video.load();}else image.src=src;previewClip=at.i;previewSource=src;}
  const effects={none:'',mono:'grayscale(1)',warm:'sepia(.18) saturate(1.1)',cool:'hue-rotate(12deg)',vivid:'saturate(1.4) contrast(1.08)',cinema:'contrast(1.15) saturate(.8)',vintage:'sepia(.35) contrast(.9)'};
  el.style.filter=`brightness(${1+c.brightness}) contrast(${c.contrast}) saturate(${c.saturation}) ${effects[c.filter]||''}`;el.style.objectFit=c.fit==='cover'?'cover':'contain';el.style.transform=`rotate(${c.rotation}deg) scaleX(${c.flip?-1:1})`;
  const d=(c.out-c.in)/c.speed;el.style.opacity=c.fade?Math.min(1,at.local/c.fade,Math.max(0,(d-at.local)/c.fade)):1;
  if(m.kind==='video'){video.playbackRate=c.speed;setGain(video,c.volume);const wanted=c.in+at.local*c.speed;if(video.readyState&&((force||newClip)||Math.abs(video.currentTime-wanted)>.4))video.currentTime=Math.min(c.out,wanted);if(app.playing&&video.paused&&video.readyState>=2)video.play().catch(()=>{});else if(!app.playing)video.pause();}
 }
 const overlays=[...app.project.texts,...app.project.subtitles].filter(x=>app.cursor>=x.start&&app.cursor<=x.end);
 if(plan()==='free'&&m)overlays.push({text:'FUMIST Studio',color:'#ffffff',size:22,position:'top'});
 const overlayHtml=overlays.map(x=>`<div class="preview-text" style="${x.position==='top'?'top:6%':x.position==='center'?'top:50%;transform:translateY(-50%)':'bottom:10%'};font-size:${x.size*previewHeight/720}px;color:${x.color}"><span>${esc(x.text)}</span></div>`).join('');
 if(overlayHtml!==lastOverlay){$('#preview-overlays').innerHTML=overlayHtml;lastOverlay=overlayHtml;}
 const currentTime=time(app.cursor);if(currentTime!==lastTime){$('#current-time').textContent=currentTime;lastTime=currentTime;}
 $('#playhead').style.left=app.cursor*app.zoom+'px';
 if(app.playing&&!trackAudio.length){
   for(const track of app.project.audio){
     const source=mById(track.media);if(!source)continue;
     const audio=new Audio(source.url);audio.preload='auto';audio._track=track;
     audio.addEventListener('error',()=>{if(trackAudio.includes(audio))toast(t('audioPlaybackError'));},{once:true});
     trackAudio.push(audio);
   }
 }
 for(const audio of trackAudio){
   const track=audio._track,source=mById(track.media);
   const local=app.cursor-track.offset;
   const length=Math.min(duration()-track.offset,track.maxLength||Infinity,track.loop?Infinity:source.seconds-track.in);
   if(local<0||local>=length){if(!audio.paused)audio.pause();continue;}
   let wanted=track.in+local;if(track.loop)wanted%=source.seconds;
   const fadeIn=track.fadeIn?local/Math.min(track.fadeIn,length):1;
   const fadeOut=track.fadeOut?(length-local)/Math.min(track.fadeOut,length):1;
   setGain(audio,track.volume*Math.max(0,Math.min(1,fadeIn,fadeOut)));
   if(audio.readyState&&(force||Math.abs(audio.currentTime-wanted)>.35))audio.currentTime=wanted;
   if(app.playing&&audio.paused&&!audio._starting&&!audio._blocked){
     audio._starting=true;
     audio.play().catch(error=>{if(error.name!=='AbortError'&&trackAudio.includes(audio)){audio._blocked=true;toast(t('audioPlaybackError'));}}).finally(()=>{audio._starting=false;});
   }
 }
}
async function boot(){
 try{app.config=await api('/api/config');}catch(e){toast(errorText('network_error'));}
 const tg=window.Telegram?.WebApp;
 try{if(tg?.initData){tg.ready();tg.expand();const result=await api('/api/auth/telegram','POST',{initData:tg.initData});await afterLogin(result.user);}else{const response=await fetch('/api/me');if(response.ok){const data=await response.json();await afterLogin(data.user);}else restoreDraft();}}catch(e){fail(e);}
 const requestedView=query.get('view');
 if(['editor','projects','exports','plans','profile'].includes(requestedView)){
   navigate(requestedView);
 } else render();
 if(requestedView==='admin'&&app.user?.is_owner)await ownerPanel();
 if(!app.user&&!tg?.initData&&!$('#modal').open)authDialog();
 pollTimer=setInterval(async()=>{if(!app.user||document.hidden||app.playing)return;try{app.user=(await api('/api/me')).user;if(['exports','plans'].includes(app.view)){if(app.view==='exports')app.jobs=(await api('/api/jobs')).jobs;else app.orders=(await api('/api/orders')).orders;render();}}catch{}},6000);
}
document.addEventListener('visibilitychange',()=>{if(document.hidden&&app.playing)pause();});
render();boot();
