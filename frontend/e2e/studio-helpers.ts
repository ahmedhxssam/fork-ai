import {expect,type Page} from '@playwright/test';
export async function understand(page:Page){
  if(await page.getByRole('button',{name:'Edit original issue',exact:true}).count())await page.getByRole('button',{name:'Edit original issue',exact:true}).click();
  await page.getByRole('button',{name:'Understand scenario',exact:true}).click();
  for(let i=0;i<12;i++){
    const state=await Promise.race([page.getByText('Ready for review',{exact:true}).waitFor().then(()=> 'ready'),page.getByTestId('intake-question').waitFor().then(()=> 'question')]);
    if(state==='ready')break;
    const question=page.getByTestId('intake-question');
    const prompt=await question.getByRole('heading').textContent();
    const choices=question.locator('.st-answer-chips button');
    if(await choices.count())await choices.first().click();
    else {const value=/minutes.*take/i.test(prompt??'')?'20':prompt?.includes('time do we have')?'90':prompt?.includes('need doing')?'6':/how many.*(?:people|same time)/i.test(prompt??'')?'2':null;if(value===null)throw new Error(`No prescribed test answer for: ${prompt}`);await page.getByRole('textbox',{name:/Your answer/}).fill(value);await page.getByRole('button',{name:'Send answer',exact:true}).click()}
    await expect(page.getByRole('status').filter({hasText:'Understanding scenario'})).toHaveCount(0);
  }
  await expect(page.getByText('Ready for review',{exact:true})).toBeVisible();
  await page.getByRole('checkbox',{name:/I reviewed the plan/}).check();
}
