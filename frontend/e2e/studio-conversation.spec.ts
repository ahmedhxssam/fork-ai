import {test,expect} from '@playwright/test';

test('human prose begins a focused interview and editing the issue clears readiness',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('button',{name:'Incomplete details',exact:true})).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Describe what is happening'})).not.toHaveValue('');
  await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
  await expect(page.getByTestId('intake-question')).toHaveCount(1);
  await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Edit original issue',exact:true}).click();
  await page.getByRole('textbox',{name:'Describe what is happening'}).fill('We need help deciding what can get done.');
  await expect(page.getByTestId('intake-question')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
});

import {understand} from './studio-helpers';

test('conflicting claims stay quoted until a person resolves them',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Conflicting details',exact:true}).click();
 await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
 const question=page.getByTestId('intake-question');await expect(question).toContainText('two technicians');await expect(question).toContainText('three technicians');
 await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
 await question.locator('.st-answer-chips button').last().click();
 await expect(question).toContainText('one hour');await expect(question).toContainText('90 minutes');
 await question.locator('.st-answer-chips button').last().click();await page.getByRole('button',{name:'Use this simplified scope',exact:true}).click();
 await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
 await page.getByRole('checkbox',{name:/I reviewed the plan/}).check();
 await page.getByRole('button',{name:'Run three futures',exact:true}).click();await expect(page.getByTestId('world-card')).toHaveCount(3);
 await page.getByRole('button',{name:'Approve selected future',exact:true}).click();await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
 const firstId=await page.evaluate(()=>localStorage.getItem('fork-studio-experiment'));const first=await(await page.request.get(`/api/studio/experiments/${firstId}`)).json();
 await page.getByRole('button',{name:'Edit answer 1',exact:true}).click();await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);
 await expect(page.getByTestId('intake-question')).toContainText('technicians');await expect(page.getByRole('textbox',{name:/Your answer/})).toHaveValue('3');
 await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
 await question.locator('.st-answer-chips button').first().click();await question.locator('.st-answer-chips button').last().click();await page.getByRole('button',{name:'Use this simplified scope',exact:true}).click();await page.getByRole('checkbox',{name:/I reviewed the plan/}).check();
 const response=page.waitForResponse(r=>r.url().endsWith('/api/studio/experiments')&&r.request().method()==='POST');await page.getByRole('button',{name:'Run three futures',exact:true}).click();const second=await(await response).json();
 expect(first.model.resources[0].capacity).toBe(3);expect(second.model.resources[0].capacity).toBe(2);expect(second.model_hash).not.toBe(first.model_hash);expect(second.worlds.map((world:any)=>world.metrics.on_time)).not.toEqual(first.worlds.map((world:any)=>world.metrics.on_time));
});

test('invalid answers remain editable and keyboard sends one answer at a time',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
 const input=page.getByRole('textbox',{name:/Your answer/});await input.fill('not a number');await input.press('Enter');
 await expect(input).toHaveValue('not a number');await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
 await input.fill('6');await input.press('Shift+Enter');await expect(input).toHaveValue('6\n');await input.press('Enter');
 await expect(page.getByTestId('intake-question')).toContainText(/minutes.*bike repair.*take/i);
 const size=await input.evaluate(element=>getComputedStyle(element).fontSize);expect(parseFloat(size)).toBeGreaterThanOrEqual(16);
});

test('late intake response cannot restore a changed issue or its readiness',async({page})=>{
 let release!:()=>void;const gate=new Promise<void>(resolve=>{release=resolve});
 await page.goto('/');await page.route('**/api/studio/intake',async route=>{const response=await route.fetch();await gate;await route.fulfill({response})});
 await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
 await page.getByRole('button',{name:'Edit original issue',exact:true}).click();await page.getByRole('textbox',{name:'Describe what is happening'}).fill('My changed operation');release();
 await expect(page.getByRole('status').filter({hasText:'Understanding scenario'})).toHaveCount(0);
 await expect(page.getByRole('textbox',{name:'Describe what is happening'})).toHaveValue('My changed operation');await expect(page.getByTestId('intake-question')).toHaveCount(0);
});

test('natural authoring resumes with original answers after outages while older drafts survive',async({page})=>{
 await page.goto('/');await page.evaluate(()=>localStorage.setItem('fork-studio-draft',JSON.stringify({brief:'Old structured source'})));
 await page.getByRole('button',{name:'Another operation',exact:true}).click();await understand(page);await page.getByRole('button',{name:'Run three futures',exact:true}).click();await expect(page.getByTestId('world-card')).toHaveCount(3);
 await page.getByRole('button',{name:'Add outage',exact:true}).click();await page.getByRole('button',{name:'Apply outages & rerun',exact:true}).click();await expect(page.getByText('Revision 2',{exact:true})).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();await expect(page.getByLabel('Outage 1 duration')).toHaveValue('20');
 expect(JSON.parse((await page.evaluate(()=>localStorage.getItem('fork-studio-draft')))!)).toEqual({brief:'Old structured source'});
 await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeEnabled();
});

