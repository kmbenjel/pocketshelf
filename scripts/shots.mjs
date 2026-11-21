// Screenshots of a built catalog: node scripts/shots.mjs FILE OUTDIR
import { launch, open } from './chrome.mjs';
const [file, out] = [process.argv[2], process.argv[3] || '/tmp'];
const url = 'file://' + file;
const c = await launch();
try {
  const d = await open(c.port, { width: 1280, height: 860 });
  await d.goto(url + '#q=', 1200);
  await d.shot(`${out}/desk-home.png`);
  await d.eval(`document.getElementById('q').value='tolst';document.getElementById('q').dispatchEvent(new Event('input'))`);
  await d.sleep(500); await d.shot(`${out}/desk-search.png`);
  const m = await open(c.port, { width: 390, height: 800, mobile: true });
  await m.goto(url, 1200); await m.shot(`${out}/mob-home.png`);
  await m.eval(`document.querySelector('.row[data-w]').click()`); await m.sleep(400); await m.shot(`${out}/mob-detail.png`);
  d.close(); m.close();
} finally { c.stop(); }
