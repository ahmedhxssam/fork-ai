import { useEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';
import './JudgingTour.css';

const chapters = [
  {title:'One morning. Meals at stake.', label:'The mission', seconds:20, target:'.brief-resources, .playback', text:'You coordinate a food bank. Meals, vehicles and a four-hour window are fixed. Can you keep deliveries moving when a vehicle fails?', cue:'This is a synthetic rehearsal of a real operations problem.', next:'Next: compare plans'},
  {title:'Three plans. Equal starting conditions.',label:'Three plans',seconds:25,target:'.world-grid',text:'Velocity favors throughput, Resilience keeps flexibility, and Equity favors high-need destinations. All receive copies of the same scenario; none can borrow from another.',cue:'These are deterministic OR-Tools policies, not autonomous AI agents.',next:'Next: honest controls'},
  {title:'A fair test needs a control.',label:'Honest controls',seconds:15,target:'.controls-section',text:'Compare the named strategies with simple greedy routing and a neutral optimizer. A simple baseline can win. The displayed numbers are computed results, not a promise of improvement.',cue:'We keep the controls visible even when they beat our strategies.',next:'Next: shared breakdown'},
  {title:'Break the same vehicle.',label:'Shared breakdown',seconds:20,target:'.mission-title',text:'Apply one shared shock: vehicle A fails at 09:25 in every world. Completed deliveries stay delivered. Its cargo stays stranded; healthy vehicles can replan the remaining work.',cue:'The initial plans did not know this failure was coming.',next:'Apply shared breakdown'},
  {title:'What did recovery actually save?',label:'Measured recovery',seconds:30,target:'.split-evidence',text:'Now compare recovery against the same breakdown with the original routes locked. These measured differences can be positive, zero or negative. Reserve, stranded cargo and unmet demand remain visible.',cue:'The unshocked reference is different from the no-replanning control.',next:'Next: your priorities'},
  {title:'Better depends on your priorities.',label:'Your priorities',seconds:20,target:'.decision-section',text:'Choose the tradeoff: more on-time meals, high-need service, or lower modeled cost. Move a weight to update the recommendation from verified outcomes. A recommendation never approves itself.',cue:'You can try a priority, then wait for it to save before continuing.',next:'Next: independent referee'},
  {title:'Trust the receipt, not the pitch.',label:'Independent referee',seconds:30,target:'[data-tour="receipt"]',text:'A separate standard-library referee replays physical evidence and recomputes metrics. Inspect its checks and hashes. A physically valid plan may still leave people unserved.',cue:'The planner does not get to write its own authoritative score.',next:'Next: human decision'},
  {title:'The decision stays human.',label:'Human decision',seconds:20,target:'.approval-footer',text:'Review the selected plan and explicitly approve it if you choose. Approval binds this revision and saved preferences to a JSON or CSV export. It never dispatches vehicles or contacts anyone.',cue:'Substantial OpenAI Codex assistance built this demo; no model provider runs here.',next:'Finish tour'},
];

export interface JudgingTourProps {
  step:number; pace:number; startedAt:number; timer:RefObject<{pausedAt:number|null; pausedTotal:number}>; busy:boolean; error:string; ready:boolean; alreadyDisrupted:boolean;
  onNext:()=>void; onBack:()=>void; onRestart:()=>void; onExit:()=>void; onPace:(pace:number)=>void;
}
export default function JudgingTour({step,pace,startedAt,timer,busy,error,ready,alreadyDisrupted,onNext,onBack,onRestart,onExit,onPace}:JudgingTourProps){
  const chapter=chapters[step];
  const [elapsed,setElapsed]=useState(0);
  const [paused,setPaused]=useState(timer.current.pausedAt!==null);
  const panel=useRef<HTMLElement>(null);
  useEffect(()=>{setPaused(timer.current.pausedAt!==null);setElapsed(0)},[startedAt,timer]);
  useEffect(()=>{const update=()=>setElapsed(Math.max(0,Math.floor(((timer.current.pausedAt??Date.now())-startedAt-timer.current.pausedTotal)/1000)));update();const interval=setInterval(update,1000);return()=>clearInterval(interval)},[startedAt,timer]);
  function toggleTimer(){if(timer.current.pausedAt!==null){timer.current.pausedTotal+=Date.now()-timer.current.pausedAt;timer.current.pausedAt=null;setPaused(false)}else{timer.current.pausedAt=Date.now();setPaused(true)}}
  useEffect(()=>{
    let target:HTMLElement|null=null;
    const highlight=()=>{const current=document.querySelector<HTMLElement>(chapter.target);if(current!==target){target?.classList.remove('tour-highlight');target=current;target?.classList.add('tour-highlight')}};
    highlight();
    const observer=new MutationObserver(highlight);
    observer.observe(document.body,{childList:true,subtree:true});
    const timer=window.setTimeout(()=>{const scrollTarget=step===0?document.querySelector('.brief-main')??target:target;scrollTarget?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'})},80);
    panel.current?.focus({preventScroll:true});
    return()=>{clearTimeout(timer);observer.disconnect();target?.classList.remove('tour-highlight')};
  },[step,chapter.target]);
  useEffect(()=>{
    const handle=(event:KeyboardEvent)=>{
      const el=event.target as HTMLElement;
      if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(!busy)onExit();return}
      if(el.matches('input,textarea,select')||el.isContentEditable)return;
      if(event.key==='ArrowRight'&&!busy&&ready){event.preventDefault();onNext()}
      if(event.key==='ArrowLeft'&&!busy&&step>0){event.preventDefault();onBack()}
    };
    document.addEventListener('keydown',handle,true);return()=>document.removeEventListener('keydown',handle,true);
  },[busy,ready,step,onNext,onBack,onExit]);
  const format=(s:number)=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  return <aside ref={panel} tabIndex={-1} className="judging-tour" data-testid="judging-tour" data-step={step} aria-label="Guided judging tour">
    <div className="tour-top"><span><i/> JUDGING MODE <b>{step+1} / 8</b></span><button onClick={onExit} disabled={busy} aria-label="Exit tour">Exit ×</button></div>
    <div className="tour-pacing"><div className="tour-pace-switch" aria-label="Presentation pacing"><button aria-pressed={pace===180} onClick={()=>onPace(180)}>3 min guided</button><button aria-pressed={pace===120} onClick={()=>onPace(120)}>2 min quick</button></div><div className="tour-clock"><span>{format(elapsed)} elapsed · {format(Math.max(0,pace-elapsed))} left</span><button className="tour-timer-toggle" onClick={toggleTimer}>{paused?'Resume timer':'Pause timer'}</button></div></div>
    <ol className="tour-chapters" aria-label="Tour chapters">{chapters.map((item,index)=><li key={item.label} aria-current={step===index?'step':undefined} className={index<step?'complete':''} title={`${index+1}. ${item.label}`}><span>{index<step?'✓':index+1}</span><span>{item.label}</span></li>)}</ol>
    <div className="tour-story"><div className="tour-chapter-label">CHAPTER {String(step+1).padStart(2,'0')} <span>~{Math.round(chapter.seconds*pace/180)} sec · advance at your pace</span></div><h2>{chapter.title}</h2><p>{chapter.text}</p></div>
    {alreadyDisrupted&&step<4&&<p className="tour-wait">Reviewing an earlier chapter. The breakdown is already applied; outcome numbers still show the current disrupted run. Restart for a fresh mission.</p>}
    <details className="tour-presenter"><summary>Presenter cue</summary><p>{chapter.cue}</p></details>
    {error&&<p className="tour-error" role="alert">{error} Your place is saved. Try the action again.</p>}
    {!ready&&!busy&&<p className="tour-wait" role="status">{step===0?'Waiting for the scenario engine.':'Save or revert your priority changes to continue.'}</p>}
    <div className="tour-actions"><button className="tour-back" onClick={onBack} disabled={step===0||busy}>Back</button><button className="tour-next" onClick={onNext} disabled={busy||!ready}>{busy?<><span className="spinner"/> Computing…</>:<>{chapter.next} <span aria-hidden="true">→</span></>}</button></div>
    <div className="tour-bottom"><button onClick={onRestart} disabled={busy}>Restart tour</button><span>← → navigate · Esc exits</span></div>
  </aside>
}
