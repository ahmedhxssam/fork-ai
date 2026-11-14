import {test,expect} from '@playwright/test';
import {understand} from './studio-helpers';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const assets=resolve(process.cwd(),'../docs/assets');
const artifacts=resolve(process.cwd(),'../artifacts');

test('three distinct workflow domains, shared engine, multiple real outages and approved downloads stay local',async({page,context})=>{
  const external:string[]=[];
  await context.route('**/*',route=>{
    const host=new URL(route.request().url()).hostname;
    if(host==='127.0.0.1'||host==='localhost')return route.continue();
    external.push(route.request().url());return route.abort();
  });
  await mkdir(assets,{recursive:true});await mkdir(artifacts,{recursive:true});
  await page.goto('/');
  await expect(page.getByRole('textbox',{name:'Describe what is happening'})).not.toHaveValue('');
  await page.screenshot({path:resolve(assets,'studio-01-workbench.png')});
  const domains=[];
  for(const title of ['Incomplete details','Conflicting details','Another operation']){
    await page.getByRole('button',{name:title,exact:true}).click();
    await understand(page);
    await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
    if(title==='Incomplete details')await page.locator('.st-workbench').screenshot({path:resolve(assets,'studio-02-model.png')});
    const response=page.waitForResponse(r=>r.url().endsWith('/api/studio/experiments')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Run three futures',exact:true}).click();
    const exp=await(await response).json();
    await expect(page.getByTestId('world-card')).toHaveCount(3);
    await expect(page.getByRole('button',{name:'Add outage',exact:true})).toBeEnabled();
    expect(exp.worlds.every((world:any)=>world.verification.valid)).toBe(true);
    expect(exp.worlds.every((world:any)=>world.segments.length>0)).toBe(true);
    domains.push({id:exp.id,title:exp.model.title,hash:exp.model_hash,
      skills:exp.model.resources.flatMap((r:any)=>r.skills),work_labels:exp.model.tasks.map((t:any)=>t.label),tasks:exp.model.tasks.map((t:any)=>t.id),
      metrics:exp.worlds.map((w:any)=>({policy:w.policy,metrics:w.verification.metrics}))});
  }
  expect(new Set(domains.map(domain=>domain.hash)).size).toBe(3);
  expect(new Set(domains.map(domain=>domain.work_labels.join(','))).size).toBe(3);
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.getByLabel('Outage 1 start').fill('5');
  await page.getByLabel('Outage 1 duration').fill('10');
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.getByLabel('Outage 2 start').fill('25');
  await page.getByLabel('Outage 2 duration').fill('8');
  const rerun=page.waitForResponse(r=>r.url().endsWith('/events')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();
  const shocked=await(await rerun).json();
  expect(shocked.model.events).toHaveLength(2);
  expect(shocked.worlds.every((world:any)=>world.verification.valid)).toBe(true);
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
  await page.locator('.st-world-grid').screenshot({path:resolve(assets,'studio-03-futures.png')});
  await page.getByRole('tab',{name:'Independent receipt',exact:true}).click();
  await expect(page.getByText('Independent verification passed',{exact:false}).first()).toBeVisible();
  await page.getByRole('button',{name:'Approve selected future',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
  const jsonDownload=page.waitForEvent('download');
  await page.getByRole('link',{name:'Export JSON',exact:true}).click();
  await(await jsonDownload).saveAs(resolve(artifacts,'studio-approved.json'));
  const exported=JSON.parse(await readFile(resolve(artifacts,'studio-approved.json'),'utf8'));
  expect(exported.approved.revision).toBe(exported.revision);
  expect(exported.approved.model_hash).toBe(exported.model_hash);
  expect(exported.model.events).toHaveLength(2);
  const selected=exported.worlds.find((world:any)=>world.id===exported.approved.world_id);
  expect(selected.verification.valid).toBe(true);
  expect(selected.verification.evidence_hash).toBe(exported.approved.evidence_hash);
  const csvDownload=page.waitForEvent('download');
  await page.getByRole('link',{name:'Export CSV',exact:true}).click();
  await(await csvDownload).saveAs(resolve(artifacts,'studio-approved.csv'));
  const csv=await readFile(resolve(artifacts,'studio-approved.csv'),'utf8');
  expect(csv.split('\n')[0].trim()).toBe('task_id,resource_id,start,end,units');
  expect(csv.split('\n').filter(Boolean).length).toBe(selected.segments.length+1);
  await page.locator('.st-inspector').screenshot({path:resolve(assets,'studio-04-receipt.png')});
  expect(external).toEqual([]);
  await writeFile(resolve(artifacts,'studio-domain-evidence.json'),JSON.stringify({mode:'deterministic',synthetic:true,external_requests:external,domains,shocked_experiment_id:shocked.id},null,2));
});

test('mobile scenario authoring and model review retain readable controls',async({page})=>{
  await mkdir(assets,{recursive:true});
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  const editorSize=await page.getByRole('textbox',{name:'Describe what is happening'}).evaluate(element=>parseFloat(getComputedStyle(element).fontSize));
  await understand(page);
  await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
  const dimensions=await page.evaluate(()=>({width:innerWidth,document:document.documentElement.scrollWidth}));
  expect(dimensions.document).toBeLessThanOrEqual(dimensions.width+1);
  expect(editorSize).toBeGreaterThanOrEqual(16);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:resolve(assets,'studio-05-mobile.png'),fullPage:true});
});
