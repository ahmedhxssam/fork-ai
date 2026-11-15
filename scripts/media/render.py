#!/usr/bin/env python3
"""Compose truthful FORK recording + separate brand chapter rail. Standard library only.
Requires local ffmpeg/ffprobe and assets created by prepare.mjs / record-judging.mjs.
"""
import hashlib,json,os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=pathlib.Path(os.environ.get('FORK_MEDIA_WORK','/private/tmp/fork-submission-media'))
OUT=ROOT/'artifacts/FORK-submission-demo.mp4'
STORY=json.loads((WORK/'storyboard.json').read_text())
EVIDENCE=json.loads((ROOT/'artifacts/FORK-submission-demo-evidence.json').read_text())
def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=(WORK/'render.log').open('a'))
def ass_time(v):
    cs=round(v*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
ASS='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial,25,&H001D2217,&H001D2217,&H00F2F7F7,&H00F2F7F7,0,0,0,0,100,100,0,0,1,2,0,2,310,45,22,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
import re
def sentence_cues(chapter):
    """Prefer measured local sentence boundaries; retain legacy storyboard support."""
    cues=chapter.get('sentence_timings')
    if cues:
        assert ' '.join(c['text'] for c in cues)==' '.join(chapter['narration'].split()),'Caption text differs from narration'
        previous=0
        for cue in cues:
            assert previous<=cue['start']<cue['end']<=chapter['speech_seconds']+.001,cue
            previous=cue['end']
        return cues
    sentences=[s.strip() for s in re.findall(r'[^.!?]+[.!?]+',chapter['narration'])]
    count=sum(map(len,sentences));at=0;cues=[]
    for sentence in sentences:
        end=at+chapter['speech_seconds']*len(sentence)/count
        cues.append({'text':sentence,'start':at,'end':end});at=end
    return cues
source_probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(WORK/'screen.webm')]))
source_video=next(s for s in source_probe['streams'] if s['codec_type']=='video')
assert (source_video['width'],source_video['height'])==(2880,1600),source_video
EVIDENCE['capture']['verified_video']={k:source_video.get(k) for k in ['codec_name','width','height','r_frame_rate']}
segments=[]
for c in STORY['chapters']:
    cues=sentence_cues(c);events=[]
    for cue in cues:
        events.append(f'Dialogue: 0,{ass_time(.65+cue["start"])},{ass_time(.65+cue["end"])},Default,,0,0,0,,{cue["text"]}')
    at=.65+c['speech_seconds']
    caption=WORK/f"caption-{c['n']}.ass";caption.write_text(ASS+'\n'.join(events)+'\n')
    # The final three seconds are a logo-only outro; the native workflow remains in the source.
    duration=c['seconds']-(3 if c['n']==8 else 0)
    if at>duration-.25:raise RuntimeError(f'Voice overlaps picture tail in chapter {c["n"]}: {at} > {duration}')
    video=WORK/f"chapter-{c['n']}.mp4";segments.append(video)
    graph=(f'[0:v]setpts=PTS-STARTPTS,lutyuv=y=val+1:u=val+2:v=val+1,scale=1600:889:flags=lanczos:in_color_matrix=bt601:in_range=tv,format=rgba,pad=1920:1080:288:104:color=0xF7F7F2,fps=30:start_time=0,setsar=1[app];'
           f'[app][1:v]overlay=0:0:format=rgb,subtitles={caption.as_posix()},scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v];'
           f'[2:a]adelay=650,apad,atrim=duration={duration},loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000[a]')
    run(['ffmpeg','-y','-ss',str(EVIDENCE['lead_seconds']+c['start']),'-i',str(WORK/'screen.webm'),'-loop','1','-i',str(WORK/f"plate-{c['n']}.png"),'-i',str(WORK/f"{c['n']}.aiff"),'-filter_complex',graph,'-map','[v]','-map','[a]','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-x264-params','colorprim=bt709:transfer=bt709:colormatrix=bt709','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','160k','-ar','48000','-ac','1','-video_track_timescale','15360',str(video)])
    print(f'Rendered chapter {c["n"]}: {duration}s',flush=True)
# A small opacity/position settle gives the single native mark a quiet animated close.
logo=WORK/'outro-logo.png'
if not logo.exists():raise RuntimeError('Missing outro logo PNG; run prepare.mjs after brand assets are present.')
outro=WORK/'outro.mp4';segments.append(outro)
graph=r'[0:v]format=rgba[bg];[1:v]format=rgba,fade=t=in:st=0.1:d=0.7:alpha=1,fade=t=out:st=2.7:d=0.3:alpha=1[logo];[bg][logo]overlay=0:12*(1-min(t/1.0\,1)):format=rgb,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]'
run(['ffmpeg','-y','-f','lavfi','-i','color=c=0xF7F7F2:s=1920x1080:r=30:d=3','-loop','1','-i',str(logo),'-f','lavfi','-i','anullsrc=r=48000:cl=mono','-filter_complex',graph,'-map','[v]','-map','2:a','-t','3','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-x264-params','colorprim=bt709:transfer=bt709:colormatrix=bt709','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','160k','-video_track_timescale','15360',str(outro)])
concat=WORK/'concat.txt';concat.write_text(''.join(f"file '{s}'\n" for s in segments))
run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(OUT)])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(OUT)]))
run(['ffmpeg','-v','error','-i',str(OUT),'-f','null','-'])
video_stream=next(s for s in probe['streams'] if s['codec_type']=='video')
audio_stream=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert video_stream['codec_name']=='h264' and video_stream['pix_fmt']=='yuv420p'
assert (video_stream['width'],video_stream['height'])==(1920,1080)
assert video_stream['r_frame_rate']=='30/1' and video_stream['avg_frame_rate']=='30/1'
assert int(video_stream['nb_frames'])==3450
assert audio_stream['codec_name']=='aac' and int(audio_stream['sample_rate'])==48000
assert abs(float(probe['format']['duration'])-115)<.1 and float(probe['format']['duration'])<=120
audio_check=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(OUT),'-af','volumedetect,silencedetect=noise=-45dB:d=0.7','-f','null','-'],check=True,capture_output=True,text=True).stderr
(WORK/'audio-check.log').write_text(audio_check)
assert 'mean_volume:' in audio_check and 'max_volume: -inf' not in audio_check
for c in STORY['chapters']:
    t=c['start']+({3:10,4:5,7:11,8:9}.get(c['n'],5))
    run(['ffmpeg','-y','-ss',str(t),'-i',str(OUT),'-frames:v','1',str(ROOT/f"docs/assets/presentation/chapter-{c['n']:02}-final.png")])
