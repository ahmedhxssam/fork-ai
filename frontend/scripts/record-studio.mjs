// Records the real localhost Scenario Studio UI. No fixtures, overlays or API writes.
// Run from the repository root: node frontend/scripts/record-studio.mjs
import { mkdtemp, mkdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';

const exec = promisify(execFile);
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const origin = process.env.FORK_URL ?? 'http://127.0.0.1:8000';
const output = resolve(root, 'artifacts/FORK-studio-demo-silent.webm');
const report = resolve(root, 'docs/STUDIO_RECORDING_REPORT.md');
const temporary = await mkdtemp(resolve(tmpdir(), 'fork-studio-recording-'));
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(root, '.cache/ms-playwright');
// Playwright resolves its browser cache while importing its registry.
const { chromium, expect } = await import('@playwright/test');
const phases = [];
const external = [];
const errors = [];
const experiments = [];
let browser;
let context;
let started;
const mark = label => {
  const seconds = Number(((performance.now() - started) / 1000).toFixed(2));
  phases.push({ seconds, label });
  process.stdout.write(`${seconds.toFixed(2)}s ${label}\n`);
};

try {
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    recordVideo: { dir: temporary, size: { width: 1440, height: 1000 } },
    acceptDownloads: true,
  });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === new URL(origin).origin) return route.continue();
    external.push(url.href);
    return route.abort();
  });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  const video = page.video();
  started = performance.now();
  const pause = ms => page.waitForTimeout(ms);
  const focus = async locator => {
    await locator.evaluate(element => element.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    await pause(650);
  };
  const click = name => page.getByRole('button', { name, exact: true }).click();
  const compile = async () => {
    await click('Compile brief');
    await expect(page.getByText('Ready for review', { exact: true })).toBeVisible();
  };
  const launch = async () => {
    const response = page.waitForResponse(r => r.url().endsWith('/api/studio/experiments') && r.request().method() === 'POST');
    await click('Run three futures');
    const data = await (await response).json();
    expect(data.mode).toBe('deterministic');
    expect(data.worlds).toHaveLength(3);
    expect(data.worlds.every(world => world.verification.valid && world.segments.length > 0)).toBe(true);
    experiments.push(data);
    await expect(page.getByTestId('world-card')).toHaveCount(3);
    await focus(page.locator('.st-results'));
    return data;
  };

  await page.goto(origin, { waitUntil: 'networkidle' });
  await expect(page.getByRole('textbox', { name: 'Scenario brief' })).not.toHaveValue('');
  mark('Prefilled repair-clinic brief');
  await pause(3300);

  await compile();
  await focus(page.locator('.st-workbench'));
  mark('Compiled resources and dependency map');
  await pause(3700);
  await page.getByText('Explicit defaults & assumptions', { exact: false }).click();
  await focus(page.locator('.st-review-panel .st-detail').nth(1));
  mark('Explicit defaults and checkpointable-work assumption');
  await pause(2200);
  await page.getByText('Explicit defaults & assumptions', { exact: false }).click();

  await launch();
  mark('Three real repair-clinic futures');
  await pause(4300);
  await click('Play playback');
  await pause(1500);
  await click('Pause playback');
  await page.getByRole('slider', { name: 'Playback minute' }).press('End');

  await focus(page.locator('.st-controls-grid'));
  await click('Add outage');
  await page.getByLabel('Outage 1 start', { exact: true }).fill('5');
  await page.getByLabel('Outage 1 duration', { exact: true }).fill('25');
  mark('A real resource outage draft: starts 5m, lasts 25m, capacity lost 1');
  await pause(2600);
  const rerunResponse = page.waitForResponse(r => r.url().endsWith('/events') && r.request().method() === 'POST');
  await click('Apply outages & rerun');
  const shocked = await (await rerunResponse).json();
  expect(shocked.revision).toBe(2);
  expect(shocked.model.events).toHaveLength(1);
  expect(shocked.worlds.every(world => world.verification.valid)).toBe(true);
  await expect(page.getByText('Revision 2', { exact: true })).toBeVisible();
  await focus(page.locator('.st-results'));
  mark('Rerun: common outage, actual metrics and locked-replay comparison');
  await pause(4400);

  await focus(page.locator('.st-workbench'));
  await click('IT service response');
  mark('Switched to the IT service response brief');
  await pause(1800);
  await compile();
  await focus(page.locator('.st-workbench'));
  mark('Compiled a distinct IT response model');
  await pause(2600);
  const it = await launch();
  expect(it.model_hash).not.toBe(experiments[0].model_hash);
  mark('Three actual IT response futures');
  await pause(3300);

  await focus(page.locator('.st-inspector'));
  await page.getByRole('tab', { name: 'Independent receipt', exact: true }).click();
  await expect(page.getByText('Independent verification passed', { exact: false }).first()).toBeVisible();
  mark('Independent replay receipt and evidence hashes');
  await pause(4000);
  await focus(page.locator('.st-approval'));
  await click('Approve selected future');
  const exportLink = page.getByRole('link', { name: 'Export JSON', exact: true });
  await expect(exportLink).toBeVisible();
  mark('Approved the selected current-revision future');
  await pause(1600);
  const downloadPromise = page.waitForEvent('download');
  await exportLink.click();
  const download = await downloadPromise;
  const exportPath = resolve(temporary, 'approved.json');
  await download.saveAs(exportPath);
  const exported = JSON.parse(await readFile(exportPath, 'utf8'));
  expect(exported.approved.revision).toBe(exported.revision);
  expect(exported.approved.model_hash).toBe(exported.model_hash);
  const selected = exported.worlds.find(world => world.id === exported.approved.world_id);
  expect(selected.verification.valid).toBe(true);
  expect(exported.approved.evidence_hash).toBe(selected.verification.evidence_hash);
  mark('Downloaded and checked the actual approved JSON');
  await pause(2000);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);

  await context.close();
  context = undefined;
  const staged = resolve(temporary, 'complete.webm');
  await video.saveAs(staged);
  await browser.close();
  browser = undefined;
  const { stdout } = await exec('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate', '-of', 'json', staged]);
  const probe = JSON.parse(stdout);
  const duration = Number(probe.format.duration);
  expect(duration).toBeGreaterThanOrEqual(40);
  expect(duration).toBeLessThanOrEqual(60);
  expect(probe.streams.some(stream => stream.codec_type === 'audio')).toBe(false);
  await exec('ffmpeg', ['-v', 'error', '-i', staged, '-f', 'null', '-'], { maxBuffer: 1024 * 1024 });
  const bytes = (await stat(staged)).size;
  const sha256 = createHash('sha256').update(await readFile(staged)).digest('hex');
  await mkdir(dirname(output), { recursive: true });
  await rename(staged, output);
  const metricRows = data => data.worlds.map(world => `| ${data.model.title} (revision ${data.revision}) | ${world.name} | ${world.verification.metrics.on_time}/${world.verification.metrics.total} | ${world.verification.metrics.completed} | ${world.verification.metrics.cost_cents} |`).join('\n');
  await writeFile(report, `# Scenario Studio recording evidence\n\nRecorded ${new Date().toISOString()} from \`${origin}\` with the repository's Playwright Chromium.\n\n- Video: [FORK-studio-demo-silent.webm](../artifacts/FORK-studio-demo-silent.webm)\n- Duration: **${duration.toFixed(3)} seconds**.\n- Size: **${bytes.toLocaleString('en-US')} bytes**.\n- Frame: **1440 × 1000**, ${probe.streams[0].codec_name}, ${probe.streams[0].r_frame_rate} fps.\n- Audio streams: **0**. This is the requested silent visual walkthrough, not a narrated two-minute pitch. Use [PITCH.md](PITCH.md) for the longer spoken presentation.\n- SHA256: \`${sha256}\`.\n\n## Recorded journey\n\n${phases.map(phase => `- ${phase.seconds.toFixed(2)}s: ${phase.label}.`).join('\n')}\n\nThe script uses visible application controls and native scrolling. It records actual server results, with no response fixtures, substituted metrics, fake overlays, title cards, speed changes or edited cuts. Browser storage starts empty. The temporary JSON download was checked against its approval revision, model hash and independent evidence hash, then removed during cleanup. It is not a separate permanent deliverable.\n\n## Actual computed outcomes in this take\n\n| Run | Future | On time | Completed | Cost (integer cents) |\n| --- | --- | --- | --- | --- |\n${metricRows(experiments[0])}\n${metricRows(shocked)}\n${metricRows(it)}\n\nOutage applied to the repair clinic's first resource pool: start 5m, duration 25m, capacity lost 1. The IT response run is a fresh model and does not inherit that clinic outage. All three futures in each recorded run passed their returned independent verification. No preferred winner or positive recovery gain is required by the script.\n\n## Verification and limits\n\n- Playwright asserted three nonempty verified schedules in each original run and verified the shocked run. It checked that the IT response model differs from the clinic model.\n- Playwright checked the downloaded JSON's approval revision, model hash and selected-world evidence hash.\n- No external-origin browser requests were allowed or observed; no page errors were observed.\n- \`ffprobe\` confirmed duration, dimensions, codec and absence of audio. \`ffmpeg -v error -i VIDEO -f null -\` decoded the complete file successfully.\n- The recording is evidence of this localhost browser journey and synthetic deterministic computation. It does not establish deployment, competition submission, organizer eligibility, field performance, arbitrary-language understanding or a runtime model-provider integration.\n- Sample-frame visual inspection is recorded separately after generation; media decoding alone does not establish visual readability.\n\n## Reproduce\n\nServe the current frontend and API on \`http://127.0.0.1:8000\`, then run \`node frontend/scripts/record-studio.mjs\` from the repository root. The script uses existing local dependencies and browser binaries, finalizes video only after its assertions and complete decode succeed, closes the browser in \`finally\`, and removes temporary recording/download files. It creates new stored experiments through normal UI actions and does not erase existing experiments.\n`);
  process.stdout.write(JSON.stringify({ output, report, duration, bytes, sha256, probe, phases }, null, 2) + '\n');
} finally {
  if (context) await context.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
  await rm(temporary, { recursive: true, force: true });
}
