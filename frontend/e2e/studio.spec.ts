import { test, expect, type Page } from '@playwright/test';

async function compile(page:Page){
  await page.getByRole('button',{name:'Compile brief',exact:true}).click();
  await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
}
async function launch(page:Page){
  await page.goto('/'); await compile(page);
  await page.getByRole('button',{name:'Run three futures',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Three possible futures',exact:true})).toBeVisible();
  await expect(page.getByTestId('world-card')).toHaveCount(3);
}

test('prefilled editable brief, cross-domain model review and unsupported requests block',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Every plan has a fork.',exact:true})).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Scenario brief'})).not.toHaveValue('');
  await compile(page);
  await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeEnabled();
  const first=await page.getByRole('textbox',{name:'Scenario brief'}).inputValue();
  await page.getByRole('button',{name:/IT.*response/i}).click();
  await expect(page.getByRole('textbox',{name:'Scenario brief'})).not.toHaveValue(first);
  await compile(page);
  await page.getByRole('textbox',{name:'Scenario brief'}).fill('Teleport every task to Mars.');
  await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Compile brief',exact:true}).click();
  await expect(page.getByText('Needs revision',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
});

test('computed futures, outage rerun, stale gates, current approval and downloadable evidence',async({page})=>{
  await launch(page);
  const id=await page.evaluate(()=>localStorage.getItem('fork-studio-experiment'));
  const before=await(await page.request.get(`/api/studio/experiments/${id}`)).json();
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
  await page.getByLabel('Outage 1 start').fill('0');
  await page.getByLabel('Outage 1 duration').fill(String(before.model.horizon));
  await page.getByLabel('Outage 1 capacity lost').fill(String(before.model.resources[0].capacity));
  await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
  const after=await(await page.request.get(`/api/studio/experiments/${id}`)).json();
  expect(after.worlds.map((world:any)=>world.segments)).not.toEqual(before.worlds.map((world:any)=>world.segments));
  expect(after.worlds.every((world:any)=>world.verification.valid)).toBe(true);
  await page.getByRole('button',{name:'Approve selected future',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
  const href=await page.getByRole('link',{name:'Export JSON',exact:true}).getAttribute('href');
  expect((await page.request.get(href!)).ok()).toBeTruthy();
  await page.getByRole('textbox',{name:'Scenario brief'}).fill('An edited brief');
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
});

test('resume survives a transient error and start over creates an empty draft',async({page})=>{
  await launch(page);
  const id=await page.evaluate(()=>localStorage.getItem('fork-studio-experiment'));
  await page.reload();
  await page.route(`**/api/studio/experiments/${id}`,route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary studio outage'})}));
  await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();
  await expect(page.getByText(/Temporary studio outage/)).toBeVisible();
  expect(await page.evaluate(()=>localStorage.getItem('fork-studio-experiment'))).toBe(id);
  await page.unroute(`**/api/studio/experiments/${id}`);
  await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Three possible futures',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'New scenario',exact:true}).click();
  await expect(page.getByRole('textbox',{name:'Scenario brief'})).toHaveValue('');
  await expect(page.getByTestId('world-card')).toHaveCount(0);
  expect(await page.evaluate(()=>localStorage.getItem('fork-studio-experiment'))).toBe(id);
});

test('mobile keyboard, real playback and bounded document width',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await launch(page);
  await page.getByRole('slider',{name:'Playback minute'}).press('End');
  await expect(page.getByTestId('playback-time')).not.toHaveText('0m');
  await page.getByRole('button',{name:'Inspect typed model',exact:true}).click();
  await expect(page.getByText('fork-workflow/1',{exact:false}).first()).toBeVisible();
  const widths=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth}));
  expect(widths.document).toBeLessThanOrEqual(widths.viewport+1);
});

test('a lost successful outage response cannot discard a newer draft on retry',async({page})=>{
  await launch(page);
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.getByLabel('Outage 1 duration').fill('20');
  await page.route('**/api/studio/experiments/*/events',async route=>{await route.fetch();await route.abort('failed')});
  await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();
  await expect(page.getByRole('button',{name:'Retry operation',exact:true})).toBeVisible();
  await page.getByLabel('Outage 1 duration').fill('35');
  await expect(page.getByRole('button',{name:'Retry operation',exact:true})).toHaveCount(0);
  await expect(page.getByLabel('Outage 1 duration')).toHaveValue('35');
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Reload saved revision',exact:true}).click();
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Outage 1 duration')).toHaveValue('20');
});

test('successful compilation cannot clear an uncertain preference write',async({page})=>{
  await launch(page);
  const slider=page.getByRole('slider',{name:'On-time completion weight'});
  await slider.press('ArrowRight');
  await page.route('**/api/studio/experiments/*/preferences',async route=>{await route.fetch();await route.abort('failed')});
  await page.getByRole('button',{name:'Save preferences',exact:true}).click();
  await expect(page.getByRole('button',{name:'Retry operation',exact:true})).toBeVisible();
  await slider.press('ArrowLeft');
  await compile(page);
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Reload saved revision',exact:true}).click();
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeEnabled();
});

test('retry reuses the mutation key after a committed response is lost',async({page})=>{
  await launch(page);let attempts=0;const keys:string[]=[];
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.route('**/api/studio/experiments/*/events',async route=>{keys.push(route.request().headers()['idempotency-key']);if(++attempts===1){await route.fetch();await route.abort('failed')}else await route.continue()});
  await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();
  await page.getByRole('button',{name:'Retry operation',exact:true}).click();
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
  expect(keys).toHaveLength(2);expect(keys[0]).toBeTruthy();expect(keys[0]).toBe(keys[1]);
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeEnabled();
});

test('multiple event drafts survive a reload and preference writes cannot discard them',async({page})=>{
  await launch(page);
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.getByRole('button',{name:'Add outage',exact:true}).click();
  await page.getByLabel('Outage 2 start').fill('35');
  await expect(page.getByRole('slider',{name:'On-time completion weight'})).toBeDisabled();
  await page.reload();await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();
  await expect(page.getByLabel('Outage 2 start')).toHaveValue('35');
  await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();
  await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
});

test('a late template response cannot replace a brief typed while examples load',async({page})=>{
  let release!:()=>void;const gate=new Promise<void>(resolve=>{release=resolve});
  await page.route('**/api/studio/templates',async route=>{await gate;await route.continue()});
  await page.goto('/');
  await page.getByRole('textbox',{name:'Scenario brief'}).fill('Title: My custom draft');
  release();
  await expect(page.getByRole('button',{name:/Community repair clinic/i})).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Scenario brief'})).toHaveValue('Title: My custom draft');
});

test('approval exports refer to the selected future and a different future can be approved',async({page})=>{
  await launch(page);await page.getByRole('button',{name:'Approve selected future',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
  await page.getByTestId('world-card').nth(1).getByRole('button',{name:'Review this future',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Approve selected future',exact:true}).click();
  const href=await page.getByRole('link',{name:'Export JSON',exact:true}).getAttribute('href');
  const exported=await(await page.request.get(href!)).json();
  expect(exported.approved.world_id).toBe(exported.worlds[1].id);
});