run(['ffmpeg','-y','-ss','113.5','-i',str(OUT),'-frames:v','1',str(ROOT/'docs/assets/presentation/outro-final.png')])
run(['ffmpeg','-y','-i',str(OUT),'-vf','fps=1/5,scale=384:216,tile=5x5','-frames:v','1',str(ROOT/'docs/assets/presentation/contact-sheet.jpg')])
run(['ffmpeg','-y','-i',str(OUT),'-vf','fps=1,scale=240:135,tile=10x12','-frames:v','1',str(ROOT/'docs/assets/presentation/contact-sheet-1fps.jpg')])
for t,label in [(0.1,'opening'),(114.8,'ending')]:
    run(['ffmpeg','-y','-ss',str(t),'-i',str(OUT),'-frames:v','1',str(ROOT/f'docs/assets/presentation/{label}-final.png')])
EVIDENCE.update({'delivery':{'duration_seconds':float(probe['format']['duration']),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','pix_fmt','r_frame_rate','avg_frame_rate','nb_frames','sample_rate','channels','color_space','color_transfer','color_primaries']} for s in probe['streams']],'complete_decode':'passed','audio_measurement_log':str(WORK/'audio-check.log'),'final_frame_checks':'pending visual inspection'},'color_pipeline':{'purpose':'Media format correction only; UI layout, labels, scenario and results are unmodified. Raw browser video and native PNGs are retained.','browser_input':'Untagged VP8 interpreted as BT.601 limited range; Y+1/U+2/V+1 neutral-patch capture calibration against retained PNG.','working_canvas':'RGBA; overlays and captions composited in RGB.','delivery':'Explicit RGB to BT.709 limited-range YUV420 conversion, with matching H.264 VUI tags.'},'source_hashes':{'screen.webm':sha(WORK/'screen.webm'),'storyboard.json':sha(ROOT/'scripts/media/storyboard.json')},'outro':'Final 3 seconds: native FORK mark and wordmark, opacity and 12px position settle.'})
EVIDENCE['delivery']['frames']=int(video_stream['nb_frames'])
EVIDENCE['delivery']['average_frame_rate']=video_stream['avg_frame_rate']
if STORY.get('narration'):
    EVIDENCE['narration']=STORY['narration']
EVIDENCE.pop('visual_review',None)
EVIDENCE['captions']={'exact_text_matches_authored_narration':True,'sentence_cue_timing':'Measured sentence-group synthesis boundaries with explicit inter-group pauses; not word alignment.' if STORY.get('narration',{}).get('engine')=='kokoro-onnx' and all(c.get('sentence_timings') for c in STORY['chapters']) else 'Proportional sentence timing within measured audio; not measured sentence alignment.','burned_in':True,'sidecar':'artifacts/FORK-submission-demo.srt'}
if EVIDENCE.get('downloaded_guidance'):
    EVIDENCE['downloaded_guidance']['use']='Reviewed story/capture/editing guidance. No implementation scripts or dependencies from that guidance repository, external voice/music APIs or advisory AI judge were executed. Kokoro is a separately credited local narration dependency.'
EVIDENCE['production_code']={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/media/render.py',ROOT/'scripts/media/prepare.mjs',ROOT/'scripts/media/storyboard.json',ROOT/'scripts/media/narrate.py',ROOT/'frontend/scripts/record-judging.mjs'] if p.exists()}
EVIDENCE['audio_measurements']={key:float(re.search(rf'{key}: ([\-0-9.]+) dB',audio_check).group(1)) for key in ['mean_volume','max_volume']}
color_checks=[]
for label,t,x,y in [('chapter_rail',5,10,200),('native_app_paper',5,344,326),('outro_paper',113.5,100,100)]:
    pixel=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(OUT),'-vf',f'format=rgb24,crop=1:1:{x}:{y}','-frames:v','1','-f','rawvideo','-'])
    rgb=list(pixel[:3]);delta=[abs(a-b) for a,b in zip(rgb,[247,247,242])]
    assert max(delta)<=3,(label,rgb,delta)
    color_checks.append({'patch':label,'time_seconds':t,'position':[x,y],'decoded_rgb':rgb,'reference_rgb':[247,247,242],'max_channel_error':max(delta)})
EVIDENCE['color_pipeline']['decoded_neutral_patch_checks']=color_checks
(ROOT/'artifacts/FORK-submission-demo-evidence.json').write_text(json.dumps(EVIDENCE,indent=2)+'\n')
(WORK/'ffprobe.json').write_text(json.dumps(probe,indent=2))
print(json.dumps(EVIDENCE['delivery'],indent=2))
