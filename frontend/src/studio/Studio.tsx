import { useEffect, useRef, useState } from 'react';
import { request, RequestError } from './api';
import type { Answer, Intake, Experiment, Model, Outage, Template, Weights, World } from './types';
import './studio.css';
import Conversation from './Conversation';
import type {Turn} from './Conversation';

const DRAFT='fork-studio-conversation-draft-v1',POINTER='fork-studio-experiment';
type Draft={version:1;brief:string;experimentId?:string;events?:Outage[];weights?:Weights;answers?:Answer[];turns?:Turn[];submitted?:boolean;answer?:string;legacy?:boolean};
function readDraft():Draft|null{try{return (()=>{const value=JSON.parse(localStorage.getItem(DRAFT)||'null');return value?.version===1?value:null})()}catch{return null}}
function savedId(){try{return localStorage.getItem(POINTER)}catch{return null}}
function write(key:string,value:string){try{localStorage.setItem(key,value)}catch{/* browser storage may be unavailable */}}
const money=(cents:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(cents/100);
const equal=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
const weightNames={completion:'On-time completion',priority:'Priority deadlines',cost:'Lower resource cost'} as const;
const policyDescriptions:Record<string,string>={throughput:'Shortest remaining work first, then deadlines and declared task value.',resilience:'Least deadline slack first, then shorter work to seek buffer.',priority:'Highest priority first, then deadlines and remaining work.'};
function Arrow(){return <span aria-hidden="true">↗</span>}
function ForkMark(){return <svg width="25" height="29" viewBox="0 0 25 29" fill="none" aria-hidden="true"><path d="M6 27V15C6 9 19 13 19 5M6 15V3M2 7L6 3L10 7M15 7L19 3L23 7" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/></svg>}

function Gantt({world,model,minute,compact=false}:{world:World;model:Model;minute:number;compact?:boolean}){
  const tasks=compact?model.tasks.slice(0,6):model.tasks;
  const completed=new Map(world.completions.map(item=>[item.task_id,item.time]));
  return <div className={`st-gantt ${compact?'st-gantt-compact':''}`} aria-label={`${world.name} computed work schedule`}>
    <div className="st-gantt-axis"><span>0m</span><span>{Math.round(model.horizon/2)}m</span><span>{model.horizon}m</span></div>
    {tasks.map(task=><div className="st-gantt-row" key={task.id}>
      <span title={task.label} className="st-task-label">{task.label}</span>
      <div className="st-track">
        {model.events.map(event=><span className="st-outage-zone" key={event.id} title={`${event.label}: ${event.at}–${Math.min(event.at+event.duration,model.horizon)}m`} style={{left:`${event.at/model.horizon*100}%`,width:`${Math.min(event.duration,model.horizon-event.at)/model.horizon*100}%`}}/>)}
        <span className="st-deadline" style={{left:`${task.due/model.horizon*100}%`}} title={`Due ${task.due}m`}/>
        {world.segments.filter(segment=>segment.task_id===task.id&&segment.start<minute).map((segment,index)=><span className="st-work-segment" key={`${segment.start}-${index}`} title={`${task.label} · ${segment.resource_id} · ${segment.start}–${segment.end}m · ${segment.units} units`} style={{left:`${segment.start/model.horizon*100}%`,width:`${(Math.min(segment.end,minute)-segment.start)/model.horizon*100}%`}}/>)}
        <span className="st-playhead" style={{left:`${minute/model.horizon*100}%`}}/>
      </div><span className="st-task-state">{completed.has(task.id)&&completed.get(task.id)!<=minute?'✓':'·'}</span>
    </div>)}
    {compact&&model.tasks.length>6&&<p className="st-small">+ {model.tasks.length-6} tasks in detailed trace</p>}
  </div>
}

export default function Studio(){
  const initial=useRef(readDraft());
  const [brief,setBrief]=useState(initial.current?.brief??'');
  const [templates,setTemplates]=useState<Template[]>([]);
  const [templatesError,setTemplatesError]=useState('');
  const [compilation,setCompilation]=useState<Intake|null>(null);
  const [compiledBrief,setCompiledBrief]=useState('');
  const [answers,setAnswers]=useState<Answer[]>(initial.current?.answers??[]);
  const [turns,setTurns]=useState<Turn[]>(initial.current?.turns??[]);
  const [answer,setAnswer]=useState(initial.current?.answer??'');
  const [submitted,setSubmitted]=useState(initial.current?.submitted??false);
  const [editing,setEditing]=useState(false);
  const [legacy,setLegacy]=useState(initial.current?.legacy??false);
  const [experimentBrief,setExperimentBrief]=useState('');
  const authoringEpoch=useRef(0);
  const touched=useRef(initial.current!==null);
  const [acceptedModel,setAcceptedModel]=useState(false);
  const [authoringDirty,setAuthoringDirty]=useState(false);
  const [experiment,setExperiment]=useState<Experiment|null>(null);
  const [pointer,setPointer]=useState(savedId);
  const [outages,setOutages]=useState<Outage[]>(initial.current?.events??[]);
  const [weights,setWeights]=useState<Weights>(initial.current?.weights??{completion:.5,priority:.35,cost:.15});
  const [selected,setSelected]=useState('throughput');
  const [minute,setMinute]=useState(0);
  const [playing,setPlaying]=useState(false);
  const [busy,setBusy]=useState('');
  const operation=useRef(false);
  const [error,setError]=useState('');
  const [uncertain,setUncertain]=useState(false);
  const retry=useRef<(()=>void)|null>(null);
  const [notice,setNotice]=useState('');
  const [modelVisible,setModelVisible]=useState(false);
  const [copied,setCopied]=useState(false);
  const [receipt,setReceipt]=useState(false);
  const resultsRef=useRef<HTMLElement>(null);
  const model=compilation?.model;
  const compileStale=compilation!==null&&brief!==compiledBrief;
  const replayStale=!!experiment?.authoring&&(!compilation?.ready||compilation.model_hash!==experiment.authoring.model_hash);
  const briefStale=!!experiment&&(replayStale||authoringDirty||editing||brief!==experimentBrief||(!legacy&&!equal(answers,experiment.authoring?.answers??[])));
  const eventsDirty=!!experiment&&!equal(outages,experiment.model.events);
  const preferencesDirty=!!experiment&&!equal(weights,experiment.comparison.weights);
  const stale=briefStale||eventsDirty||preferencesDirty||uncertain;
  const validBrief=!!brief.trim()&&compilation?.ready&&!!model&&!compileStale&&!editing&&!legacy&&acceptedModel;
  const currentWorld=experiment?.worlds.find(world=>world.id===selected)??experiment?.worlds[0];
  const currentApproved=!!experiment?.approved&&experiment.approved.revision===experiment.revision&&experiment.approved.world_id===currentWorld?.id&&!stale&&!busy;
  const simplified=!!experiment?.authoring;
  const weightSum=weights.completion+weights.priority+weights.cost;

  const loadTemplates=async()=>{setTemplatesError('');try{const data=await request<{prompts:Template[]}>('/prompts');setTemplates(data.prompts);if(!touched.current&&data.prompts[0]){setBrief(data.prompts[0].brief);initial.current={version:1,brief:data.prompts[0].brief}}}catch(err){setTemplatesError(String(err instanceof Error?err.message:err))}};
  useEffect(()=>{void loadTemplates();if(initial.current?.submitted&&!initial.current.legacy&&initial.current.brief.trim())interview(initial.current.answers??[],initial.current.turns??[],true)},[]);
  useEffect(()=>{write(DRAFT,JSON.stringify({version:1,brief,answers,turns,submitted,answer,legacy,experimentId:experiment?.id??initial.current?.experimentId,events:outages,weights}))},[brief,answers,turns,submitted,answer,legacy,outages,weights,experiment?.id]);
  useEffect(()=>{if(!playing||!experiment)return;const timer=window.setInterval(()=>setMinute(value=>{if(value>=experiment.model.horizon){setPlaying(false);return value}return Math.min(experiment.model.horizon,value+Math.max(1,Math.round(experiment.model.horizon/100)))}),180);return()=>clearInterval(timer)},[playing,experiment]);

  async function perform(label:string,action:(key:string)=>Promise<void>,mutation=false,key=crypto.randomUUID()){
    if(operation.current)return;
    operation.current=true;setBusy(label);if(!uncertain)setError('');setNotice('');
    retry.current=()=>void perform(label,action,mutation,key);
    try{await action(key);if(!uncertain)retry.current=null}catch(err){setError(err instanceof Error?err.message:String(err));if(mutation)setUncertain(true)}finally{operation.current=false;setBusy('')}
  }
  function accept(data:Experiment,resetDraft=true){
    setExperimentBrief(data.authoring?data.brief:(data.display_brief??data.brief));
    setUncertain(false);setError('');retry.current=null;setExperiment(data);setSelected(value=>data.worlds.some(world=>world.id===value)?value:data.worlds[0]?.id??'throughput');
    if(resetDraft){setOutages(data.model.events);setWeights(data.comparison.weights)}
    write(POINTER,data.id);setPointer(data.id);setMinute(data.model.horizon);setPlaying(false);
  }
  function invalidateAuthoring(){authoringEpoch.current++;setAuthoringDirty(true);retry.current=null;setAcceptedModel(false);setCompilation(null);setCompiledBrief('');setModelVisible(false);if(!uncertain)setError('');}
  function editBrief(value:string){touched.current=true;invalidateAuthoring();setBrief(value);setAnswers([]);setTurns([]);setAnswer('');setSubmitted(false);setLegacy(false);setNotice('Issue changed. Earlier answers and assumptions need confirming again.');}
  function interview(nextAnswers=answers,nextTurns=turns,preserveAnswer=false){
    const epoch=authoringEpoch.current,source=brief;setSubmitted(true);setEditing(false);
    void perform('Understanding scenario',async()=>{const result=await request<Intake>('/intake',{brief:source,answers:nextAnswers}).catch(err=>{if(epoch!==authoringEpoch.current)return null;throw err});if(!result||epoch!==authoringEpoch.current)return;setCompilation(result);setCompiledBrief(source);if(experiment&&source===experimentBrief&&equal(result.accepted_answers,experiment.authoring?.answers)&&result.ready)setAuthoringDirty(false);setAnswers(result.accepted_answers);setTurns(nextTurns.slice(0,result.accepted_answers.length));setModelVisible(false);setAcceptedModel(false);if(!preserveAnswer&&result.accepted_answers.length===nextAnswers.length)setAnswer('');setNotice(result.ready?'Review what will be simulated and accept its limits.':'One detail at a time. Your answers become inspectable model inputs.');});
  }
  function editOriginal(){invalidateAuthoring();setAnswers([]);setTurns([]);setEditing(true);setNotice('Changing the original issue clears dependent answers.');}
  function submitAnswer(value=answer){const question=compilation?.questions[0];if(!question||!value.trim())return;if(question.id.endsWith(':scope')&&value==='revise'){editOriginal();return}setAnswer(value);interview([...answers,{question_id:question.id,answer:value}],[...turns,{question_id:question.id,prompt:question.prompt,answer:value,display_answer:question.choices.find(choice=>choice.value===value)?.label}]);}
  function editAnswer(index:number){const previous=turns[index];invalidateAuthoring();setAnswers(answers.slice(0,index));setTurns(turns.slice(0,index));setAnswer(previous?.answer??'');setNotice('Later answers were cleared. Confirm this answer and the remaining assumptions again.');interview(answers.slice(0,index),turns.slice(0,index),true);}
  function launch(){if(!validBrief||!model||!compilation?.model_hash)return;void perform('Computing three futures',async key=>{
    const data=await request<Experiment>('/experiments',{brief,model,model_hash:compilation.model_hash,authoring:{method:'conversation',answers,brief_hash:compilation.brief_hash}},key);accept(data);setAuthoringDirty(false);setReceipt(false);setNotice('Three deterministic schedules computed and independently checked.');window.setTimeout(()=>resultsRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),80)
  })}
  function resume(){if(!pointer)return;const epoch=authoringEpoch.current;void perform('Restoring saved experiment',async()=>{
    let data:Experiment;try{data=await request<Experiment>(`/experiments/${pointer}`)}catch(err){if(err instanceof RequestError&&err.status===404){try{localStorage.removeItem(POINTER)}catch{/* unavailable */}setPointer(null)}throw err}
    if(epoch!==authoringEpoch.current)return;const draft=readDraft();accept(data);setAuthoringDirty(false);const restored=draft?.experimentId===data.id?draft:null;
    const natural=!!data.authoring;const source=natural?data.brief:(data.display_brief??'Saved workflow. Review the existing futures below.');
    setBrief(restored?.brief??source);setLegacy(!natural);setSubmitted(true);setEditing(false);setAcceptedModel(false);
    if(restored?.events)setOutages(restored.events);if(restored?.weights)setWeights(restored.weights);
    if(natural){const history=restored?.answers??data.authoring!.answers;setAnswers(history);setTurns(restored?.turns??history.map((item,i)=>({...item,prompt:`Clarification ${i+1}`})));const result=await request<Intake>('/intake',{brief:restored?.brief??source,answers:history});if(epoch!==authoringEpoch.current)return;setCompilation(result);setCompiledBrief(restored?.brief??source)}else{setAnswers([]);setTurns([]);setCompilation(null);setCompiledBrief('')}
    setNotice('Saved experiment restored. Authoring describes the original plan; applied outages appear in the current run evidence. Unsaved edits remain drafts.');
  })}
  function reload(){if(!experiment)return;void perform('Reloading saved revision',async()=>{const data=await request<Experiment>(`/experiments/${experiment.id}`);accept(data);setNotice('Saved revision restored; pending outage and preference edits reverted.');})}
  function applyEvents(){if(!experiment||briefStale)return;void perform('Rerunning with outages',async key=>{const data=await request<Experiment>(`/experiments/${experiment.id}/events`,{revision:experiment.revision,events:outages},key);accept(data);setNotice('Outages applied. A new counterfactual run starts from minute zero.');},true)}
  function savePreferences(){if(!experiment||weightSum<=0)return;void perform('Saving preferences',async key=>{const data=await request<Experiment>(`/experiments/${experiment.id}/preferences`,{revision:experiment.revision,weights},key);accept(data);setNotice('Preferences saved. Review the new revision before approving.');},true)}
  function approve(){if(!experiment||!currentWorld||stale||!currentWorld.verification.valid)return;void perform('Approving selected future',async key=>{const data=await request<Experiment>(`/experiments/${experiment.id}/approve`,{revision:experiment.revision,world_id:currentWorld.id},key);accept(data);setNotice('Approval bound to this revision and independent evidence.');},true)}
  function newScenario(){touched.current=true;invalidateAuthoring();setBrief('');setAnswers([]);setTurns([]);setAnswer('');setSubmitted(false);setEditing(false);setLegacy(false);setExperiment(null);setOutages([]);setError('');setUncertain(false);setNotice('New empty scenario. Previous experiments remain saved.');setPlaying(false);initial.current={version:1,brief:''};window.scrollTo({top:0,behavior:'smooth'})}
  function chooseTemplate(template:Template){editBrief(template.brief);setEditing(false);setNotice('Example loaded. Describe or change the issue, then start the interview.');}
  function addOutage(){if(!experiment)return;retry.current=null;const resource=experiment.model.resources[0];setOutages(items=>[...items,{id:`outage-${Date.now().toString(36)}-${items.length}`,kind:'resource_outage',resource_id:resource.id,at:Math.min(15,experiment.model.horizon-1),duration:Math.min(20,experiment.model.horizon),capacity_lost:1,label:`Outage ${items.length+1}`}]);setNotice('Unapplied outage edits. Approval and exports are paused.');}
  function editOutage(index:number,change:Partial<Outage>){retry.current=null;setOutages(items=>items.map((item,i)=>i===index?{...item,...change}:item))}
  const hash=compilation?.model_hash;

  return <div className="st-app">
    <a href="#studio-brief" className="st-skip">Skip to scenario brief</a>
    <header className="st-header">
      <a className="st-brand" href="/" aria-label="FORK Scenario Studio"><ForkMark/><strong>FORK<span>.</span></strong><span className="st-brand-rule"/><span className="st-brand-caption">SCENARIO<br/>STUDIO</span></a>
      <nav aria-label="Studio navigation"><a href="?view=logistics">Logistics lab <Arrow/></a><span className="st-mode"><i/>Deterministic demo</span></nav>
    </header>
    <main className="st-main">
      <section className="st-hero" aria-labelledby="studio-title"><div><div className="st-eyebrow"><span/>A WORKBENCH FOR WHAT IF</div><h1 id="studio-title">Every plan has a fork.</h1><p>Describe the work. Explore three futures.<br className="st-mobile-break"/> Make the tradeoff visible.</p></div><div className="st-hero-note"><span className="st-note-index">01 / BRIEF → MODEL → EVIDENCE</span><p>Describe an issue in ordinary words. A bounded local interview clarifies the details before we compute and independently verify three possible futures.</p><a href="#studio-method">How it works <span aria-hidden="true">↓</span></a></div></section>
      <div className="st-process" aria-label="Workflow progress"><span className="st-step st-step-active"><b>01</b> Define the work</span><i/><span className={`st-step ${compilation?.ready&&!compileStale?'st-step-active':''}`}><b>02</b> Review the model</span><i/><span className={`st-step ${experiment?'st-step-active':''}`}><b>03</b> Compare futures</span></div>
      {(notice||busy)&&<div className="st-status" role="status" aria-live="polite">{busy?<><span className="st-spinner"/>{busy}…</>:<><span aria-hidden="true">↳</span>{notice}</>}</div>}
      {error&&<div className="st-alert" role="alert"><div><strong>The operation could not finish.</strong><p>{error}</p>{uncertain&&<p>Saved state may have advanced. Approval and downloads stay paused until a successful retry or saved revision reload.</p>}</div><div className="st-alert-actions">{retry.current&&<button className="st-btn st-btn-small" disabled={!!busy} onClick={()=>retry.current?.()}>Retry operation</button>}{experiment&&<button className="st-btn st-btn-small st-btn-quiet" disabled={!!busy} onClick={reload}>Reload saved revision</button>}</div></div>}
      <section className="st-workbench" aria-label="Scenario workbench">
        <div className="st-brief-panel">
          <div className="st-panel-top"><span className="st-eyebrow">01 — THE SCENARIO</span><button className="st-link-button" disabled={!!busy} onClick={newScenario}>New scenario <span aria-hidden="true">＋</span></button></div>
          <Conversation brief={brief} submitted={submitted} editing={editing} templates={templates} templatesError={templatesError} busy={busy} intake={compilation} answer={answer} answers={answers} turns={turns} legacy={legacy} onBrief={editBrief} onSend={()=>interview()} onAnswer={value=>{retry.current=null;setAnswer(value)}} onSubmitAnswer={submitAnswer} onEdit={editOriginal} onEditAnswer={editAnswer} onExample={chooseTemplate} onRetryExamples={()=>void loadTemplates()}/>
          {legacy&&experiment&&<details className="st-detail"><summary>Earlier authoring source · advanced</summary><pre className="st-run-model">{experiment.brief}</pre></details>}
          {pointer&&!experiment&&<div className="st-resume"><span>A saved experiment is available on this browser.</span><button className="st-link-button" disabled={!!busy} onClick={resume}>Resume saved experiment</button></div>}
        </div>
        <div className={`st-review-panel ${compileStale?'st-is-stale':''}`}>
          <div className="st-panel-top"><span className="st-eyebrow">02 — WHAT WE WILL SIMULATE</span><span className={`st-pill ${compilation?.ready?'st-pill-green':''}`}>{compilation?.ready&&!compileStale?'Ready for review':legacy?'Saved plan':'Clarifying the details'}</span></div>
          {!compilation?.ready?<div className="st-review-waiting"><h2>{legacy?'Your saved futures are below.':'A little clarity goes a long way.'}</h2><p>{legacy?'The original source remains in the saved record. Start a new scenario to build a different plan.':'We will ask only for the details needed to model the work. Nothing runs until you review the plan.'}</p>{compilation?.known?.length? <dl className="st-known">{compilation.known.map(item=><div key={item.id}><dt>{item.label}</dt><dd>{item.value}<small>Provided or resolved · {item.source}</small></dd></div>)}</dl>:null}</div>:<>
            <div className="st-model-heading"><h2>{model?.title}</h2><p>{compilation.summary}</p></div>
            {model&&<div className="st-human-model"><h3>People and resources</h3>{model.resources.map(resource=><p key={resource.id}><strong>{resource.capacity} × {resource.label}</strong><span>{resource.skills.flatMap(skill=>model.tasks.filter(task=>task.skill===skill).slice(0,1).map(task=>task.label.replace(/ \d+$/,''))).join(', ')||'No work assigned to this pool'}</span></p>)}<h3>Work and time</h3><p>{model.tasks.length} work items over {model.horizon} minutes. {model.budget_cents===null?'No spending limit is modeled.':`Spending limit: ${money(model.budget_cents)}.`}</p><ul>{model.tasks.map(task=><li key={task.id}><strong>{task.label}</strong> · {task.duration} minutes · due by minute {task.due}{task.depends_on.length?` · follows ${task.depends_on.map(id=>model.tasks.find(t=>t.id===id)?.label??id).join(', ')}`:''}</li>)}</ul><h3>Accepted assumptions and limits</h3><p>{compilation.scope_note}</p><ul>{compilation.assumptions.filter(item=>!['scope','excluded_details'].includes(item.field)).map((item,i)=><li key={i}>{item.reason.replace(/^Accepted scope: /,'')}</li>)}</ul>{compilation.assumptions.filter(item=>item.field==='excluded_details'&&Array.isArray(item.value)&&item.value.length>0).map((item,i)=><div key={i} className="st-assumption-card"><strong>Outside this simulation</strong>{(item.value as string[]).map((quote,j)=><blockquote key={j}>{quote}</blockquote>)}</div>)}<p>Work can pause and resume. These are synthetic schedules, with no travel or human behavior inferred.</p></div>}
            <details className="st-detail"><summary>Where the facts came from</summary><div className="st-facts">{compilation.known.map(item=><div key={item.id}><p><strong>{item.label}: {item.value}</strong><br/>{item.source}</p></div>)}</div></details>
            <details className="st-detail"><summary>Advanced model and source trace</summary><div className="st-assumptions">{compilation.assumptions.map((item,i)=><p key={`assumption-${i}`}><strong>{item.field}</strong> = {JSON.stringify(item.value)}<span>{item.reason}</span></p>)}{compilation.facts.map((fact,i)=><p key={i}>{fact.text}<span>{fact.targets.join(' · ')}</span></p>)}</div><button className="st-link-button st-json-toggle" onClick={()=>setModelVisible(value=>!value)}>Inspect typed model <span aria-hidden="true">{modelVisible?'−':'＋'}</span></button>{modelVisible&&<div className="st-json"><div><span>DATA ONLY · fork-workflow/1</span><button onClick={async()=>{try{await navigator.clipboard.writeText(JSON.stringify(model,null,2));setCopied(true)}catch{setNotice('Clipboard unavailable. Select the model text to copy it.')}}}>{copied?'Copied':'Copy JSON'}</button></div><pre tabIndex={0}>{JSON.stringify(model,null,2)}</pre></div>}</details>
            <label className="st-review-consent"><input type="checkbox" checked={acceptedModel} onChange={e=>setAcceptedModel(e.target.checked)}/>I reviewed the plan and accept these assumptions for this simulation.</label>
          </>}
          <div className="st-run-box"><p><strong>Three futures, your decision.</strong><span>Review the plan before computing.</span></p><button className="st-btn st-btn-dark" disabled={!validBrief||!!busy} onClick={launch}>Run three futures <Arrow/></button></div>
        </div>
      </section>
      {experiment&&<section className={`st-results ${briefStale?'st-results-stale':''}`} ref={resultsRef} aria-labelledby="futures-title">
        <div className="st-results-heading"><div><div className="st-eyebrow">03 — THE FORK</div><h2 id="futures-title">Three possible futures</h2><p>{experiment.model.title} <span>·</span> Same inputs, isolated schedules, independently checked.</p></div><div className="st-results-revision"><span className="st-pill">Revision {experiment.revision}</span><code>{experiment.id.slice(0,18)}</code></div></div>
        {stale&&<div className="st-inline-warning" role="status">{replayStale?'The authoring model needs reconfirming or its fingerprint changed. Complete the interview, review it and run again.':briefStale?'The issue or an answer changed. These futures belong to an earlier plan. Complete the interview and run again.':eventsDirty?'Outage edits are unapplied. Apply or revert them before approving.':preferencesDirty?'Preferences changed. Save or revert them before approving.':'Saved revision needs reconciliation after a failed request.'} Approval and export are paused.</div>}
        <div className="st-playback"><button className="st-play-button" aria-label={playing?'Pause playback':'Play playback'} onClick={()=>{if(minute>=experiment.model.horizon)setMinute(0);setPlaying(value=>!value)}}>{playing?'Ⅱ':'▶'}</button><div className="st-playback-label"><strong>Computed playback</strong><span>Actual work segments · minutes from zero</span></div><input aria-label="Playback minute" type="range" min="0" max={experiment.model.horizon} value={minute} onChange={event=>{setPlaying(false);setMinute(Number(event.target.value))}}/><span className="st-playback-time" data-testid="playback-time">{minute}m</span><span className="st-playback-total">/ {experiment.model.horizon}m</span></div>
        <div className="st-world-grid">{experiment.worlds.map((world,index)=>{
          const metrics=world.verification.metrics;
          const baseline=experiment.baseline_worlds.find(item=>item.id===world.id);
          const control=experiment.controls.find(item=>item.id===world.id);
          const gain=control?metrics.on_time-control.verification.metrics.on_time:0;
          const isRecommended=experiment.comparison.recommended_id===world.id;
          const isTie=experiment.comparison.tied_ids.includes(world.id);
          const done=world.completions.filter(item=>item.time<=minute).length;
          return <article key={world.id} data-testid="world-card" className={`st-world st-world-${index} ${selected===world.id?'st-world-selected':''}`}>
            <div className="st-world-top"><span>FUTURE {String(index+1).padStart(2,'0')}</span>{isRecommended?<span className="st-world-recommend">Recommended</span>:isTie?<span className="st-world-recommend">Tied preference score</span>:<span className="st-world-strategy">{world.policy}</span>}</div>
            <h3>{world.name}</h3><p className="st-world-description">{policyDescriptions[world.policy]??'A deterministic scheduling heuristic.'}</p>
            <div className="st-world-metric"><strong>{metrics.on_time}<span>/{metrics.total}</span></strong><div>tasks on time<span>{metrics.completed} completed · {metrics.unserved} unserved</span></div><svg viewBox="0 0 45 45" aria-hidden="true"><circle cx="22.5" cy="22.5" r="18"/><circle cx="22.5" cy="22.5" r="18" strokeDasharray={`${metrics.on_time/Math.max(1,metrics.total)*113} 113`}/></svg></div>
            <div className="st-world-submetrics"><div><span>{simplified?'Importance':'Priority on time'}</span><b>{simplified?'Equal for every job':`${metrics.priority_on_time} / ${metrics.priority_total}`}</b></div><div><span>Worked cost</span><b>{simplified?'Not modeled':money(metrics.cost_cents)}</b></div><div><span>{simplified?'Completed jobs':'Completed value'}</span><b>{metrics.value_completed} / {metrics.value_total}</b></div></div>
            <Gantt world={world} model={experiment.model} minute={minute} compact/>
            <div className="st-world-playback"><span>{done} finished at {minute}m</span><span>{world.segments.length} work segments</span></div>
            <div className="st-world-evidence"><span className={world.verification.valid?'st-verified':'st-invalid'}>{world.verification.valid?'✓ Independent receipt valid':'! Independent receipt invalid'}</span><div><span>Adaptation vs locked replay</span><strong>{gain>0?'+':''}{gain} on time</strong></div>{baseline&&<div><span>Without outages</span><strong>{baseline.verification.metrics.on_time} on time</strong></div>}</div>
            <button className="st-select-world" aria-pressed={selected===world.id} disabled={!!busy} onClick={()=>{setSelected(world.id);setReceipt(false)}}>{selected===world.id?'Selected for review':'Review this future'}<span aria-hidden="true">{selected===world.id?'✓':'→'}</span></button>
          </article>
        })}</div>
        <div className="st-legend"><span><i className="st-legend-work"/>Actual processing</span><span><i className="st-legend-due"/>Task deadline</span><span><i className="st-legend-outage"/>Scenario outage interval</span><p>Three bounded heuristics; no optimality claim. Initial plans cannot see outages.</p></div>
        <div className="st-controls-grid"><section className="st-control-panel" aria-labelledby="outage-title"><div className="st-panel-top"><span className="st-eyebrow">THE STRESS TEST</span><span className="st-pill">{outages.length} / 12 events</span></div><h3 id="outage-title">Change the conditions.</h3><p>Take capacity offline. Rerun every future from minute zero with the same outage schedule.</p>
          {!outages.length&&<div className="st-no-outages"><span aria-hidden="true">⌁</span><div><strong>No outages configured.</strong><p>Add a resource outage to reveal how the schedules respond.</p></div></div>}
          <div className="st-outages">{outages.map((outage,index)=><div className="st-outage-editor" key={outage.id}><div className="st-outage-title"><strong>{String(index+1).padStart(2,'0')} / RESOURCE OUTAGE</strong><button aria-label={`Remove outage ${index+1}`} disabled={!!busy||preferencesDirty} onClick={()=>{retry.current=null;setOutages(items=>items.filter(item=>item.id!==outage.id))}}>Remove ×</button></div><label>Resource<select aria-label={`Outage ${index+1} resource`} disabled={!!busy||preferencesDirty} value={outage.resource_id} onChange={event=>{const resource=experiment.model.resources.find(item=>item.id===event.target.value)!;editOutage(index,{resource_id:resource.id,capacity_lost:Math.min(outage.capacity_lost,resource.capacity)})}}>{experiment.model.resources.map(resource=><option key={resource.id} value={resource.id}>{resource.label} (×{resource.capacity})</option>)}</select></label><div className="st-outage-numbers"><label>Starts at (min)<input aria-label={`Outage ${index+1} start`} type="number" min="0" max={experiment.model.horizon-1} step="1" value={outage.at} disabled={!!busy||preferencesDirty} onChange={event=>editOutage(index,{at:Number(event.target.value)})}/></label><label>Lasts (min)<input aria-label={`Outage ${index+1} duration`} type="number" min="1" max={720} step="1" value={outage.duration} disabled={!!busy||preferencesDirty} onChange={event=>editOutage(index,{duration:Number(event.target.value)})}/></label><label>Capacity lost<input aria-label={`Outage ${index+1} capacity lost`} type="number" min="1" max={experiment.model.resources.find(resource=>resource.id===outage.resource_id)?.capacity??12} step="1" value={outage.capacity_lost} disabled={!!busy||preferencesDirty} onChange={event=>editOutage(index,{capacity_lost:Number(event.target.value)})}/></label></div></div>)}</div>
          <div className="st-control-actions"><button className="st-btn st-btn-quiet" disabled={!!busy||outages.length>=12||briefStale||preferencesDirty} onClick={addOutage}>Add outage <span aria-hidden="true">＋</span></button>{eventsDirty&&<><button className="st-btn st-btn-dark" disabled={!!busy||briefStale||preferencesDirty} onClick={applyEvents}>Apply outages & rerun</button><button className="st-link-button" disabled={!!busy} onClick={reload}>Revert outages</button></>}</div><p className="st-small">Overlapping outages add losses, capped at pool capacity. Work is checkpointable. Each change reruns a hypothetical schedule; no real operation is altered.</p></section>
          <section className="st-control-panel" aria-labelledby="preferences-title"><div className="st-panel-top"><span className="st-eyebrow">YOUR TRADEOFF</span><span className="st-pill">Human preference</span></div><h3 id="preferences-title">What matters most?</h3><p>Scores compare verified outcomes. A recommendation is a preference comparison; you choose what to approve.</p>{simplified&&<p className="st-inline-warning">This simplified model gives every job equal importance and excludes costs. Only on-time completion distinguishes the preference scores; no separate priority levels or cost differences are modeled.</p>}<div className="st-weights">{(Object.keys(weightNames) as (keyof Weights)[]).map(key=><label key={key}><span>{weightNames[key]}<b>{Math.round(weights[key]*100)}%</b></span><input aria-label={`${weightNames[key]} weight`} type="range" min="0" max="1" step=".01" value={weights[key]} disabled={!!busy||briefStale||eventsDirty||(simplified&&key!=='completion')} onChange={event=>{retry.current=null;setWeights(value=>({...value,[key]:Number(event.target.value)}))}}/></label>)}</div>{weightSum<=0&&<p className="st-inline-warning">Choose at least one positive preference.</p>}
          {preferencesDirty&&<div className="st-control-actions"><button className="st-btn st-btn-dark" disabled={!!busy||weightSum<=0||eventsDirty||briefStale} onClick={savePreferences}>Save preferences</button><button className="st-link-button" disabled={!!busy} onClick={reload}>Revert preferences</button></div>}
          <div className="st-ranking">{experiment.comparison.ranking.map(item=><div key={item.world_id}><span>{experiment.worlds.find(world=>world.id===item.world_id)?.name??item.world_id}</span><span className="st-score-bar"><i style={{width:`${Math.max(0,Math.min(1,item.score??0))*100}%`}}/></span><b>{item.eligible&&item.score!==null?item.score.toFixed(3):'invalid'}</b></div>)}</div><p className="st-small">Weights are normalized when saved. Score = weighted on-time completion + priority deadlines − resource cost. Exact ties remain ties.</p>
          </section></div>
        {currentWorld&&<section className="st-inspector" aria-label="Selected future review"><div className="st-inspector-header"><div><span className="st-eyebrow">SELECTED FUTURE / REV {experiment.revision}</span><h3>{currentWorld.name}<span>Review the evidence.</span></h3></div><div className="st-inspector-tabs" role="tablist" aria-label="Evidence view"><button role="tab" aria-selected={!receipt} onClick={()=>setReceipt(false)}>Work trace</button><button role="tab" aria-selected={receipt} onClick={()=>setReceipt(true)}>Independent receipt</button></div></div>
          {!receipt?<div role="tabpanel" className="st-trace-panel"><Gantt world={currentWorld} model={experiment.model} minute={minute}/><details className="st-detail"><summary>Modeled execution events <span>{currentWorld.events.length}</span></summary><ol className="st-event-log">{currentWorld.events.filter(event=>event.time<=minute).map((event,index)=><li key={index}><time>{event.time}m</time><span>{event.summary}</span></li>)}{!currentWorld.events.some(event=>event.time<=minute)&&<li>No events at this playback minute.</li>}</ol></details></div>:<div role="tabpanel" className="st-receipt"><div className="st-receipt-banner"><span className={currentWorld.verification.valid?'st-verified':'st-invalid'}>{currentWorld.verification.valid?'✓ Independent verification passed':'! Verification failed'}</span><span>{currentWorld.verification.checks.filter(check=>check.passed).length}/{currentWorld.verification.checks.length} checks</span></div><div className="st-checks">{currentWorld.verification.checks.map(check=><details key={check.id}><summary><span className={check.passed?'st-check-pass':'st-invalid'}>{check.passed?'✓':'!'}</span>{check.label}</summary><p>{check.detail}</p></details>)}</div>{currentWorld.verification.violations.map((violation,index)=><p className="st-inline-warning" key={index}>{violation}</p>)}<p className="st-small">A separate standard-library replay recomputes metrics and checks work, capacity, outages, stock, costs and dependencies.</p><code className="st-evidence-hash">EVIDENCE SHA256<br/>{currentWorld.verification.evidence_hash}<br/>CURRENT EXPERIMENT MODEL SHA256<br/>{experiment.model_hash}</code><details className="st-detail"><summary>Current run model & applied outages</summary><pre className="st-run-model">{JSON.stringify(experiment.model,null,2)}</pre></details></div>}
          <div className="st-approval"><div><strong>{currentApproved?`Approved: ${experiment.worlds.find(world=>world.id===experiment.approved?.world_id)?.name}`:'Human approval is the final gate.'}</strong><p>{currentApproved?`Bound to revision ${experiment.revision}, model and evidence hash.`:'Approval selects a simulated plan for export. No real dispatch or outbound action.'}</p></div>{currentApproved?<div className="st-export"><a className="st-btn st-btn-dark" href={`/api/studio/experiments/${experiment.id}/export?format=json`} download>Export JSON <span aria-hidden="true">↓</span></a><a className="st-btn st-btn-quiet" href={`/api/studio/experiments/${experiment.id}/export?format=csv`} download>Export CSV <span aria-hidden="true">↓</span></a></div>:<button className="st-btn st-btn-primary" disabled={stale||!!busy||!currentWorld.verification.valid} onClick={approve}>Approve selected future <span aria-hidden="true">✓</span></button>}</div>
        </section>}
      </section>}
      <section id="studio-method" className="st-method"><div><span className="st-eyebrow">AN INSPECTABLE SYSTEM</span><h2>Nothing up<br/>its sleeve.</h2></div><div className="st-method-item"><span>01</span><h3>Bounded interview</h3><p>Local phrase extraction and focused questions build an inspectable model. This deterministic demo has a limited language scope; missing facts and unsupported constraints stay visible.</p><a href="/api/studio/schema" target="_blank" rel="noreferrer">Inspect the schema <Arrow/></a></div><div className="st-method-item"><span>02</span><h3>Physical accounting</h3><p>Each minute of work uses actual modeled capacity. Dependencies, stock and budgets constrain all three scheduling heuristics.</p></div><div className="st-method-item"><span>03</span><h3>Independent evidence</h3><p>The referee recomputes outcomes from work segments. A future AI adapter could propose this same schema; no model calls run today.</p></div></section>
      <footer className="st-footer"><div><ForkMark/><strong>FORK.</strong><span>Explore consequences. Own the decision.</span></div><p>Synthetic inputs · Deterministic planning · No real dispatch<br/>Built with substantial OpenAI Codex development assistance.</p>{hash&&<code title={hash}>BRIEF MODEL {hash.slice(0,12)}</code>}</footer>
    </main>
  </div>
}