test('unfinished interview reconstructs its next question on reload',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Understand scenario',exact:true}).click();await page.getByRole('textbox',{name:/Your answer/}).fill('6');await page.getByRole('button',{name:'Send answer',exact:true}).click();await expect(page.getByTestId('intake-question')).toContainText(/minutes.*bike repair.*take/i);await page.reload();await expect(page.getByTestId('intake-question')).toContainText(/minutes.*bike repair.*take/i);
});


test('legacy resume presents a readable issue while preserving its earlier source',async({page})=>{
 const templates=await(await page.request.get('/api/studio/templates')).json();const brief=templates.templates[0].brief;const compiled=await(await page.request.post('/api/studio/compile',{data:{brief}})).json();const exp=await(await page.request.post('/api/studio/experiments',{data:{brief,model:compiled.model,model_hash:compiled.model_hash},headers:{'Idempotency-Key':`legacy-browser-${Date.now()}`}})).json();
 await page.goto('/');await page.evaluate(id=>{localStorage.setItem('fork-studio-experiment',id);localStorage.removeItem('fork-studio-conversation-draft-v1')},exp.id);await page.reload();await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();
 await expect(page.getByText('Saved earlier-format experiment.',{exact:false})).toBeVisible();await expect(page.getByRole('textbox',{name:'Describe what is happening'})).toHaveCount(0);await expect(page.locator('.st-user-message')).not.toContainText('Resource:');await expect(page.getByTestId('world-card')).toHaveCount(3);
 const saved=await(await page.request.get(`/api/studio/experiments/${exp.id}`)).json();expect(saved.brief).toBe(brief);await page.getByText('Earlier authoring source · advanced',{exact:true}).click();await expect(page.locator('.st-brief-panel pre')).toHaveText(brief);await page.reload();await expect(page.getByText('Saved earlier-format experiment.',{exact:false})).toBeVisible();await expect(page.getByTestId('intake-question')).toHaveCount(0);
});

test('a pending answer prevents a second draft being typed into the outgoing question',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Understand scenario',exact:true}).click();await page.getByRole('textbox',{name:/Your answer/}).fill('6');await page.getByRole('button',{name:'Send answer',exact:true}).click();await expect(page.getByTestId('intake-question')).toContainText(/minutes.*bike repair.*take/i);
 let release!:()=>void;const gate=new Promise<void>(resolve=>{release=resolve});await page.route('**/api/studio/intake',async route=>{const response=await route.fetch();await gate;await route.fulfill({response})});
 const input=page.getByRole('textbox',{name:/Your answer/});await input.fill('20');await page.getByRole('button',{name:'Send answer',exact:true}).click();await expect(input).toBeDisabled();release();await expect(page.getByTestId('intake-question')).toContainText('time do we have');await expect(page.getByRole('textbox',{name:/Your answer/})).toBeEnabled();
});

test('a changed replay fingerprint cannot reuse an approval from the saved authoring model',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Another operation',exact:true}).click();await understand(page);await page.getByRole('button',{name:'Run three futures',exact:true}).click();await expect(page.getByTestId('world-card')).toHaveCount(3);await page.getByRole('button',{name:'Approve selected future',exact:true}).click();await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toBeVisible();
 await page.route('**/api/studio/intake',async route=>{const response=await route.fetch();const body=await response.json();body.model_hash='f'.repeat(64);await route.fulfill({response,json:body})});await page.reload();await page.getByRole('button',{name:'Resume saved experiment',exact:true}).click();await expect(page.getByTestId('world-card')).toHaveCount(3);await expect(page.getByRole('link',{name:'Export JSON',exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'Approve selected future',exact:true})).toBeDisabled();
});

test('choosing to revise scope returns directly to the original issue editor',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Another operation',exact:true}).click();
 await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
 await expect(page.getByRole('button',{name:'I need to change the scope',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'I need to change the scope',exact:true}).click();
 await expect(page.getByRole('textbox',{name:'Describe what is happening',exact:true})).toBeVisible();
 await expect(page.getByRole('textbox',{name:'Describe what is happening',exact:true})).toBeFocused();
 await expect(page.getByRole('textbox',{name:'Describe what is happening',exact:true})).not.toHaveValue('');
 await expect(page.getByTestId('intake-question')).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Run three futures',exact:true})).toBeDisabled();
 await expect(page.getByRole('alert')).toHaveCount(0);
});
