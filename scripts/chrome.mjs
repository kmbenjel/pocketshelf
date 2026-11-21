// Tiny zero-dependency Chrome DevTools driver for screenshots, GIF frames, benchmarks and the browser tests.
// Chrome runs as a transient user unit (`systemd-run --user`), so it has its own clean environment and stops with
// the unit; on CI, or with PS_DIRECT_CHROME=1, it is started directly instead.
// It picks its own free DevTools port, so runs side by side never collide.
import { execFileSync, spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.CHROME || ['/opt/google/chrome/chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => existsSync(p)) || 'google-chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KEYS = { ArrowLeft: 37, ArrowUp: 38, ArrowRight: 39, ArrowDown: 40, Enter: 13, Escape: 27, Tab: 9 };

export async function launch({ unit = 'pocketshelf-chrome' } = {}) {
  const prof = mkdtempSync(join(tmpdir(), 'ps-chrome-'));
  const flags = ['--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars', `--user-data-dir=${prof}`, '--remote-debugging-port=0', '--remote-allow-origins=*', 'about:blank'];
  const direct = !!(process.env.CI || process.env.PS_DIRECT_CHROME);
  const name = `${unit}-${process.pid}-${Date.now() % 1e6}`;
  const child = direct
    ? spawn(CHROME, ['--no-sandbox', ...flags], { stdio: 'ignore', detached: true })
    : spawn('systemd-run', ['--user', '--collect', `--unit=${name}`, `--setenv=PATH=${process.env.PATH}`, CHROME, ...flags], { stdio: 'ignore', detached: true });
  let failed = null;
  child.on('error', e => { failed = e; });
  child.unref();
  const stop = () => {
    // the profile is thrown away, so a direct Chrome is killed outright: nothing is left writing into the folder
    try { direct ? process.kill(-child.pid, 'SIGKILL') : execFileSync('systemctl', ['--user', 'stop', name], { stdio: 'ignore' }); } catch {}
    try { rmSync(prof, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 }); } catch {}
  };
  // Chrome writes the port it chose into its profile folder
  let port = 0;
  for (let i = 0; i < 240 && !port && !failed; i++) {
    try { port = +readFileSync(join(prof, 'DevToolsActivePort'), 'utf8').split('\n')[0]; await fetch(`http://127.0.0.1:${port}/json/version`); } catch { port = 0; await sleep(250); }
  }
  if (!port) { stop(); throw new Error(failed ? `cannot start ${direct ? CHROME : 'systemd-run'}: ${failed.message}` : `Chrome (${CHROME}) did not open a DevTools port within 60 s`); }
  return { port, unit: name, stop };
}

export async function open(port, { width = 1280, height = 900, mobile = false, dark = false } = {}) {
  let tab;
  for (let i = 0; ; i++) {
    try { tab = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json(); break; }
    catch (e) { if (i >= 20) throw e; await sleep(250); }
  }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.addEventListener('open', res); ws.addEventListener('error', () => rej(new Error('cannot connect to the tab'))); });
  let id = 0; const pend = new Map();
  const errors = [];
  ws.addEventListener('message', m => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
    else if (d.method === 'Runtime.exceptionThrown') errors.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
    else if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') errors.push(d.params.args.map(a => a.value ?? a.description).join(' '));
  });
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend.set(i, d => d.error ? rej(new Error(`${method}: ${JSON.stringify(d.error)}`)) : res(d.result)); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: mobile ? 2 : 1, mobile });
  if (mobile) await send('Emulation.setTouchEmulationEnabled', { enabled: true });
  if (dark) await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
  const api = {
    send, errors,
    async goto(url, wait = 600) { await send('Page.navigate', { url }); await sleep(wait); },
    async eval(expr) { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(`${expr.slice(0, 120)}: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`); return r.result.value; },
    // Poll an expression until it is truthy; a test waits for the page, never for a fixed time.
    async waitFor(expr, what = expr, ms = 15000) {
      for (const t = Date.now(); ;) { const v = await api.eval(expr); if (v) return v; if (Date.now() - t > ms) throw new Error(`timed out after ${ms} ms waiting for ${what}`); await sleep(20); }
    },
    async shot(file, { clip } = {}) { const r = await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 1 } } : {}) }); writeFileSync(file, Buffer.from(r.data, 'base64')); },
    async type(sel, text, delay = 0) { await api.eval(`document.querySelector(${JSON.stringify(sel)}).focus()`); for (const ch of text) { await send('Input.insertText', { text: ch }); if (delay) await sleep(delay); } },
    async press(key) {
      const k = { key, code: key, windowsVirtualKeyCode: KEYS[key], nativeVirtualKeyCode: KEYS[key] };
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', ...k }); await send('Input.dispatchKeyEvent', { type: 'keyUp', ...k });
    },
    async click(sel) { await api.eval(`document.querySelector(${JSON.stringify(sel)}).click()`); },
    sleep,
    close() { ws.close(); },
  };
  return api;
}
