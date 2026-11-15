import { test, expect } from '@playwright/test';

test('guided judging preserves saved work, uses one real shock, and requires human approval', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('fork-experiment', 'saved-before-tour'));
  let launches=0, shocks=0;
  page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/api/experiments')) launches++; if(request.url().endsWith('/disrupt')) shocks++;});
  await page.goto('/?view=logistics&tour=1&pace=120');
  const tour=page.getByTestId('judging-tour');
  await expect(tour).toBeVisible();
  await expect(tour).toHaveAttribute('data-step','0');
  await page.getByRole('button',{name:'Next: compare plans',exact:true}).click();
  await expect(tour).toHaveAttribute('data-step','1',{timeout:120000});
  await expect(page.locator('.world-card')).toHaveCount(3);
  await page.getByRole('button',{name:'Next: honest controls',exact:true}).click();
  await expect(page.locator('.controls-section')).toHaveClass(/tour-highlight/);
  await page.getByRole('button',{name:'Next: shared breakdown',exact:true}).click();
  await page.getByRole('button',{name:'Apply shared breakdown',exact:true}).click();
  await expect(tour).toHaveAttribute('data-step','4',{timeout:120000});
  await expect(page.getByLabel('Mission timeline')).toHaveValue('14400');
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await page.getByRole('button',{name:'Apply shared breakdown',exact:true}).click();
  await expect(tour).toHaveAttribute('data-step','4');
  expect(shocks).toBe(1); expect(launches).toBe(1);
  await page.getByRole('button',{name:'Next: your priorities',exact:true}).click();
  await page.getByRole('button',{name:'Next: independent referee',exact:true}).click();
  await expect(page.locator('dialog[open]').getByTestId('judging-tour')).toBeVisible();
  await expect(page.getByRole('tab',{name:'Referee receipt',exact:true})).toHaveAttribute('aria-selected','true');
  await page.getByRole('tab',{name:'Event ledger',exact:true}).click();
  await expect(page.getByRole('tab',{name:'Event ledger',exact:true})).toHaveAttribute('aria-selected','true');
  await page.getByRole('tab',{name:'Referee receipt',exact:true}).click();
  await expect(page.locator('dialog[open] [data-tour=receipt]')).toHaveClass(/tour-highlight/);
  await page.getByRole('button',{name:'Next: human decision',exact:true}).click();
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await expect(page.locator('dialog[open] [data-tour=receipt]')).toHaveClass(/tour-highlight/);
  await page.getByRole('button',{name:'Next: human decision',exact:true}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:/^Approve simulated plan/}).click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Finish tour',exact:true}).click();
  await expect(tour).toHaveCount(0);
  expect(await page.evaluate(()=>localStorage.getItem('fork-experiment'))).toBe('saved-before-tour');
});

test('failed launch stays retryable; restart and keyboard navigation work on mobile',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto('/?view=logistics&tour=1');
  await page.route('**/api/experiments', route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary tutorial test failure'})}),{times:1});
  await page.getByRole('button',{name:'Next: compare plans',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','0');
  await expect(page.getByTestId('judging-tour').getByRole('alert')).toBeVisible();
  await page.getByRole('button',{name:'Next: compare plans',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','1',{timeout:120000});
  await page.keyboard.press('ArrowRight');
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','2');
  await page.keyboard.press('ArrowLeft');
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','1');
  await page.getByRole('button',{name:'Restart tour',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','0');
  await expect(page.getByRole('heading',{name:'Keep food deliveries moving.',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('judging-tour')).toHaveCount(0);
});

test('shared shock failure is retryable without losing the chapter or approving anything',async({page})=>{
  await page.goto('/?view=logistics&tour=1');
  for(const name of ['Next: compare plans','Next: honest controls','Next: shared breakdown']) await page.getByRole('button',{name,exact:true}).click();
  await page.route('**/disrupt',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary disruption failure'})}),{times:1});
  await page.getByRole('button',{name:'Apply shared breakdown',exact:true}).click();
  await expect(page.getByTestId('judging-tour').getByRole('alert')).toBeVisible();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','3');
  await page.getByRole('button',{name:'Apply shared breakdown',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','4',{timeout:120000});
  await expect(page.locator('.split-world')).toHaveCount(3);
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toContainText('breakdown is already applied');
  await page.getByRole('button',{name:'Restart tour',exact:true}).click();
  await page.getByRole('button',{name:'Next: compare plans',exact:true}).click();
  await expect(page.getByTestId('judging-tour')).toHaveAttribute('data-step','1',{timeout:120000});
  await expect(page.locator('.split-evidence')).toHaveCount(0);
});

test('mobile receipt and explicit approval remain accessible above the tour panel',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/?view=logistics&tour=1');
  for(const name of ['Next: compare plans','Next: honest controls','Next: shared breakdown','Apply shared breakdown','Next: your priorities','Next: independent referee']) await page.getByRole('button',{name,exact:true}).click();
  await expect(page.locator('dialog[open] [data-tour=receipt]')).toHaveClass(/tour-highlight/);
  await page.getByRole('button',{name:'Pause timer',exact:true}).click();
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await expect(page.getByRole('button',{name:'Resume timer',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Next: independent referee',exact:true}).click();
  await expect(page.getByRole('button',{name:'Resume timer',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Next: human decision',exact:true}).click();
  const approve=page.getByRole('button',{name:/^Approve simulated plan/});
  await approve.scrollIntoViewIfNeeded();
  const approvalBox=await approve.boundingBox(), panelBox=await page.getByTestId('judging-tour').boundingBox();
  expect(approvalBox!.y+approvalBox!.height).toBeLessThanOrEqual(panelBox!.y);
  await approve.click();
  await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('judging-tour')).toHaveCount(0);
  await expect(page.locator('dialog[open]')).toHaveCount(0);
});

test('tablet briefing spotlight contains its resource figures',async({page})=>{
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/?view=logistics&tour=1');
  await expect(page.locator('.brief-resources')).toHaveClass(/tour-highlight/);
  const target=await page.locator('.brief-resources').boundingBox();
  expect(target!.width).toBeGreaterThan(500);
  for(const figure of await page.locator('.brief-resources>div').all()){
    const box=await figure.boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(target!.x);
    expect(box!.x+box!.width).toBeLessThanOrEqual(target!.x+target!.width+1);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('logistics first render waits for its stylesheet',async({page})=>{
  await page.route('**/assets/styles-*.css',async route=>{
    await new Promise(resolve=>setTimeout(resolve,400));
    await route.continue();
  });
  await page.goto('/?view=logistics',{waitUntil:'domcontentloaded'});
  await page.locator('.brand').waitFor();
  const appearance=await page.locator('.brand').evaluate(element=>({color:getComputedStyle(element).color,font:getComputedStyle(element).fontFamily}));
  expect(appearance.color).not.toBe('rgb(0, 0, 238)');
  expect(appearance.font).toMatch(/Inter|sans-serif/);
});
