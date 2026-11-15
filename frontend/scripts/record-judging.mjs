/** Record the actual local FORK workflow. Editorial frames are composed separately.
 * node scripts/media/prepare.mjs
 * FORK_URL=http://127.0.0.1:8767 node frontend/scripts/record-judging.mjs
 * .venv/bin/python scripts/media/render.py
 * Uses a fresh experiment; never resets or deletes history. No API mocks or model calls.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH ||= path.join(root,'.cache/ms-playwright');
const {chromium,expect}=await import('@playwright/test');
const work=process.env.FORK_MEDIA_WORK || '/private/tmp/fork-submission-media';
const storyboard=JSON.parse(await fs.readFile(path.join(work,'storyboard.json'),'utf8'));
const screens=path.join(root,'docs/assets/presentation');
await fs.mkdir(screens,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--force-device-scale-factor=2']});
const context=await browser.newContext({viewport:{width:1440,height:800},deviceScaleFactor:2,recordVideo:{dir:path.join(work,'raw'),size:{width:2880,height:1600}},acceptDownloads:true,reducedMotion:'no-preference'});
const external=[],errors=[],timeline=[];const responses=[];
await context.route('**/*',r=>{const u=new URL(r.request().url());if(['127.0.0.1','localhost'].includes(u.hostname))return r.continue();external.push(u.origin);return r.abort();});
await context.addInitScript(()=>{
 addEventListener('DOMContentLoaded',()=>{const dot=document.createElement('div');dot.id='recording-pointer';dot.style.cssText='position:fixed;left:-40px;top:-40px;width:14px;height:14px;border-radius:50%;background:#5C7658;box-shadow:0 0 0 3px #D8E4D0b0;z-index:2147483647;pointer-events:none;transform:translate(-50%,-50%);transition:box-shadow .15s';document.body.append(dot);addEventListener('mousemove',e=>{dot.style.left=e.clientX+'px';dot.style.top=e.clientY+'px'});addEventListener('mousedown',()=>dot.style.boxShadow='0 0 0 9px #D8E4D0b0');addEventListener('mouseup',()=>dot.style.boxShadow='0 0 0 3px #D8E4D0b0');});
});
const recordStart=Date.now(),page=await context.newPage(),video=page.video();
page.on('pageerror',e=>errors.push(e.message));
page.on('response',r=>{if(r.request().method()==='POST')responses.push({url:new URL(r.url()).pathname,status:r.status()});});
await page.goto(process.env.FORK_URL || 'http://127.0.0.1:8767/',{waitUntil:'networkidle'});
await expect(page.getByRole('link',{name:'Try the food-bank demo',exact:true})).toBeVisible();
await page.waitForTimeout(500);
const lead=(Date.now()-recordStart)/1000;const origin=Date.now();
let baseline,experiment,approval,packet,beforePreferences,afterPreferences;
async function click(target){await target.evaluate(el=>{const r=el.getBoundingClientRect();if(r.top<0||r.bottom>innerHeight)el.scrollIntoView({behavior:'smooth',block:'center'})});await page.waitForTimeout(650);const b=await target.boundingBox();await page.mouse.move(b.x+b.width*.6,b.y+b.height*.5,{steps:22});await page.waitForTimeout(220);await target.click();}
async function smooth(target){await target.evaluate(el=>el.scrollIntoView({behavior:'smooth',block:'center'}));await page.waitForTimeout(1100);}
async function shot(n){await page.screenshot({path:path.join(screens,`chapter-${String(n).padStart(2,'0')}-source.png`)});}
async function phase(n,fn){const c=storyboard.chapters[n-1],start=Date.now();timeline.push({chapter:n,start:(start-origin)/1000,planned_seconds:c.seconds});await fn();const elapsed=(Date.now()-start)/1000;if(elapsed>c.seconds-.3)throw Error(`Chapter ${n} action ${elapsed}s exceeded hold`);await page.waitForTimeout(c.seconds*1000-(Date.now()-start));}
try{
 await phase(1,async()=>{await shot(1);});
 await phase(2,async()=>{await click(page.getByRole('link',{name:'Try the food-bank demo',exact:true}));await expect(page.getByRole('button',{name:/fork the mission/i})).toBeEnabled();await shot(2);});
 await phase(3,async()=>{const response=page.waitForResponse(r=>r.url().endsWith('/api/experiments')&&r.request().method()==='POST');await click(page.getByRole('button',{name:/fork the mission/i}));baseline=await(await response).json();await expect(page.getByRole('heading',{name:'Velocity',exact:true})).toBeVisible();expect(baseline.worlds.map(w=>w.metrics.meals_delivered)).toEqual([216,192,216]);expect(baseline.benchmarks.find(b=>b.id==='greedy').metrics.meals_delivered).toBe(224);await click(page.getByRole('button',{name:'Verified outcomes →',exact:true}));await page.waitForTimeout(3000);await smooth(page.locator('.controls-section'));await shot(3);});
 await phase(4,async()=>{await click(page.getByRole('button',{name:/inject disruption/i}));await page.getByRole('combobox',{name:/Vehicle/}).selectOption('A');await page.getByLabel('Failure time in minutes').fill('25');await shot(4);await page.waitForTimeout(2600);const response=page.waitForResponse(r=>r.url().endsWith('/disrupt')&&r.request().method()==='POST');await click(page.getByRole('button',{name:/confirm shared breakdown/i}));experiment=await(await response).json();expect(experiment.disruption).toEqual({vehicle_id:'A',time:1500});expect(experiment.worlds.map(w=>w.metrics.meals_delivered)).toEqual([168,168,168]);expect(experiment.worlds.map(w=>w.unadapted_metrics.meals_delivered)).toEqual([144,120,144]);for(const w of experiment.worlds){expect(w.verification.valid).toBe(true);expect(w.unadapted_verification.valid).toBe(true);}await click(page.getByRole('button',{name:'Verified outcomes →',exact:true}));});
 await phase(5,async()=>{await smooth(page.locator('.world-grid .outcome-head').first());await shot(5);await page.waitForTimeout(7500);await smooth(page.locator('.split-evidence'));await page.screenshot({path:path.join(screens,'chapter-05-exposure-source.png')});});
 await phase(6,async()=>{await smooth(page.locator('.decision-section'));beforePreferences=await page.locator('.recommendation').innerText();await page.waitForTimeout(1900);const response=page.waitForResponse(r=>r.url().endsWith('/preferences')&&r.request().method()==='POST');const slider=page.getByRole('slider',{name:'Use fewer resources weight'});await slider.focus();await slider.press('End');const savedPreferences=await response;expect(savedPreferences.ok()).toBe(true);const current=await savedPreferences.json();experiment={...experiment,revision:current.revision,comparison:current};await expect(page.locator('.recommendation > span').first()).toHaveText('CURRENT RECOMMENDATION');afterPreferences=await page.locator('.recommendation').innerText();await shot(6);});
 await phase(7,async()=>{await click(page.getByRole('button',{name:'Inspect Velocity',exact:true}));await click(page.getByRole('tab',{name:'Referee receipt',exact:true}));await expect(page.getByRole('heading',{name:'Independent verification',exact:true})).toBeVisible();await shot(7);});
 await phase(8,async()=>{await page.waitForTimeout(2000);const response=page.waitForResponse(r=>r.url().endsWith('/approve')&&r.request().method()==='POST');await click(page.getByRole('button',{name:/approve simulated plan/i}));approval=await(await response).json();await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();await page.waitForTimeout(1500);const downloaded=page.waitForEvent('download');await click(page.getByRole('link',{name:'Export JSON',exact:true}));await(await downloaded).saveAs(path.join(root,'artifacts/FORK-submission-approved.json'));packet=JSON.parse(await fs.readFile(path.join(root,'artifacts/FORK-submission-approved.json'),'utf8'));expect(packet.external_dispatch).toBe(false);expect(packet.decision.revision).toBe(experiment.revision);expect(packet.decision.revision).toBe(approval.revision);expect(packet.world.verification.valid).toBe(true);const csv=page.waitForEvent('download');await click(page.getByRole('link',{name:'Export CSV',exact:true}));await(await csv).saveAs(path.join(root,'artifacts/FORK-submission-approved.csv'));await shot(8);});
 expect(external).toEqual([]);expect(errors).toEqual([]);
}finally{await context.close();await video.saveAs(path.join(work,'screen.webm'));await fs.copyFile(path.join(work,'screen.webm'),path.join(root,'artifacts/FORK-submission-source.webm'));await browser.close();}
const evidence={source:'Actual uncut local browser workflow, with separate editorial chapter frame and visible pointer.',source_video:'artifacts/FORK-submission-source.webm',synthetic:true,mode:'deterministic',capture:{css_viewport:{width:1440,height:800},device_scale_factor:2,requested_video:{width:2880,height:1600}},narration:storyboard.narration || 'Local synthetic narration; see the prepared storyboard.',external_requests:external,page_errors:errors,post_responses:responses,lead_seconds:lead,recorded_timeline:timeline,experiment_id:experiment.id,revision:experiment.revision,shock:experiment.disruption,baseline:{named_meals:baseline.worlds.map(w=>w.metrics.meals_delivered),greedy_meals:baseline.benchmarks.find(b=>b.id==='greedy').metrics.meals_delivered},worlds:experiment.worlds.map(w=>({id:w.id,delivered:w.metrics.meals_delivered,fixed_plan_delivered:w.unadapted_metrics.meals_delivered,valid:w.verification.valid,fixed_plan_valid:w.unadapted_verification.valid})),before_preferences:beforePreferences,after_preferences:afterPreferences,approval,export:{external_dispatch:packet.external_dispatch,revision:packet.decision.revision,referee_valid:packet.world.verification.valid},video:'artifacts/FORK-submission-demo.mp4'};
await fs.writeFile(path.join(root,'artifacts/FORK-submission-demo-evidence.json'),JSON.stringify(evidence,null,2));
console.log(JSON.stringify(evidence,null,2));
