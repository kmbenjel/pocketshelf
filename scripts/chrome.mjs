// Tiny zero-dependency Chrome DevTools driver for screenshots, GIF frames and smoke tests.
// Chrome is started as a user unit (`systemd-run --user`) because it cannot start from some IDE shells.
import { execFileSync, spawn } from 'node:child_process';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.CHROME || ['/opt/google/chrome/chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => existsSync(p)) || 'google-chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function launch({ port = 9333, unit = 'pocketshelf-chrome' } = {}) {
  const prof = mkdtempSync(join(tmpdir(), 'ps-chrome-'));
  const args = ['--user', '--collect', `--unit=${unit}-${port}`, `--setenv=PATH=${process.env.PATH}`, CHROME, '--headless=new', '--disable-gpu',
    '--no-first-run', '--hide-scrollbars', `--user-data-dir=${prof}`, `--remote-debugging-port=${port}`, '--remote-allow-origins=*', 'about:blank'];
  const direct = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars', '--no-sandbox', `--user-data-dir=${prof}`, `--remote-debugging-port=${port}`, '--remote-allow-origins=*', 'about:blank'];
  if (process.env.CI || process.env.PS_DIRECT_CHROME) spawn(direct[0], direct.slice(1), { stdio: 'ignore', detached: true }).unref();
  else spawn('systemd-run', args, { stdio: 'ignore', detached: true }).unref();
  for (let i = 0; i < 60; i++) { try { await fetch(`http://127.0.0.1:${port}/json/version`); break; } catch { await sleep(250); } }
  return { port, unit: `${unit}-${port}`, stop() {
    try { execFileSync('systemctl', ['--user', 'stop', `${unit}-${port}`], { stdio: 'ignore' }); } catch { try { execFileSync('pkill', ['-f', `remote-debugging-port=${port}`]); } catch {} } } };
}

export async function open(port, { width = 1280, height = 900, mobile = false, dark = false } = {}) {
  const tab = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r));
  let id = 0; const pend = new Map();
  const errors = [];
  ws.addEventListener('message', m => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
    else if (d.method === 'Runtime.exceptionThrown') errors.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
    else if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') errors.push(d.params.args.map(a => a.value ?? a.description).join(' '));
  });
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend.set(i, d => d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result)); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: mobile ? 2 : 1, mobile });
  if (dark) await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
  const api = {
    send, errors,
    async goto(url, wait = 600) { await send('Page.navigate', { url }); await sleep(wait); },
    async eval(expr) { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; },
    async shot(file, { clip } = {}) { const r = await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 1 } } : {}) }); writeFileSync(file, Buffer.from(r.data, 'base64')); },
    async type(sel, text, delay = 0) { await api.eval(`document.querySelector(${JSON.stringify(sel)}).focus()`); for (const ch of text) { await send('Input.insertText', { text: ch }); if (delay) await sleep(delay); } },
    async click(sel) { await api.eval(`document.querySelector(${JSON.stringify(sel)}).click()`); },
    sleep,
    close() { ws.close(); },
  };
  return api;
}
