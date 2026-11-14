// Genuine local conversation walkthrough. No fixtures, overlays or direct API writes.
// Run after serving the frozen application: node frontend/scripts/record-conversation.mjs
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
const output = resolve(root, 'artifacts/FORK-conversation-demo-silent.webm');
const report = resolve(root, 'docs/CONVERSATION_RECORDING_REPORT.md');
// A new recording must not silently erase an earlier take.
try { await stat(output); throw new Error(`Refusing to overwrite existing video: ${output}`); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const temporary = await mkdtemp(resolve(tmpdir(), 'fork-conversation-recording-'));
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(root, '.cache/ms-playwright');
const { chromium, expect } = await import('@playwright/test');
const phases = [], external = [], errors = [], badResponses = [], experiments = [];
let browser, context, started;
const sha = value => createHash('sha256').update(value).digest('hex');
const canonical = value => JSON.stringify(value, (_key, item) => item && typeof item === 'object' && !Array.isArray(item) ? Object.fromEntries(Object.entries(item).sort(([a], [b]) => a.localeCompare(b, 'en'))) : item);
const mark = label => {
  const seconds = Number(((performance.now() - started) / 1000).toFixed(2));
  phases.push({ seconds, label });
  process.stdout.write(`${seconds.toFixed(2)}s ${label}\n`);
};

try {
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1,
    recordVideo: { dir: temporary, size: { width: 1440, height: 1000 } }, acceptDownloads: true });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === new URL(origin).origin) return route.continue();
    external.push(url.href); return route.abort();
  });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.status() >= 400) badResponses.push(`${response.status()} ${response.url()}`); });
  const video = page.video(); started = performance.now();
  const pause = ms => page.waitForTimeout(ms);
  const focus = async (locator, block = 'start') => {
    await locator.evaluate((element, position) => element.scrollIntoView({ behavior: 'smooth', block: position }), block);
    await pause(650);
  };
  const click = name => page.getByRole('button', { name, exact: true }).click();
  const intakeAction = async action => {
    const pending = page.waitForResponse(r => r.url().endsWith('/api/studio/intake') && r.request().method() === 'POST');
    await action(); const response = await pending; expect(response.ok()).toBe(true); return response.json();
  };
  const question = page.getByTestId('intake-question');
  const answer = async (text, nextPrompt) => {
    const input = page.getByRole('textbox', { name: /Your answer/ });
    await expect(input).toBeEnabled(); await input.fill(text); await pause(800);
    const data = await intakeAction(() => input.press('Enter'));
    await expect(question).toContainText(nextPrompt); await pause(1100); return data;
  };
  const review = async expected => {
    await expect(page.getByRole('button', { name: 'Run three futures', exact: true })).toBeDisabled();
    await focus(question, 'center'); mark('Explicit simplified-scope question and visible limits'); await pause(1800);
    const ready = await intakeAction(() => click('Use this simplified scope'));
    expect(ready.ready).toBe(true); expect(ready.model.resources[0].capacity).toBe(expected.staff);
    expect(ready.model.tasks).toHaveLength(6); expect(ready.model.tasks.every(task => task.duration === 45)).toBe(true);
    expect(ready.model.horizon).toBe(expected.horizon); expect(ready.model_hash).toBe(sha(canonical(ready.model)));
    await expect(page.getByText('Ready for review', { exact: true })).toBeVisible();
    await focus(page.locator('.st-review-panel')); mark(`Reviewable actual model: ${expected.staff} people, six 45-minute jobs, ${expected.horizon} minutes`);
    await pause(1900); const checkbox = page.getByRole('checkbox', { name: /I reviewed the plan/ });
    await focus(checkbox, 'center'); await checkbox.check(); await pause(750); return ready;
  };
  const run = async (ready, expectedComplete) => {
    const pending = page.waitForResponse(r => r.url().endsWith('/api/studio/experiments') && r.request().method() === 'POST');
    await click('Run three futures'); const response = await pending; expect(response.ok()).toBe(true); const data = await response.json();
    expect(data.mode).toBe('deterministic'); expect(data.worlds).toHaveLength(3);
    expect(data.model_hash).toBe(ready.model_hash); expect(data.authoring.model_hash).toBe(ready.model_hash);
    expect(data.authoring.brief_hash).toBe(ready.brief_hash); expect(data.authoring.answers).toEqual(ready.accepted_answers);
    for (const world of data.worlds) {
      expect(world.model_hash).toBe(data.model_hash); expect(world.segments.length).toBeGreaterThan(0);
      expect(world.verification.valid).toBe(true); expect(world.verification.checks.every(check => check.passed)).toBe(true);
      expect(world.verification.metrics.completed).toBe(expectedComplete); expect(world.verification.metrics.on_time).toBe(expectedComplete);
      expect(world.verification.evidence_hash).toMatch(/^[0-9a-f]{64}$/);
    }
    experiments.push(data); await expect(page.getByTestId('world-card')).toHaveCount(3); await focus(page.locator('.st-results'));
    mark(`Three real independently checked futures: each completes ${expectedComplete}/6`); await pause(3400); return data;
  };

  await page.goto(origin, { waitUntil: 'networkidle' });
  const brief = page.getByRole('textbox', { name: 'Describe what is happening', exact: true });
  await expect(brief).toHaveValue(/two volunteers/);
  mark('Ordinary incomplete repair-clinic description'); await pause(2200);
  const first = await intakeAction(() => click('Understand scenario'));
  expect(first.ready).toBe(false); await expect(question).toBeVisible(); mark('Focused missing-work question'); await pause(1600);
  await answer('Six bikes', 'take'); mark('Plain answer: six bikes');
  await answer('About 45 minutes each', 'time'); mark('Plain answer: about 45 minutes each');
  await answer('We have two hours', 'simplified'); mark('Plain answer: two hours, used as 120 minutes');
  const firstReady = await review({ staff: 2, horizon: 120 }); const firstRun = await run(firstReady, 4);

  await focus(page.locator('.st-examples')); await click('Conflicting details'); await focus(brief, 'center');
  await expect(brief).toHaveValue(/two technicians.*three technicians.*one hour.*90 minutes/);
  mark('Ordinary conflict example: two versus three technicians, one hour versus 90 minutes'); await pause(1800);
  const staffing = await intakeAction(() => click('Understand scenario'));
  expect(staffing.questions[0].conflict).toBe(true); expect(staffing.questions[0].choices.map(c => c.value)).toEqual(['2', '3']);
  await expect(question).toContainText('two technicians'); await expect(question).toContainText('three technicians');
  await focus(question, 'center'); mark('Both staffing source claims remain quoted'); await pause(2000);
  const timing = await intakeAction(() => question.getByRole('button', { name: '3 people', exact: true }).click());
  expect(timing.questions[0].conflict).toBe(true); expect(timing.questions[0].choices.map(c => c.value)).toEqual(['60', '90']);
  await expect(question).toContainText('one hour'); await expect(question).toContainText('90 minutes');
  await focus(question, 'center'); mark('Both time-window source claims remain quoted'); await pause(2000);
  await intakeAction(() => question.getByRole('button', { name: '90 minutes', exact: true }).click());
  mark('Person resolves conflicts with three technicians and 90 minutes');
  const secondReady = await review({ staff: 3, horizon: 90 }); const secondRun = await run(secondReady, 6);
  expect(secondRun.model_hash).not.toBe(firstRun.model_hash);

  await focus(page.locator('.st-inspector')); await page.getByRole('tab', { name: 'Independent receipt', exact: true }).click();
  await expect(page.getByText('Independent verification passed', { exact: false }).first()).toBeVisible();
  mark('Independent replay receipt, checks and current evidence hashes'); await pause(2500);
  await focus(page.locator('.st-approval'), 'center');
  const approvalResponse = page.waitForResponse(r => r.url().endsWith('/approve') && r.request().method() === 'POST');
  await click('Approve selected future'); expect((await approvalResponse).ok()).toBe(true);
  const exportLink = page.getByRole('link', { name: 'Export JSON', exact: true }); await expect(exportLink).toBeVisible();
  mark('Human approval bound to the selected current simulated future'); await pause(1000);
  const downloadPromise = page.waitForEvent('download'); await exportLink.click(); const download = await downloadPromise;
  const exportPath = resolve(temporary, 'approved.json'); await download.saveAs(exportPath);
  const exported = JSON.parse(await readFile(exportPath, 'utf8'));
  expect(exported.id).toBe(secondRun.id); expect(exported.approved.revision).toBe(exported.revision);
  expect(exported.approved.model_hash).toBe(exported.model_hash); expect(exported.model_hash).toBe(secondReady.model_hash);
  const selected = exported.worlds.find(world => world.id === exported.approved.world_id);
  expect(selected.verification.valid).toBe(true); expect(exported.approved.evidence_hash).toBe(selected.verification.evidence_hash);
  mark('Actual approved JSON downloaded and checked');
  await pause(Math.max(1500, 56000 - (performance.now() - started)));
  expect(external).toEqual([]); expect(errors).toEqual([]); expect(badResponses).toEqual([]);

  await context.close(); context = undefined;
  const staged = resolve(temporary, 'complete.webm'); await video.saveAs(staged);
  await browser.close(); browser = undefined;
  const { stdout } = await exec('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate', '-of', 'json', staged]);
  const probe = JSON.parse(stdout), duration = Number(probe.format.duration);
  expect(duration).toBeGreaterThanOrEqual(45); expect(duration).toBeLessThanOrEqual(65);
  expect(probe.streams.some(stream => stream.codec_type === 'audio')).toBe(false);
  expect(probe.streams[0].width).toBe(1440); expect(probe.streams[0].height).toBe(1000);
  await exec('ffmpeg', ['-v', 'error', '-i', staged, '-f', 'null', '-'], { maxBuffer: 1024 * 1024 });
  const bytes = (await stat(staged)).size, sha256 = sha(await readFile(staged));
  await mkdir(dirname(output), { recursive: true }); await rename(staged, output);
  const metricRows = data => data.worlds.map(world => `| ${data.id} | ${world.name} | ${data.model.resources[0].capacity} | ${data.model.horizon} | ${world.verification.metrics.on_time}/6 | ${world.verification.metrics.completed} |`).join('\n');
  await writeFile(report, `# Conversation walkthrough recording evidence\n\nRecorded ${new Date().toISOString()} from \`${origin}\` using repository Playwright Chromium, fresh browser storage, and the frozen locally served application.\n\n- Video: [FORK-conversation-demo-silent.webm](../artifacts/FORK-conversation-demo-silent.webm)\n- Duration: **${duration.toFixed(3)} seconds**.\n- Size: **${bytes.toLocaleString('en-US')} bytes**.\n- Frame: **1440 × 1000**, ${probe.streams[0].codec_name}, ${probe.streams[0].r_frame_rate} fps.\n- Audio streams: **0**. This is a silent visual walkthrough, with no narration or soundtrack.\n- SHA256: \`${sha256}\`.\n\n## Recorded journey\n\nThe following are script action timestamps, not frame-accurate media cues; browser recording starts before navigation orchestration.\n\n${phases.map(phase => `- ${phase.seconds.toFixed(2)}s: ${phase.label}.`).join('\n')}\n\nThe first actual built-in prompt has two volunteers and missing work quantity, duration and available time. Visible plain answers are “Six bikes”, “About 45 minutes each” and “We have two hours”. The conflict prompt visibly supplies two versus three technicians and one hour versus 90 minutes; the person selects three people and 90 minutes. Both journeys explicitly accept simplified scope and check the model-review consent before a real run. Equal policy outcomes remain visible.\n\nThe script uses application controls and native scrolling. There are no fixtures, substituted metrics, overlays, title cards, edited cuts, speed changes or direct API mutations. API responses are observed only to assert the actual UI actions. Normal actions create new saved experiments without erasing old ones. The temporary actual JSON download is checked and removed during cleanup.\n\n## Actual computed outcomes\n\n| Experiment | Future | Capacity | Horizon (minutes) | On time | Completed |\n| --- | --- | --- | --- | --- | --- |\n${experiments.map(metricRows).join('\n')}\n\nFirst model SHA256: \`${firstReady.model_hash}\`. Second model SHA256: \`${secondReady.model_hash}\`. They differ. All six displayed futures have valid independent receipts, with every returned check passed.\n\n## Executed checks and limits\n\n- Playwright checked actual capacity, six tasks, 45-minute durations, 120/90-minute model horizons, and canonical model hashes. Staffing conflict choices were 2/3; time conflict choices were 60/90. Both original claims were asserted visibly quoted.\n- Launch authoring answers and brief/model hashes match the accepted interview. Every world has segments, the current model hash, a valid receipt and expected hand-derived completion totals: four for two people over 120 minutes, six for three people over 90 minutes.\n- Actual downloaded JSON matches the second experiment, current approval revision, model hash and selected independent evidence hash.\n- External-origin browser requests were blocked; none were observed. No browser page errors or HTTP responses of 400 or higher were observed.\n- \`ffprobe\` confirmed duration, dimensions, codec and absence of audio. \`ffmpeg -v error -i VIDEO -f null -\` decoded the complete video successfully.\n- Sample-frame visual inspection: pending separate inspection after generation.\n- This records localhost synthetic deterministic planning. It does not establish deployment, offline use, competition submission, eligibility, field performance, arbitrary-language understanding or a connected model provider. No real dispatch or external messaging occurs.\n\n## Reproduce\n\nServe the frozen current frontend and API at \`http://127.0.0.1:8000\`, then run \`node frontend/scripts/record-conversation.mjs\` from the repository root. The script refuses to overwrite an existing take. Move an earlier video to a separately named archive before intentional re-recording. It saves the finalized video before browser shutdown and only promotes a take after assertions, probing and complete decoding pass.\n`);
  process.stdout.write(JSON.stringify({ output, report, duration, bytes, sha256, probe, phases }, null, 2) + '\n');
} finally {
  if (context) await context.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
  await rm(temporary, { recursive: true, force: true });
}
