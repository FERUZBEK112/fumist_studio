"""Bounded FFmpeg rendering and analysis; all media IDs are resolved by ownership."""
import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
import wave
from functools import lru_cache
from pathlib import Path
import core

FFMPEG = os.getenv('FFMPEG_PATH', 'ffmpeg')
FFPROBE = os.getenv('FFPROBE_PATH', 'ffprobe')
STOP = threading.Event()

def demux(path):
    # Force a real container. Do not allow uploaded playlist files to reference
    # network resources or another account's media through FFmpeg auto-detection.
    formats={'.mp4':'mov','.m4v':'mov','.mov':'mov','.m4a':'mov','.mkv':'matroska','.webm':'matroska',
             '.mp3':'mp3','.wav':'wav','.ogg':'ogg','.opus':'ogg','.flac':'flac','.aif':'aiff','.aiff':'aiff','.aac':'aac','.png':'png_pipe',
             '.jpg':'jpeg_pipe','.jpeg':'jpeg_pipe','.webp':'webp_pipe'}
    value=formats.get(Path(path).suffix.lower())
    if not value: raise core.Error('invalid_media')
    return value

def number(value, lo, hi, default=0):
    try: result = float(value if value is not None else default)
    except (TypeError, ValueError): raise core.Error('invalid_number')
    if not math.isfinite(result) or not lo <= result <= hi: raise core.Error('invalid_number')
    return result

def media_owned(identifier, user_id):
    with core.db() as c:
        row = c.execute('SELECT * FROM media WHERE id=? AND user_id=?',(identifier,user_id)).fetchone()
    if not row: raise core.Error('media_not_found',404)
    return dict(row)

