// Screenshots and GIF frames for the README. Usage: node scripts/make_media.mjs DEMO_ALL.html DEMO_AR.html OUTDIR
import { mkdirSync } from 'node:fs';
import { launch, open } from './chrome.mjs';

const [all, ar, out] = process.argv.slice(2);
mkdirSync(`${out}/frames`, { recursive: true });
const c = await launch();
const setQ = async (p, q) => { await p.eval(`(()=>{const i=document.getElementById('q');i.value=${JSON.stringify(q)};i.dispatchEvent(new Event('input'))})()`); await p.sleep(160); };
try {
  // --- stills -----------------------------------------------------------------------------------------------
  const d = await open(c.port, { width: 1280, height: 800 });
  await d.goto('file://' + all, 1000); await d.eval('location.reload()'); await d.sleep(900);
  await setQ(d, 'moby'); await d.eval(`document.querySelector('.row[data-w]').click()`); await d.sleep(500);
  await d.shot(`${out}/desktop-editions.png`);
  await d.eval(`document.getElementById('x').click()`); await setQ(d, 'shakespeare'); await d.sleep(300);
  await d.shot(`${out}/desktop-search.png`);
  const m = await open(c.port, { width: 390, height: 800, mobile: true });
  await m.goto('file://' + all, 800); await m.eval('location.reload()'); await m.sleep(900);
  await setQ(m, 'dickens'); await m.shot(`${out}/phone-search.png`);
  const dk = await open(c.port, { width: 390, height: 800, mobile: true, dark: true });
  await dk.goto('file://' + all + '#v=authors', 800); await dk.eval('location.reload()'); await dk.sleep(900);
  await dk.shot(`${out}/phone-authors-dark.png`);
  const a = await open(c.port, { width: 390, height: 800, mobile: true });
  await a.goto('file://' + ar, 800); await a.eval('location.reload()'); await a.sleep(900);
  await a.shot(`${out}/phone-ar-home.png`);
  await setQ(a, 'الغزالي'); await a.shot(`${out}/phone-ar-search.png`);
  await a.goto('file://' + ar + '#v=stats', 800); await a.eval('location.reload()'); await a.sleep(900);
  await a.shot(`${out}/phone-ar-stats.png`);
  await a.goto('file://' + ar + '#v=cats', 800); await a.eval('location.reload()'); await a.sleep(900);
  await a.shot(`${out}/phone-ar-cats.png`);
  const dar = await open(c.port, { width: 1280, height: 800 });
  await dar.goto('file://' + ar + '#v=authors', 800); await dar.eval('location.reload()'); await dar.sleep(900);
  await dar.shot(`${out}/desktop-ar-authors.png`);

  // --- GIF frames: a phone-sized window, 1x scale, typing three searches -----------------------------------
  const g = await open(c.port, { width: 390, height: 640 });
  await g.goto('file://' + all, 800); await g.eval('location.reload()'); await g.sleep(900);
  let n = 0;
  const frame = async (repeat = 1) => { for (let k = 0; k < repeat; k++) await g.shot(`${out}/frames/f${String(n++).padStart(3, '0')}.png`); };
  const typeSeq = async (text, endHold = 12) => {
    for (let i = 1; i <= [...text].length; i++) { await setQ(g, [...text].slice(0, i).join('')); await frame(1); }
    await frame(endHold);
    await setQ(g, ''); await frame(3);
  };
  await frame(8);
  await typeSeq('frankenst');           // prefix search
  await typeSeq('miserables');          // accents: finds "Les Misérables"
  await typeSeq('احياء علوم');           // Arabic folding: finds "إحياء علوم الدين"
  await typeSeq('tolstoy anna', 14);    // two words, any order, across title and author
  d.close(); m.close(); dk.close(); a.close(); dar.close(); g.close();
} finally { c.stop(); }
