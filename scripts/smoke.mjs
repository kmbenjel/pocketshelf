import { launch, open } from './chrome.mjs';
const url = process.argv[2];
const c = await launch();
try {
  const p = await open(c.port, { width: 1280, height: 900 });
  const logs = [];
  p.send('Log.enable').catch(() => {});
  await p.goto(url, 1500);
  console.log(await p.eval('JSON.stringify({err:document.getElementById("boot").hidden?null:document.getElementById("boot").textContent, ps:window.__pocketshelf})'));
  await p.shot(process.argv[3] || '/tmp/smoke.png');
  p.close();
} finally { c.stop(); }