def probe(path):
    try:
        result = subprocess.run([FFPROBE,'-v','error','-protocol_whitelist','file,pipe','-f',demux(path),'-show_format','-show_streams','-of','json',str(path)],
                                capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise core.Error('media_probe_timeout',422) from exc
    if result.returncode: raise core.Error('invalid_media')
    info = json.loads(result.stdout)
    streams = info.get('streams',[])
    videos = [s for s in streams if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic')]
    audio = any(s['codec_type']=='audio' for s in streams)
    video = videos[0] if videos else {}
    ext = Path(path).suffix.lower()
    kind = 'image' if ext in ('.png','.jpg','.jpeg','.webp') else 'video' if videos else 'audio' if audio else None
    if not kind: raise core.Error('invalid_media')
    seconds = float(info.get('format',{}).get('duration') or 0)
    if kind != 'image' and (not math.isfinite(seconds) or not 0 < seconds <= 7200): raise core.Error('invalid_duration')
    if video.get('width',0)>7680 or video.get('height',0)>7680: raise core.Error('resolution_too_large')
    return dict(kind=kind,seconds=seconds,width=video.get('width',0),height=video.get('height',0),has_audio=int(audio))

def validate(body,u):
    if not isinstance(body,dict): raise core.Error('invalid_project')
    limits=u['limits']
    clips=body.get('clips',[])
    if not isinstance(clips,list) or not 1 <= len(clips) <= limits['clips']: raise core.Error('clip_limit')
    ratio=body.get('ratio','16:9')
    if ratio not in ('16:9','9:16','1:1','4:5'): raise core.Error('invalid_ratio')
    resolution=int(number(body.get('resolution',720),720,1080))
    if resolution not in (720,1080) or resolution>limits['height']: raise core.Error('plan_required',403)
    fps=int(number(body.get('fps',30),24,30))
    if fps not in (24,30): raise core.Error('invalid_fps')
    clean={'ratio':ratio,'resolution':resolution,'fps':fps,'clips':[], 'texts':[], 'subtitles':[], 'audio':[]}
    total=0
    for clip in clips:
        m=media_owned(clip.get('media'),u['id'])
        if m['kind'] not in ('video','image'): raise core.Error('invalid_clip')
        start=number(clip.get('in',0),0,m['seconds'] if m['kind']=='video' else 0)
        end=number(clip.get('out',m['seconds'] or 5),start+0.1,m['seconds'] if m['kind']=='video' else 120)
        speed=number(clip.get('speed',1),.25,4)
        duration=(end-start)/speed
        total+=duration
        if total>limits['seconds']: raise core.Error('duration_limit',403)
        filters=('none','cinema','mono','warm','cool','vintage','vivid')
        effect=clip.get('filter','none')
        if effect not in filters: raise core.Error('invalid_filter')
        if effect in ('cinema','vintage') and u['plan']=='free': raise core.Error('plan_required',403)
        rotation=int(number(clip.get('rotation',0),0,270))
        if rotation not in (0,90,180,270): raise core.Error('invalid_rotation')
        clean['clips'].append(dict(media=m['id'],**{'in':start,'out':end},speed=speed,
            volume=number(clip.get('volume',1),0,2),rotation=rotation,flip=bool(clip.get('flip')),
            filter=effect,brightness=number(clip.get('brightness',0),-.5,.5),
            contrast=number(clip.get('contrast',1),.5,2),saturation=number(clip.get('saturation',1),0,2),
            fade=number(clip.get('fade',0),0,min(2,duration/2)),fit='cover' if clip.get('fit')=='cover' else 'contain'))
    for field in ('texts','subtitles'):
        entries=body.get(field,[])
        if not isinstance(entries,list) or len(entries)>150: raise core.Error('text_limit')
        for text in entries:
            content=str(text.get('text','')).replace('\x00','')[:500]
            color=str(text.get('color','#ffffff'))
            if not re.fullmatch(r'#[0-9a-fA-F]{6}',color): raise core.Error('invalid_color')
            a=number(text.get('start',0),0,total)
            b=number(text.get('end',total),a+.01,total)
            clean[field].append(dict(text=content,start=a,end=b,color=color,
                size=number(text.get('size',48),16,120),position=text.get('position','bottom') if text.get('position') in ('top','center','bottom') else 'bottom'))
    tracks=body.get('audio',[])
    if not isinstance(tracks,list) or len(tracks)>3: raise core.Error('audio_limit')
    for track in tracks:
        m=media_owned(track.get('media'),u['id'])
        if not m['has_audio']: raise core.Error('no_audio')
        offset=number(track.get('offset',0),0,max(0,total-.01))
        start=number(track.get('in',0),0,max(0,m['seconds']-.01))
        clean['audio'].append(dict(media=m['id'],offset=offset,**{'in':start},volume=number(track.get('volume',.5),0,2),loop=bool(track.get('loop')),
                                   fadeIn=number(track.get('fadeIn',0),0,10),fadeOut=number(track.get('fadeOut',0),0,10),
                                   maxLength=number(track.get('maxLength',0),0,7200)))
    clean['duration']=total
    return clean

def run(args,cwd=None,timeout=1800):
    result=subprocess.run([FFMPEG,'-nostdin','-hide_banner','-loglevel','error','-y','-threads','2','-filter_threads','2','-filter_complex_threads','2',*args],
                          cwd=cwd,capture_output=True,timeout=timeout)
    if result.returncode:
        # Bounded diagnostic kept server-side; never return paths or source filenames to clients.
        print('FFmpeg failed:',result.stderr.decode(errors='replace')[-1500:])
        raise core.Error('render_failed')

def progress(identifier,n):
    with core.db() as c: c.execute('UPDATE jobs SET progress=? WHERE id=?',(n,identifier))

def dimensions(p):
    h=p['resolution']
    w,h = {'16:9':(h*16/9,h),'9:16':(h,h*16/9),'1:1':(h,h),'4:5':(h,h*5/4)}[p['ratio']]
    return int(w)//2*2,int(h)//2*2

def render(identifier,u,p):
    work=core.DATA/'work'/identifier
    work.mkdir(exist_ok=True)
    w,h=dimensions(p)
    for i,clip in enumerate(p['clips']):
        m=media_owned(clip['media'],u['id'])
        image=m['kind']=='image'
        duration=(clip['out']-clip['in'])/clip['speed']
        args=['-protocol_whitelist','file,pipe']
        if image: args+=['-loop','1','-framerate',str(p['fps'])]
        else: args+=['-ss',str(clip['in'])]
        args+=['-f',demux(m['path']),'-i',str(core.DATA/m['path'])]
        if not m['has_audio']:
            args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        vf=[f"setpts=(PTS-STARTPTS)/{clip['speed']}"]
        if clip['rotation']==90: vf+=['transpose=1']
        if clip['rotation']==180: vf+=['hflip','vflip']
        if clip['rotation']==270: vf+=['transpose=2']
        if clip['flip']: vf+=['hflip']
        if clip['fit']=='cover': vf += [f'scale={w}:{h}:force_original_aspect_ratio=increase',f'crop={w}:{h}']
        else: vf += [f'scale={w}:{h}:force_original_aspect_ratio=decrease',f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black']
        vf += ['setsar=1',f'fps={p["fps"]}',f"eq=brightness={clip['brightness']}:contrast={clip['contrast']}:saturation={clip['saturation']}"]
        vf += {'none':[],'mono':['hue=s=0'],'warm':['colorbalance=rs=.10:bs=-.08'],
               'cool':['colorbalance=rs=-.08:bs=.12'],'vivid':['eq=saturation=1.4:contrast=1.08'],
               'cinema':['eq=contrast=1.15:saturation=.8'],'vintage':['curves=preset=vintage']}[clip['filter']]
        if clip['fade']:
            vf += [f"fade=t=in:st=0:d={clip['fade']}",f"fade=t=out:st={duration-clip['fade']}:d={clip['fade']}"]
        speed=clip['speed']
        tempos=[]
        while speed>2: tempos.append('atempo=2'); speed/=2
        while speed<.5: tempos.append('atempo=.5'); speed/=.5
        af=[f'atrim=duration={clip["out"]-clip["in"]}','asetpts=PTS-STARTPTS',*tempos,f'atempo={speed}',f'volume={clip["volume"]}','aresample=48000','apad']
        args += ['-map','0:v:0','-map','0:a:0' if m['has_audio'] else '1:a:0','-vf',','.join(vf),'-af',','.join(af),
                 '-t',str(duration),'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',
                 '-c:a','aac','-ar','48000','-ac','2',str(work/f'{i}.mp4')]
        run(args)
        progress(identifier,5+int((i+1)/len(p['clips'])*65))
    (work/'concat.txt').write_text('\n'.join(f"file '{i}.mp4'" for i in range(len(p['clips']))),encoding='utf-8')
    run(['-f','concat','-safe','1','-i','concat.txt','-c','copy','joined.mp4'],cwd=work)
    args=['-i',str(work/'joined.mp4')]
    for track in p['audio']:
        m=media_owned(track['media'],u['id'])
        if track['loop']: args+=['-stream_loop','-1']
        args+=['-ss',str(track['in']),'-protocol_whitelist','file,pipe','-f',demux(m['path']),'-i',str(core.DATA/m['path'])]
    vf=[]
    font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    fontarg=f'fontfile={font}:' if font.exists() else ''
    overlays=p['texts']+p['subtitles']
    if u['plan']=='free': overlays += [dict(text='FUMIST Studio',start=0,end=p['duration'],color='#ffffff',size=22,position='top')]
    for i,text in enumerate(overlays):
        if not text['text']: continue
        (work/f'text{i}.txt').write_text(text['text'],encoding='utf-8')
        y={'top':'h*0.06','center':'(h-th)/2','bottom':'h-th-h*0.10'}[text['position']]
        vf += [f"drawtext={fontarg}textfile=text{i}.txt:expansion=none:fontcolor={text['color']}:fontsize={text['size']*h/720}:x=(w-tw)/2:y={y}:box=1:boxcolor=black@0.4:boxborderw=10:enable='between(t,{text['start']},{text['end']})'"]
    if vf: args+=['-vf',','.join(vf)]
    if p['audio']:
        af=[]
        for i,track in enumerate(p['audio'],1):
            available=p['duration']-track['offset']
            if track['maxLength']: available=min(available,track['maxLength'])
            if not track['loop']:
                available=min(available,media_owned(track['media'],u['id'])['seconds']-track['in'])
            filters=[f'atrim=duration={available}', 'asetpts=PTS-STARTPTS', f'volume={track["volume"]}']
            if track['fadeIn']:
                filters.append(f'afade=t=in:d={min(track["fadeIn"],available)}')
            if track['fadeOut']:
                fade=min(track['fadeOut'],available)
                filters.append(f'afade=t=out:st={available-fade}:d={fade}')
            filters.append(f'adelay={int(track["offset"]*1000)}:all=1')
            af.append(f'[{i}:a]'+','.join(filters)+f'[a{i}]')
        af += ['[0:a]'+''.join(f'[a{i}]' for i in range(1,len(p['audio'])+1))+f'amix=inputs={len(p["audio"])+1}:duration=first:normalize=0,alimiter=limit=.95[mix]']
        args+=['-filter_complex',';'.join(af),'-map','0:v:0','-map','[mix]']
    else: args+=['-map','0:v:0','-map','0:a:0']
    destination=core.DATA/'exports'/f'{identifier}.mp4'
    args += ['-t',str(p['duration']),'-c:v','libx264' if vf else 'copy','-c:a','aac','-movflags','+faststart',str(destination)]
    run(args,cwd=work)
    progress(identifier,98)
    return {'download':f'/api/download/{identifier}','seconds':p['duration']}

@lru_cache(maxsize=1)
def caption_model(name):
    from faster_whisper import WhisperModel
    bundled = Path('/opt/whisper/base')
    source = str(bundled) if name == 'base' and bundled.is_dir() else name
    return WhisperModel(source, device='cpu', compute_type='int8', cpu_threads=2,
                        download_root=str(core.DATA/'models'))

def analysis(identifier,u,body,kind):
    m=media_owned(body.get('media'),u['id'])
    if not m['has_audio']: raise core.Error('no_audio')
    start=number(body.get('in',0),0,max(0,m['seconds']-.1))
    end=number(body.get('out',min(m['seconds'],u['limits']['seconds'])),start+.1,m['seconds'])
    if end-start>u['limits']['seconds']: raise core.Error('duration_limit',403)
    work=core.DATA/'work'/identifier
    work.mkdir(exist_ok=True)
    run(['-ss',str(start),'-protocol_whitelist','file,pipe','-f',demux(m['path']),'-i',str(core.DATA/m['path']),'-t',str(end-start),'-vn','-ar','16000','-ac','1',str(work/'audio.wav')])
    progress(identifier,25)
    if kind=='silence':
        proc=subprocess.run([FFMPEG,'-nostdin','-i',str(work/'audio.wav'),'-af','silencedetect=noise=-35dB:d=0.6','-f','null','-'],capture_output=True,timeout=180)
        if proc.returncode: raise core.Error('analysis_failed')
        silence_start=None; cursor=0; ranges=[]
        for line in proc.stderr.decode(errors='replace').splitlines():
            a=re.search(r'silence_start: ([0-9.]+)',line)
            b=re.search(r'silence_end: ([0-9.]+)',line)
            if a:
                silence_start=float(a.group(1))
                if silence_start-cursor>.15: ranges.append({'in':start+cursor,'out':start+silence_start})
            if b: cursor=float(b.group(1)); silence_start=None
        if silence_start is None and end-start-cursor>.15: ranges.append({'in':start+cursor,'out':end})
        return {'ranges':ranges[:60]}
    if not core.enabled('ENABLE_AI_TRANSCRIPTION'): raise core.Error('ai_not_configured',503)
    model=caption_model(core.setting('WHISPER_MODEL','base'))
    language=body.get('language') if body.get('language') in ('uz','ru','en') else None
    import numpy as np
    with wave.open(str(work/'audio.wav'), 'rb') as audio:
        samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype='<i2').astype(np.float32)
    samples /= 32768.0
    segments,info=model.transcribe(samples,language=language,vad_filter=True,beam_size=3)
    result=[{'start':round(s.start,2),'end':round(s.end,2),'text':s.text.strip(),'color':'#ffffff','size':40,'position':'bottom'} for s in segments]
    return {'subtitles':result[:150],'language':info.language}

def worker():
    while not STOP.wait(1):
        with core.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if not row: continue
            c.execute("UPDATE jobs SET status='running',progress=2 WHERE id=?",(row['id'],))
        try:
            u=core.by_id(row['user_id'])
            body=json.loads(row['body'])
            result=render(row['id'],u,validate(body,u)) if row['kind']=='render' else analysis(row['id'],u,body,row['kind'])
            with core.db() as c: c.execute("UPDATE jobs SET status='done',progress=100,result=? WHERE id=?",(json.dumps(result),row['id']))
        except Exception as exc:
            code=exc.code if isinstance(exc,core.Error) else 'processing_failed'
            print('Job failed',row['id'],type(exc).__name__)
            with core.db() as c: c.execute("UPDATE jobs SET status='failed',error=? WHERE id=?",(code,row['id']))
        finally: shutil.rmtree(core.DATA/'work'/row['id'],ignore_errors=True)

def enqueue(u,kind,body):
    if kind=='render': body=validate(body,u)
    elif kind in ('transcribe','silence'):
        m=media_owned(body.get('media'),u['id'])
        if not m['has_audio']: raise core.Error('no_audio')
        if kind=='transcribe' and not core.enabled('ENABLE_AI_TRANSCRIPTION'): raise core.Error('ai_not_configured',503)
    else: raise core.Error('invalid_job')
    with core.db() as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND status IN ('queued','running')",(u['id'],)).fetchone()[0]>=2:
            raise core.Error('job_pending',429)
        if c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=20: raise core.Error('queue_full',429)
        count=c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND kind=? AND created>? AND status!='failed'",(u['id'],kind,core.now()-86400)).fetchone()[0]
        if count>=u['limits']['exports' if kind=='render' else 'ai']: raise core.Error('daily_limit',429)
        identifier=core.uid()
        c.execute("INSERT INTO jobs(id,user_id,kind,body,status,created) VALUES(?,?,?,?,'queued',?)",(identifier,u['id'],kind,json.dumps(body),core.now()))
    return {'id':identifier,'status':'queued'}
