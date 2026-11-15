/** Generate local voice assets and editorial chrome. No provider, network or remote code. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH ||= path.join(root,'.cache/ms-playwright');
const require=createRequire(path.join(root,'frontend/package.json'));
const {chromium}=require('@playwright/test');
const work=process.env.FORK_MEDIA_WORK || '/private/tmp/fork-submission-media';
await fs.mkdir(work,{recursive:true});
const storyboard=JSON.parse(await fs.readFile(path.join(root,'scripts/media/storyboard.json'),'utf8'));
const engine=storyboard.voice_engine || 'say';
const digest=value=>createHash('sha256').update(value).digest('hex');
const normalize=text=>text.trim().replace(/\s+/g,' ');
let voiceManifest;
if(engine==='kokoro-onnx'){
 const python=process.env.FORK_TTS_PYTHON || path.join(root,'.cache/tts-venv/bin/python');
 try{await fs.access(python)}catch{throw Error(`Missing optional TTS Python: ${python}. Install scripts/media/requirements-voice.txt in the optional environment, or set FORK_TTS_PYTHON.`)}
 const result=execFileSync(python,[path.join(root,'scripts/media/narrate.py'),'--storyboard',path.join(root,'scripts/media/storyboard.json'),'--work-dir',work],{encoding:'utf8',maxBuffer:8*1024*1024,stdio:['ignore','pipe','inherit']});
 voiceManifest=JSON.parse(result);
 storyboard.narration=voiceManifest.narration;
}else if(engine==='say'){
 const macOS=execFileSync('/usr/bin/sw_vers',['-productVersion'],{encoding:'utf8'}).trim();
 const chapters=[];
 for(const c of storyboard.chapters){
  const audio=path.join(work,`${c.n}.aiff`),sidecar=path.join(work,`${c.n}.narration.json`),text=path.join(work,`${c.n}.txt`);
  const identity={engine:'say',voice:storyboard.voice,rate:storyboard.voice_rate,lang:storyboard.voice_lang||null,text:c.narration,model_sha256:null,voices_sha256:null,packages:{macOS},format:'AIFF',pipeline_revision:2};
  const signature=digest(JSON.stringify(identity));let cached=false;
  try{const meta=JSON.parse(await fs.readFile(sidecar,'utf8'));cached=meta.signature===signature&&meta.audio_sha256===digest(await fs.readFile(audio))}catch{}
  await fs.writeFile(text,c.narration);
  if(!cached)execFileSync('/usr/bin/say',['-v',storyboard.voice,'-r',String(storyboard.voice_rate),'-f',text,'-o',audio]);
  const speech_seconds=Number(execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',audio],{encoding:'utf8'}).trim());
  const meta={chapter:c.n,identity,signature,audio_file:`${c.n}.aiff`,audio_sha256:digest(await fs.readFile(audio)),speech_seconds,cache_hit:cached};
  await fs.writeFile(sidecar,JSON.stringify(meta,null,2)+'\n');chapters.push(meta);
 }
 storyboard.narration={engine:'say',voice:storyboard.voice,rate:storyboard.voice_rate,packages:{macOS},description:`Offline macOS ${storyboard.voice} system narration; a synthetic system voice, not the owner's voice.`,timing:'Proportional per-sentence estimates; not measured alignment.',assets:chapters.map(c=>({chapter:c.chapter,file:c.audio_file,sha256:c.audio_sha256,signature:c.signature,speech_seconds:c.speech_seconds}))};
 voiceManifest={narration:storyboard.narration,chapters};
 await fs.writeFile(path.join(work,'narration-manifest.json'),JSON.stringify(voiceManifest,null,2)+'\n');
}else throw Error(`Unsupported voice_engine: ${engine}. Use kokoro-onnx or omit it for legacy macOS say.`);
const overruns=[];
for(const c of storyboard.chapters){
 const meta=voiceManifest.chapters.find(x=>x.chapter===c.n);
 if(!meta)throw Error(`Missing narration manifest chapter ${c.n}`);
 const measured=Number(execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',path.join(work,meta.audio_file)],{encoding:'utf8'}).trim());
 if(!Number.isFinite(measured)||measured<=0||Math.abs(measured-meta.speech_seconds)>.01)throw Error(`Invalid or mismatched voice duration in chapter ${c.n}`);
 c.speech_seconds=measured;
 c.narration_audio={file:meta.audio_file,sha256:meta.audio_sha256,signature:meta.signature,cache_hit:meta.cache_hit};
 if(meta.sentence_timings){
  if(normalize(meta.sentence_timings.map(x=>x.text).join(' '))!==normalize(c.narration))throw Error(`Sentence captions do not match narration in chapter ${c.n}`);
  let end=0;for(const cue of meta.sentence_timings){if(!Number.isFinite(cue.start)||!Number.isFinite(cue.end)||cue.start<end-.001||cue.end<=cue.start||cue.end>measured+.001)throw Error(`Invalid sentence cue in chapter ${c.n}`);end=cue.end}
  c.sentence_timings=meta.sentence_timings;
 }else{
  const sentences=c.narration.match(/[^.!?]+[.!?]+|[^.!?]+$/g).map(x=>x.trim());const length=sentences.reduce((sum,x)=>sum+x.length,0);let at=0;
  c.sentence_timings=sentences.map(text=>{const start=at;at+=measured*text.length/length;return {text,start,end:at}});
 }
 console.log(`Chapter ${c.n}: ${measured.toFixed(2)}s voice / ${c.seconds}s planned (${engine}${meta.cache_hit?', cached':''})`);
 const maximum=c.seconds-(c.n===8?3:0)-.9;
 if(measured>maximum)overruns.push(`${c.n}: ${measured.toFixed(2)}s exceeds ${maximum.toFixed(2)}s`);
}
if(overruns.length)throw Error(`Narration exceeds the fixed footage budget: ${overruns.join('; ')}. Adjust authored narration or synthesis speed; the footage/outro were not changed.`);
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
const logo=await fs.readFile(path.join(root,'frontend/public/fork-wordmark.svg'),'utf8');
const logoUrl='data:image/svg+xml;base64,'+Buffer.from(logo).toString('base64');
let start=0;const captions=[];
for(const c of storyboard.chapters){
 c.start=start;c.end=start+c.seconds;start=c.end;
 for(const cue of c.sentence_timings)captions.push({start:c.start+.65+cue.start,end:c.start+.65+cue.end,text:cue.text});
 const pips=storyboard.chapters.map(x=>`<i class="${x.n===c.n?'active':x.n<c.n?'done':''}"></i>`).join('');
 await page.setContent(`<!doctype html><style>
 *{box-sizing:border-box}html,body{margin:0;background:transparent;width:1920px;height:1080px;font-family:Arial,sans-serif;color:#17221D}.left{position:absolute;inset:0 auto 0 0;width:276px;background:#F7F7F2}.top{position:absolute;left:276px;top:0;right:0;height:96px;background:#F7F7F2}.bottom{position:absolute;left:276px;bottom:0;right:0;height:80px;background:#F7F7F2}.right{position:absolute;right:0;top:96px;bottom:80px;width:32px;background:#F7F7F2}.wordmark{position:absolute;left:36px;top:30px;font-size:43px;font-weight:900;letter-spacing:-3px}.wordmark b{color:#5C7658}.edition{position:absolute;top:40px;right:42px;font-size:16px;letter-spacing:2px;font-weight:700}.chapter{position:absolute;top:140px;left:36px;width:214px}.number{font-size:95px;letter-spacing:-6px;line-height:1;font-weight:800;color:#5C7658}.eyebrow{font-size:12px;font-weight:700;letter-spacing:2px;margin:24px 0 20px;line-height:1.8}.title{font-size:32px;line-height:1.16;font-weight:700;letter-spacing:-1px;margin:0 0 38px}.points{padding:0;list-style:none}.points li{font-size:17px;line-height:1.4;padding:14px 0;border-top:1px solid #cad1bc;display:flex;gap:10px}.points span{font-weight:bold;color:#5C7658;font-size:13px;padding-top:3px}.bottomnote{position:absolute;left:36px;bottom:34px;width:210px;font-size:12px;line-height:1.6;color:#5c6b5d;letter-spacing:.5px}.pips{position:absolute;left:36px;bottom:138px;display:flex;gap:7px}.pips i{width:19px;height:5px;border-radius:5px;background:#D8E4D0}.pips .done{background:#a7b5a0}.pips .active{background:#5C7658}.head{position:absolute;left:316px;top:38px;font-size:19px;font-weight:700;letter-spacing:.4px}.time{position:absolute;left:36px;bottom:163px;font-size:13px;color:#52664f;letter-spacing:1px}.screen-border{position:absolute;left:287px;top:103px;width:1602px;height:891px;border:1px solid #b5c2aa;box-shadow:0 8px 20px #1c2e1f14;pointer-events:none}.footer{position:absolute;left:316px;bottom:28px;font-size:14px;color:#53604f;letter-spacing:.7px}
 </style><div class="left"></div><div class="top"></div><div class="bottom"></div><div class="right"></div><img class="wordmark" src="${logoUrl}" width="210" height="51" alt="FORK"><div class="edition">REAL PRODUCT DEMO · SYNTHETIC DATA</div><div class="chapter"><div class="number">${String(c.n).padStart(2,'0')}</div><div class="eyebrow">${c.label}</div><h1 class="title">${c.title}</h1><ul class="points">${c.points.map((p,i)=>`<li><span>0${i+1}</span>${p}</li>`).join('')}</ul></div><div class="head">${String(c.n).padStart(2,'0')} / 08 &nbsp; ${c.label}</div><div class="screen-border"></div><div class="time">${String(Math.floor(c.start/60)).padStart(2,'0')}:${String(c.start%60).padStart(2,'0')} — ${String(Math.floor(c.end/60)).padStart(2,'0')}:${String(c.end%60).padStart(2,'0')}</div><div class="pips">${pips}</div><div class="bottomnote">DETERMINISTIC PLANNER<br>Human approval · No dispatch</div>`);
 await page.screenshot({path:path.join(work,`plate-${c.n}.png`),omitBackground:true});
}
await page.setContent(`<!doctype html><style>html,body{margin:0;width:1920px;height:1080px;background:transparent}img{position:absolute;width:420px;height:auto;left:750px;top:490px}</style><img src="${logoUrl}" alt="FORK">`);
await page.evaluate(async()=>{const img=document.querySelector('img');await img.decode();const canvas=document.createElement('canvas');canvas.width=300;canvas.height=72;const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0,300,72);const a=ctx.getImageData(0,0,300,72).data;let l=300,r=0,t=72,b=0;for(let y=0;y<72;y++)for(let x=0;x<300;x++)if(a[(y*300+x)*4+3]>8){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y)}img.style.left=(960-(l+r)*.7)+'px';img.style.top=(540-(t+b)*.7)+'px'});
await page.screenshot({path:path.join(work,'outro-logo.png'),omitBackground:true});
await browser.close();
await fs.writeFile(path.join(work,'storyboard.json'),JSON.stringify(storyboard,null,2));
await fs.writeFile(path.join(root,'artifacts/FORK-submission-demo-storyboard.json'),JSON.stringify(storyboard,null,2));
const stamp=t=>{const m=Math.round(t*1000);return `${String(Math.floor(m/3600000)).padStart(2,'0')}:${String(Math.floor(m/60000)%60).padStart(2,'0')}:${String(Math.floor(m/1000)%60).padStart(2,'0')},${String(m%1000).padStart(3,'0')}`};
await fs.writeFile(path.join(root,'artifacts/FORK-submission-demo.srt'),captions.map((c,i)=>`${i+1}\n${stamp(c.start)} --> ${stamp(c.end)}\n${c.text}\n`).join('\n'));
await fs.writeFile(path.join(root,'artifacts/FORK-submission-demo-transcript.txt'),`FORK submission demo\nNarration: ${storyboard.narration.description}\nActual local UI; synthetic data; Deterministic Planner Mode.\n\n`+storyboard.chapters.map(c=>`${String(c.n).padStart(2,'0')} · ${c.start}s–${c.end}s · ${c.title}\n${c.narration}\n`).join('\n'));
console.log(JSON.stringify(storyboard.chapters.map(c=>({chapter:c.n,planned:c.seconds,speech:c.speech_seconds})),null,2));
