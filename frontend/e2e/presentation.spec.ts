import { test, expect, type Page } from '@playwright/test';
import { mkdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const assets=resolve(process.cwd(),'../docs/assets');
const artifacts=resolve(process.cwd(),'../artifacts');

async function launch(page:Page){
  await page.goto('/?view=logistics');
  await page.getByRole('button',{name:/fork the mission/i}).click();
  await expect(page.getByRole('heading',{name:'Velocity',exact:true})).toBeVisible();
}

async function shock(page:Page,vehicle:string,minutes='30'){
  await page.getByRole('button',{name:/inject disruption/i}).click();
  await page.getByRole('combobox',{name:/Vehicle/}).selectOption(vehicle);
  await page.getByLabel('Failure time in minutes').fill(minutes);
  const response=page.waitForResponse(r=>r.url().endsWith('/disrupt')&&r.request().method()==='POST');
  await page.getByRole('button',{name:/confirm shared breakdown/i}).click();
  const data=await (await response).json();
  expect(data.disruption).toEqual({vehicle_id:vehicle,time:Number(minutes)*60});
  expect(data.worlds.every((w:any)=>w.verification.valid)).toBe(true);
  await expect(page.getByText('Recovery vs. no replanning').first()).toBeVisible();
  return data;
}

test('presentation screenshots, independent evidence, and real downloadable artifacts',async({page})=>{
  await mkdir(assets,{recursive:true}); await mkdir(artifacts,{recursive:true});
  await page.goto('/?view=logistics');
  await expect(page.getByRole('button',{name:/fork the mission/i})).toBeEnabled();
  await page.screenshot({path:resolve(assets,'01-mission.png'),fullPage:true});
  await page.getByRole('button',{name:/fork the mission/i}).click();
  await expect(page.getByRole('heading',{name:'Velocity',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Verified outcomes →',exact:true}).click();
  await page.screenshot({path:resolve(assets,'02-parallel-worlds.png'),fullPage:true});
  await shock(page,'B');
  await page.getByRole('button',{name:'Verified outcomes →',exact:true}).click();
  await page.screenshot({path:resolve(assets,'03-aftershock.png'),fullPage:true});
  await page.locator('.world-grid').screenshot({path:resolve(assets,'04-world-comparison.png')});
  await page.getByRole('button',{name:'Inspect Resilience',exact:true}).click();
  await page.getByRole('tab',{name:'Referee receipt',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Independent verification',exact:true})).toBeVisible();
  await page.screenshot({path:resolve(assets,'05-referee.png')});
  await page.getByRole('button',{name:/Approve simulated plan/}).click();
  const jsonDownload=page.waitForEvent('download');
  await page.getByRole('link',{name:'Export JSON',exact:true}).click();
  await (await jsonDownload).saveAs(resolve(artifacts,'approved-resilience.json'));
  const exported=JSON.parse(await readFile(resolve(artifacts,'approved-resilience.json'),'utf8'));
  expect(exported.world.verification.valid).toBe(true);
  expect(exported.decision.world_id).toBe('resilience');
  expect(exported.external_dispatch).toBe(false);
  const csvDownload=page.waitForEvent('download');
  await page.getByRole('link',{name:'Export CSV',exact:true}).click();
  await (await csvDownload).saveAs(resolve(artifacts,'approved-resilience.csv'));
  expect((await readFile(resolve(artifacts,'approved-resilience.csv'),'utf8')).split('\n').length).toBeGreaterThan(2);
});

for(const vehicle of ['A','B','C']){
  test(`judge choice ${vehicle} recomputes real verified recovery`,async({page})=>{
    await launch(page); const data=await shock(page,vehicle);
    for(const world of data.worlds){
      expect(world.initial_hash).toBe(data.scenario.hash);
      expect(world.unadapted_verification.valid).toBe(true);
      expect(world.recovery_gain).toBe(world.metrics.meals_delivered-world.unadapted_metrics.meals_delivered);
    }
  });
}

test('full local journey runs with every external origin blocked',async({page,context})=>{
  const external:string[]=[];
  await context.route('**/*',route=>{
    const host=new URL(route.request().url()).hostname;
    if(host==='127.0.0.1'||host==='localhost') return route.continue();
    external.push(route.request().url()); return route.abort();
  });
  await launch(page); await shock(page,'C','25');
  expect(external).toEqual([]);
  await page.reload();
  await page.getByRole('button',{name:/Resume saved experiment/}).click();
  await expect(page.getByText(/Saved replay/).first()).toBeVisible();
  await page.getByRole('button',{name:'Verified outcomes →',exact:true}).click();
  await expect(page.getByText('Recovery vs. no replanning').first()).toBeVisible();
});

test('narrow layout keeps controls usable without horizontal document overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await launch(page);
  await page.getByRole('tab',{name:/Resilience/}).click();
  await expect(page.getByRole('heading',{name:'Resilience',exact:true})).toBeVisible();
  const widths=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth}));
  expect(widths.document).toBeLessThanOrEqual(widths.viewport+1);
  await page.screenshot({path:resolve(assets,'06-mobile.png'),fullPage:true});
});
