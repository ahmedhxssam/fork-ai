import { test, expect } from '@playwright/test';

test('computed fork, shared shock, evidence and revision-bound approval', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /one decision/i })).toBeVisible();
  await page.getByRole('button', { name: /fork the mission/i }).click();
  await expect(page.getByRole('heading', { name: 'Velocity', exact: true })).toBeVisible({ timeout: 120000 });
  await expect(page.getByRole('heading', { name: 'Resilience', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Equity', exact: true })).toBeVisible();
  await page.getByRole('button', { name: /inject disruption/i }).click();
  await page.getByLabel('Failure time in minutes').fill('25');
  await page.getByRole('button', { name: /confirm shared breakdown/i }).click();
  await expect(page.getByText('Recovery vs. no replanning').first()).toBeVisible({ timeout: 120000 });
  await page.getByRole('button', { name: 'Inspect Velocity' }).click();
  await page.getByRole('tab', { name: 'Referee receipt' }).click();
  await expect(page.getByText('Independent verification', { exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Routes & custody' }).click();
  await page.getByRole('button', { name: /approve simulated plan/i }).click();
  await expect(page.getByRole('link', { name: 'Export JSON' })).toBeVisible();
  const href=await page.getByRole('link', { name: 'Export JSON' }).getAttribute('href');
  const artifact=await page.request.get(href!);
  expect(artifact.status()).toBe(200);
  expect(artifact.headers()['content-type']).toContain('json');
});
