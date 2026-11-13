// Load and search timings of a built catalog in headless Chrome, optionally with a throttled CPU.
//   node bench/load_time.mjs FILE [cpuSlowdown=1] [runs=5]
import { launch, open } from '../scripts/chrome.mjs';
const [file, slow = '1', runs = '5'] = process.argv.slice(2);
const c = await launch({ port: 9350 });
const med = a => [...a].sort((x, y) => x - y)[Math.floor(a.length / 2)];
try {
  const p = await open(9350, { width: 390, height: 800, mobile: true });
  await p.send('Emulation.setCPUThrottlingRate', { rate: +slow });
  const load = [], first = [], model = [], search = {};
  const queries = ['a', 'river', 'gar', 'الكتاب', 'jardin hiv', 'zzzz'];
  for (let i = 0; i < +runs; i++) {
    await p.goto('about:blank', 100);
    const t = Date.now();
    await p.send('Page.navigate', { url: 'file://' + file });
    for (let k = 0; k < 400; k++) { if (await p.eval(`!!window.__pocketshelf`)) break; await p.sleep(25); }
    const ms = Date.now() - t;
    const r = JSON.parse(await p.eval(`JSON.stringify({ load: window.__pocketshelf.loadMs, model: window.__pocketshelf.modelMs, nav: window.__pocketshelf.readyMs })`));
    load.push(r.nav); first.push(r.load); model.push(r.model);
    for (const q of queries) {
      const ms2 = await p.eval(`(()=>{const t=performance.now();const n=window.__pocketshelf.search(${JSON.stringify(q)});return [performance.now()-t,n]})()`);
      (search[q] ||= []).push(ms2[0]); search[q + '_n'] = ms2[1];
    }
  }
  const out = { file, cpuSlowdown: +slow, runs: +runs, pageReadyMs: Math.round(med(load)), decodeMs: Math.round(med(first)), modelMs: Math.round(med(model)),
    searchMs: Object.fromEntries(queries.map(q => [q, { ms: +med(search[q]).toFixed(1), results: search[q + '_n'] }])) };
  console.log(JSON.stringify(out));
  p.close();
} finally { c.stop(); }
