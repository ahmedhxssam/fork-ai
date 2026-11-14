import { test, expect } from '@playwright/test';

test('a judge can find the operations category and open a real food-bank recovery decision', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Business & Enterprise', { exact: false }).first()).toBeVisible();
  await expect(page.getByText('Operations planning', { exact: false }).first()).toBeVisible();
  const demo = page.getByRole('link', { name: 'Try the food-bank demo', exact: true });
  await expect(demo).toBeVisible();
  const position = await demo.boundingBox();
  expect(position).not.toBeNull();
  expect(position!.y).toBeGreaterThanOrEqual(0);
  expect(position!.y + position!.height).toBeLessThanOrEqual(await page.evaluate(() => innerHeight));
  await demo.click();
  await expect(page).toHaveURL(/\?view=logistics$/);
  await expect(page.getByText('Food-bank delivery resilience', { exact: false }).first()).toBeVisible();
  await expect(page.getByText(/food.bank coordinators?/i).first()).toBeVisible();

  await page.getByRole('button', { name: /fork the mission/i }).click();
  await expect(page.getByRole('heading', { name: 'Velocity', exact: true })).toBeVisible({ timeout: 120000 });
  await page.getByRole('button', { name: /inject disruption/i }).click();
  await page.getByRole('combobox', { name: /Vehicle/ }).selectOption('A');
  await page.getByLabel('Failure time in minutes').fill('25');
  const disrupted = page.waitForResponse(response => response.url().endsWith('/disrupt') && response.request().method() === 'POST');
  await page.getByRole('button', { name: /confirm shared breakdown/i }).click();
  const response = await disrupted;
  expect(response.ok()).toBe(true);
  const experiment = await response.json();
  expect(experiment.disruption).toEqual({ vehicle_id: 'A', time: 1500 });
  expect(experiment.worlds).toHaveLength(3);
  for (const world of experiment.worlds) {
    expect(world.initial_hash).toBe(experiment.scenario.hash);
    expect(world.verification.valid).toBe(true);
    expect(world.unadapted_verification.valid).toBe(true);
  }
  await expect(page.getByText('Recovery vs. no replanning').first()).toBeVisible();
  await page.getByRole('button', { name: 'Inspect Velocity', exact: true }).click();
  await page.getByRole('tab', { name: 'Referee receipt', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Independent verification', exact: true })).toBeVisible();
  await page.getByRole('button', { name: /approve simulated plan/i }).click();
  const exported = page.getByRole('link', { name: 'Export JSON', exact: true });
  await expect(exported).toBeVisible();
  const artifact = await page.request.get((await exported.getAttribute('href'))!);
  expect(artifact.ok()).toBe(true);
  const packet = await artifact.json();
  expect(packet.synthetic).toBe(true);
  expect(packet.external_dispatch).toBe(false);
  expect(packet.disruption).toEqual({ vehicle_id: 'A', time: 1500 });
  expect(packet.decision.experiment_id).toBe(experiment.id);
  expect(packet.decision.revision).toBe(experiment.revision);
  expect(packet.decision.world_id).toBe('velocity');
  expect(packet.world.verification.valid).toBe(true);
  expect(packet.world.initial_hash).toBe(experiment.scenario.hash);
});

test('a mobile judge can reach the food-bank demo and launch it without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByText('Business & Enterprise', { exact: false }).first()).toBeVisible();
  const demo = page.getByRole('link', { name: 'Try the food-bank demo', exact: true });
  await expect(demo).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
  expect(await demo.evaluate(element => parseFloat(getComputedStyle(element).fontSize))).toBeGreaterThanOrEqual(16);
  await demo.click();
  await expect(page.getByText('Food-bank delivery resilience', { exact: false }).first()).toBeVisible();
  const launch = page.getByRole('button', { name: /fork the mission/i });
  await expect(launch).toBeEnabled();
  expect(await launch.evaluate(element => parseFloat(getComputedStyle(element).fontSize))).toBeGreaterThanOrEqual(16);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
  await launch.click();
  await expect(page.getByRole('heading', { name: 'Velocity', exact: true })).toBeVisible({ timeout: 120000 });
  await expect(page.getByRole('button', { name: /inject disruption/i })).toBeEnabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
});
