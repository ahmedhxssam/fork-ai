/**
 * Record an actual silent automated FORK walkthrough.
 * Run only after the final production build is served at FORK_URL (default :8000).
 * No fabricated frames, API mocks, overlays, or narrated-pitch claim.
 *
 * From the repository root:
 * PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" node frontend/scripts/record-demo.mjs
 */
import { mkdir, mkdtemp, stat, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve(root, '.cache/ms-playwright');
const { chromium, expect } = await import('@playwright/test');
const output = resolve(root, 'artifacts/FORK-demo-silent.webm');
const temporary = await mkdtemp(resolve(tmpdir(), 'fork-demo-recording-'));
const started = Date.now();
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 960 },
  deviceScaleFactor: 1,
  recordVideo: { dir: temporary, size: { width: 1440, height: 960 } },
});
const page = await context.newPage();
const video = page.video();
const failures = [];
page.on('pageerror', error => failures.push(error.message));
const hold = milliseconds => page.waitForTimeout(milliseconds);
let recommendationBefore, recommendationAfter, experimentId, approvedWorld;
try {
  await page.goto(process.env.FORK_URL || 'http://127.0.0.1:8000', { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /one decision/i })).toBeVisible();
  await expect(page.locator('.mode-label').filter({ hasText: /Deterministic planner/i })).toBeVisible();
  await hold(2000);

  const launched = page.waitForResponse(response =>
    response.url().endsWith('/api/experiments') && response.request().method() === 'POST');
  await page.getByRole('button', { name: /fork the mission/i }).click();
  const launchResponse = await launched;
  expect(launchResponse.ok()).toBeTruthy();
  experimentId = (await launchResponse.json()).id;
  await expect(page.getByRole('heading', { name: 'Velocity', exact: true })).toBeVisible();
  await hold(1800);
  await page.getByLabel('Playback speed').selectOption('600');
  await page.getByRole('button', { name: 'Run playback', exact: true }).click();
  await hold(3000);
  await page.getByRole('button', { name: 'Pause playback', exact: true }).click();
  await hold(800);

  await page.getByRole('button', { name: /inject disruption/i }).click();
  await page.getByRole('combobox', { name: /Vehicle/ }).selectOption('B');
  await page.getByLabel('Failure time in minutes').fill('30');
  await hold(1500);
  const shocked = page.waitForResponse(response =>
    response.url().includes(`/api/experiments/${experimentId}/disrupt`) && response.request().method() === 'POST');
  await page.getByRole('button', { name: /confirm shared breakdown/i }).click();
  const shockResponse = await shocked;
  expect(shockResponse.ok()).toBeTruthy();
  const experiment = await shockResponse.json();
  expect(experiment.disruption).toEqual({ vehicle_id: 'B', time: 1800 });
  expect(experiment.worlds.every(world => world.verification.valid)).toBeTruthy();
  await expect(page.getByText('Recovery vs. no replanning').first()).toBeVisible();
  await hold(1200);
  await page.getByRole('button', { name: 'Run playback', exact: true }).click();
  await hold(9000);
  await page.getByRole('button', { name: /verified outcomes/i }).click();
  await hold(2200);

  await page.locator('.split-evidence').scrollIntoViewIfNeeded();
  await hold(2500);
  await page.locator('.decision-section').scrollIntoViewIfNeeded();
  await hold(2000);
  recommendationBefore = await page.locator('.recommendation').innerText();
  const preferences = page.waitForResponse(response =>
    response.url().includes(`/api/experiments/${experimentId}/preferences`) && response.request().method() === 'POST');
  await page.getByRole('slider', { name: 'Use fewer resources weight' }).focus();
  await page.getByRole('slider', { name: 'Use fewer resources weight' }).press('End');
  expect((await preferences).ok()).toBeTruthy();
  await expect(page.locator('.recommendation > span').first()).toHaveText('CURRENT RECOMMENDATION');
  recommendationAfter = await page.locator('.recommendation').innerText();
  await hold(2200);

  const recommended = page.getByRole('button', { name: 'Open decision evidence →', exact: true });
  if (await recommended.count()) await recommended.click();
  else await page.getByRole('button', { name: 'Inspect Velocity', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await hold(1800);
  await page.getByRole('tab', { name: 'Referee receipt', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Independent verification', exact: true })).toBeVisible();
  await hold(2400);

  const approval = page.waitForResponse(response =>
    response.url().includes(`/api/experiments/${experimentId}/approve`) && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Approve simulated plan', exact: false }).click();
  const approvalResponse = await approval;
  expect(approvalResponse.ok()).toBeTruthy();
  approvedWorld = (await approvalResponse.json()).world_id;
  await expect(page.getByRole('link', { name: 'Export JSON', exact: true })).toBeVisible();
  await hold(2600);
  if (failures.length) throw new Error(`Browser errors: ${failures.join('; ')}`);
} catch (error) {
  await context.close();
  await browser.close();
  throw error;
}
// Playwright finalizes the actual browser capture when the page/context closes.
await context.close();
await mkdir(dirname(output), { recursive: true });
await video.saveAs(output);
await browser.close();
await rm(temporary, { recursive: true, force: true });
const result = await stat(output);
console.log(JSON.stringify({
  output, bytes: result.size, elapsedSeconds: (Date.now() - started) / 1000,
  viewport: '1440x960', format: 'webm', audio: false,
  label: 'Silent automated walkthrough of the actual local application; not the two-minute narrated pitch.',
  experimentId, shock: { vehicle_id: 'B', time: 1800 }, approvedWorld,
  recommendationBefore, recommendationAfter, pageErrors: failures,
}, null, 2));
