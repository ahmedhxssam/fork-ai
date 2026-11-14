import { test, expect, type Page } from '@playwright/test';
async function mission(page:Page){await page.goto('/?view=logistics');await page.getByRole('button',{name:/fork the mission/i}).click();await expect(page.getByRole('heading',{name:'Velocity',exact:true})).toBeVisible({timeout:120000})}
async function approve(page:Page){await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();await page.getByRole('button',{name:/approve simulated plan/i}).click();await expect(page.getByRole('link',{name:'Export JSON'})).toBeVisible();await page.getByRole('button',{name:'Close inspector'}).click()}

test('failed preference save hides prior approved exports and blocks approval until retry',async({page})=>{
  await mission(page);await approve(page);
  await page.route('**/api/experiments/*/preferences',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary preference outage'})}));
  await page.getByRole('slider',{name:'Feed more people weight'}).press('End');
  await expect(page.getByText('Temporary preference outage',{exact:false}).first()).toBeVisible();
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:/approve simulated plan/i})).toBeDisabled();
  await page.getByRole('button',{name:'Close inspector'}).click();
  await page.unroute('**/api/experiments/*/preferences');await page.getByRole('button',{name:'Retry preferences'}).click();
  await expect(page.getByText('Preferences saved',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();await expect(page.getByRole('button',{name:/approve simulated plan/i})).toBeEnabled();
});
test('all-zero desired priorities block a previously approved plan',async({page})=>{
  await mission(page);await approve(page);
  await page.getByRole('slider',{name:'Feed more people weight'}).press('Home');
  await page.getByRole('slider',{name:'Protect high-need service weight'}).press('Home');
  await page.getByRole('slider',{name:'Use fewer resources weight'}).press('Home');
  await expect(page.getByText('Choose a priority',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();await expect(page.getByRole('link',{name:'Export JSON'})).toHaveCount(0);await expect(page.getByRole('button',{name:/approve simulated plan/i})).toBeDisabled();
});
test('preference writes remain serialized under reversed network delays and acknowledge latest sliders',async({page})=>{
  await mission(page);let requests=0,active=0,maxActive=0;
  await page.route('**/api/experiments/*/preferences',async route=>{const order=++requests;active++;maxActive=Math.max(maxActive,active);await new Promise(resolve=>setTimeout(resolve,order===1?700:10));const response=await route.fetch();await route.fulfill({response});active--});
  await page.getByRole('slider',{name:'Feed more people weight'}).press('End');await page.getByRole('slider',{name:'Use fewer resources weight'}).press('End');
  await expect.poll(()=>requests).toBe(2);await expect.poll(()=>active).toBe(0);expect(maxActive).toBe(1);
  const id=await page.evaluate(()=>localStorage.getItem('fork-experiment'));const latest=await(await page.request.get(`/api/experiments/${id}`)).json();
  for(const [key,name] of [['coverage','Feed more people'],['equity','Protect high-need service'],['cost','Use fewer resources']]){await expect.poll(async()=>Number(await page.getByRole('slider',{name:`${name} weight`}).inputValue())).toBeCloseTo(latest.comparison.weights[key],7)}
});
test('transient resume GET retains saved experiment and can be retried',async({page})=>{
  const response=await page.request.post('/api/experiments',{data:{seed:26}});expect(response.ok()).toBeTruthy();const experiment=await response.json();
  await page.addInitScript(id=>localStorage.setItem('fork-experiment',id),experiment.id);
  await page.route(`**/api/experiments/${experiment.id}`,route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary resume outage'})}));
  await page.goto('/?view=logistics');await page.getByRole('button',{name:/resume saved experiment/i}).click();await expect(page.getByText('Temporary resume outage',{exact:false}).first()).toBeVisible();
  await expect(page.getByRole('button',{name:/resume saved experiment/i})).toBeVisible();expect(await page.evaluate(()=>localStorage.getItem('fork-experiment'))).toBe(experiment.id);
  await page.unroute(`**/api/experiments/${experiment.id}`);await page.getByRole('button',{name:/resume saved experiment/i}).click();await expect(page.getByRole('heading',{name:'Velocity',exact:true})).toBeVisible();
});

test('revert re-fetches server preferences after a lost successful POST response',async({page})=>{
  await mission(page);await approve(page);
  await page.route('**/api/experiments/*/preferences',async route=>{await route.fetch();await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Response lost after commit'})})});
  await page.getByRole('slider',{name:'Feed more people weight'}).press('End');
  await expect(page.getByText('Response lost after commit',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Revert saved weights'}).click();
  await expect(page.getByText('Preferences saved',{exact:true})).toBeVisible();
  const id=await page.evaluate(()=>localStorage.getItem('fork-experiment'));const latest=await(await page.request.get(`/api/experiments/${id}`)).json();
  expect(Number(await page.getByRole('slider',{name:'Feed more people weight'}).inputValue())).toBeCloseTo(latest.comparison.weights.coverage,7);
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:/approve simulated plan/i})).toBeEnabled();
});

test('a confirmed not-found resume clears the obsolete saved pointer',async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('fork-experiment','nonexistent-reliability-run'));
  await page.goto('/?view=logistics');await page.getByRole('button',{name:/resume saved experiment/i}).click();
  await expect(page.getByRole('button',{name:/resume saved experiment/i})).toHaveCount(0);
  expect(await page.evaluate(()=>localStorage.getItem('fork-experiment'))).toBeNull();
});

test('late approval response cannot replace a newer acknowledged preference revision',async({page})=>{
  await mission(page);
  let confirmCommit!:()=>void,releaseResponse!:()=>void;
  const committed=new Promise<void>(resolve=>{confirmCommit=resolve});
  const release=new Promise<void>(resolve=>{releaseResponse=resolve});
  await page.route('**/api/experiments/*/approve',async route=>{
    const response=await route.fetch();confirmCommit();await release;await route.fulfill({response});
  });
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();
  const delayedApproval=page.waitForResponse(response=>response.url().endsWith('/approve'));
  await page.getByRole('button',{name:/approve simulated plan/i}).click();
  await committed;
  await page.getByRole('button',{name:'Close inspector'}).click();
  await page.getByRole('slider',{name:'Use fewer resources weight'}).press('End');
  await expect(page.getByText('Preferences saved',{exact:true})).toBeVisible();
  const id=await page.evaluate(()=>localStorage.getItem('fork-experiment'));
  const latest=await(await page.request.get(`/api/experiments/${id}`)).json();
  expect(latest.revision).toBe(2);expect(latest.approved).toBeNull();
  releaseResponse();await delayedApproval;
  await expect(page.locator('.busy-indicator')).toHaveCount(0);
  await expect(page.locator('.mission-title .section-kicker')).toContainText(`REV ${latest.revision}`);
  await page.getByRole('button',{name:'Inspect Velocity',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:/approve simulated plan/i})).toBeEnabled();
});
