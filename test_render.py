"""Real codec integration test. Runs in the deployment image with FFmpeg installed."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import core
import engine

@unittest.skipUnless(shutil.which(engine.FFMPEG) and shutil.which(engine.FFPROBE),'FFmpeg not installed on this host')
class RenderIntegration(unittest.TestCase):
    def test_video_image_music_text_and_export(self):
        old=core.DATA
        with tempfile.TemporaryDirectory() as folder:
            try:
                core.DATA=Path(folder);core.init();u=core.register('render_test','render-test-password')
                engine.run(['-f','lavfi','-i','testsrc2=size=320x240:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(core.DATA/'media'/'video.mp4')])
                engine.run(['-f','lavfi','-i','color=c=green:size=320x240','-frames:v','1',str(core.DATA/'media'/'image.png')])
                engine.run(['-f','lavfi','-i','sine=frequency=220:sample_rate=48000','-t','3',str(core.DATA/'media'/'music.wav')])
                ids=[]
                for name in ['video.mp4','image.png','music.wav']:
                    identifier=core.uid();ids.append(identifier);info=engine.probe(core.DATA/'media'/name)
                    with core.db() as c:c.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?,?,?)',(identifier,u['id'],name,info['kind'],'media/'+name,info['seconds'],info['width'],info['height'],info['has_audio'],123,core.now()))
                p={'ratio':'9:16','resolution':720,'fps':24,'clips':[
                    {'media':ids[0],'in':.2,'out':1.2,'speed':2,'rotation':90,'flip':True,'fade':.1,'filter':'warm'},
                    {'media':ids[1],'in':0,'out':.5,'speed':1,'filter':'mono'}],
                    'audio':[{'media':ids[2],'volume':.2,'in':0,'offset':0,'loop':True}],
                    'texts':[{'text':"O'zbekcha: 100% - test 'quote'",'start':0,'end':1,'color':'#ffffff','size':40,'position':'center'}],
                    'subtitles':[{'text':'Subtitle test','start':0,'end':1,'size':30,'position':'bottom','color':'#ffffff'}]}
                identifier=core.uid();result=engine.render(identifier,u,engine.validate(p,u))
                output=core.DATA/'exports'/f'{identifier}.mp4';info=engine.probe(output)
                self.assertTrue(output.stat().st_size>1000)
                self.assertEqual((info['width'],info['height']),(720,1280))
                self.assertAlmostEqual(info['seconds'],1,delta=.15)
                self.assertTrue(info['has_audio']);self.assertEqual(result['download'],f'/api/download/{identifier}')
                analysis=engine.analysis(core.uid(),u,{'media':ids[0],'in':0,'out':1},'silence')
                self.assertEqual(len(analysis['ranges']),1)
            finally:core.DATA=old

if __name__=='__main__':unittest.main()

