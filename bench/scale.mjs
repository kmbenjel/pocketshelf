// How a catalog behaves as it grows: one JSON line per file with the page's start-up, search, sort and view
// timings, the longest time the page was blocked after its first paint, and its JS heap; in headless Chrome
// with an optionally throttled CPU.  Files are visited in turn on every run, so two builds of the same data
// given side by side are compared under the same machine load.
//   node bench/scale.mjs [cpuSlowdown=4] [runs=5] FILE...
import { launch, open } from '../scripts/chrome.mjs';
const [slow = '4', runs = '5', ...files] = process.argv.slice(2);
const c = await launch();
const med = a => [...a].sort((x, y) => x - y)[Math.floor(a.length / 2)];
const timed = body => `(()=>{const P=window.__pocketshelf,S=P.state;const t=performance.now();${body};return performance.now()-t})()`;
const KEYS = ['ready', 'decode', 'model', 'blocked', 'miss', 'word', 'arabic', 'broad', 'sortAuthor', 'authors', 'cats', 'stats', 'heapMB'];
try {
  const p = await open(c.port, { width: 390, height: 800, mobile: true });
  await p.send('Emulation.setCPUThrottlingRate', { rate: +slow });
  await p.send('Page.addScriptToEvaluateOnNewDocument', { source: `window.__long=[];new PerformanceObserver(l=>{for(const e of l.getEntries())window.__long.push([e.startTime,e.duration])}).observe({entryTypes:['longtask']});` });
  const m = files.map(() => Object.fromEntries(KEYS.map(k => [k, []]))), books = [];
  for (let i = 0; i < +runs; i++) for (const [f, file] of files.entries()) {
    await p.goto('about:blank', 100);
    await p.send('Page.navigate', { url: 'file://' + file });
    await p.waitFor('!!window.__pocketshelf', 'the catalog', 120000);
    const r = JSON.parse(await p.eval(`JSON.stringify(window.__pocketshelf)`));
    books[f] = r.books; m[f].ready.push(r.readyMs); m[f].decode.push(r.loadMs); m[f].model.push(r.modelMs);
    // leave the page alone while it builds its search index, then ask how long it was ever blocked in one go
    await p.sleep(700 * +slow);
    m[f].blocked.push(await p.eval(`Math.max(0, ...window.__long.filter(e => e[0] >= window.__pocketshelf.readyMs).map(e => e[1]))`));
    await p.eval(timed(`P.search('zzzz')`));
    m[f].miss.push(await p.eval(timed(`P.search('zzzz')`)));
    m[f].word.push(await p.eval(timed(`P.search('river')`)));
    m[f].arabic.push(await p.eval(timed(`P.search('الكتاب')`)));
    m[f].broad.push(await p.eval(timed(`P.search('a')`)));
    m[f].sortAuthor.push(await p.eval(timed(`S.sort='author';P.search('')`)));
    await p.eval(`window.__pocketshelf.state.sort='rel'`);
    for (const v of ['authors', 'cats', 'stats']) m[f][v].push(await p.eval(timed(`S.view='${v}';P.search('')`)));
    await p.eval(`window.__pocketshelf.state.view='browse';window.__pocketshelf.search('')`);
    await p.send('HeapProfiler.collectGarbage');
    m[f].heapMB.push((await p.send('Runtime.getHeapUsage')).usedSize / 1e6);
  }
  for (const [f, file] of files.entries()) {
    const out = { file: file.split('/').pop(), books: books[f], cpuSlowdown: +slow, runs: +runs };
    for (const k of KEYS) out[k + (k === 'heapMB' ? '' : 'Ms')] = +med(m[f][k]).toFixed(1);
    console.log(JSON.stringify(out));
  }
  p.close();
} finally { c.stop(); }
