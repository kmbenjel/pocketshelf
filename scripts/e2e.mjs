// End-to-end checks of a built catalog in headless Chrome. Usage: node scripts/e2e.mjs FILE [--big]
// Prints a JSON object {ok:boolean, failures:[...], checks:n}. Expects the fixture catalog of tests/test_e2e.py.
import { launch, open } from './chrome.mjs';

const file = process.argv[2];
const port = 9360 + Math.floor(Math.random() * 30);
const c = await launch({ port });
const failures = []; let checks = 0;
const eq = (name, got, want) => { checks++; if (JSON.stringify(got) !== JSON.stringify(want)) failures.push(`${name}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`); };
const yes = (name, v) => { checks++; if (!v) failures.push(name); };
try {
  const p = await open(port, { width: 1000, height: 800 });
  const ready = async (hash = '') => { await p.goto('about:blank', 50); await p.send('Page.navigate', { url: 'file://' + file + hash }); for (let i = 0; i < 100; i++) { if (await p.eval('!!window.__pocketshelf')) return; await p.sleep(50); } };
  const search = q => p.eval(`window.__pocketshelf.search(${JSON.stringify(q)})`);
  const titles = () => p.eval(`[...document.querySelectorAll('.row[data-w] .t')].map(e=>e.textContent)`);

  await ready();
  yes('no script errors on load', p.errors.length === 0);
  eq('all books listed', await p.eval('window.__pocketshelf.works'), 5);

  // folding: accents, Arabic variants, harakat, transliteration marks
  eq('accent-insensitive', await search('miserables'), 1);
  eq('accent-insensitive reversed', await search('Misérábles'.replace('á', 'a')), 1);
  eq('arabic hamza/alef variants', await search('احياء علوم الدين'), 1);
  eq('arabic with harakat', await search('إِحْيَاءُ'), 1);
  eq('teh marbuta / heh', await search('مقدمه'), 1);
  eq('transliteration marks', await search('abd al rahman'), 1);
  eq('and across fields (title+author)', await search('emma austen'), 1);
  eq('no match', await search('zzzzqqq'), 0);
  yes('empty state shown', (await p.eval(`document.querySelector('.empty')?.textContent`) || '').length > 0);
  await search('emma');
  eq('results show highlight', await p.eval(`document.querySelectorAll('.row mark').length > 0`), true);
  await search('');

  // editions are grouped into one row
  eq('emma editions in one row', await p.eval(`(()=>{window.__pocketshelf.search('emma');return [...document.querySelectorAll('.row[data-w]')].length})()`), 1);
  yes('editions badge', (await p.eval(`document.querySelector('.tag.ed')?.textContent`) || '').includes('2'));

  // open the detail sheet; the link is the relative path under base
  await p.eval(`document.querySelector('.row[data-w]').click()`); await p.sleep(100);
  eq('sheet visible', await p.eval(`!document.getElementById('sheet').hidden`), true);
  const hrefs = await p.eval(`[...document.querySelectorAll('#panel a.open')].map(a=>a.getAttribute('href'))`);
  eq('links are base + encoded relative path', hrefs, ['../lib/Fiction/Emma%20-%20Austen.pdf', '../lib/Fiction/Emma%202.epub']);
  await p.eval(`document.getElementById('x').click()`); await p.sleep(100);
  eq('sheet closes', await p.eval(`document.getElementById('sheet').hidden`), true);

  // views
  await search('');
  await p.eval(`document.querySelector('#tabs [data-v=authors]').click()`); await p.sleep(100);
  const heads = await p.eval(`[...document.querySelectorAll('.row.hd span')].map(e=>e.textContent)`);
  yes('authors grouped by century (AH and CE)', heads.some(h => /19th/.test(h)) && heads.some(h => /9th.*AH/.test(h)) && heads.some(h => /6th.*AH/.test(h)));
  await p.eval(`document.querySelector('#tabs [data-v=cats]').click()`); await p.sleep(100);
  yes('category tree rows', (await p.eval(`document.querySelectorAll('.row.cat').length`)) >= 2);
  await p.eval(`document.querySelector('#tabs [data-v=stats]').click()`); await p.sleep(100);
  yes('stats rendered', (await p.eval(`document.querySelectorAll('.kpi').length`)) >= 3);
  await p.eval(`document.querySelector('#tabs [data-v=browse]').click()`); await p.sleep(100);

  // category filter through the URL hash
  await ready('#cat=Fiction');
  eq('category filter', await p.eval('window.__pocketshelf.state.cat'), 'Fiction');
  yes('filtered list', (await titles()).length >= 1 && (await p.eval(`document.querySelectorAll('.pill').length`)) === 1);

  // interface language and direction
  await p.eval(`localStorage.setItem('pocketshelf:lang','ar')`); await ready();
  eq('arabic UI sets rtl', await p.eval(`document.documentElement.dir`), 'rtl');
  await p.eval(`localStorage.setItem('pocketshelf:lang','fr')`); await ready();
  eq('french UI placeholder', await p.eval(`document.getElementById('q').placeholder`), 'Titre, auteur…');
  await p.eval(`localStorage.removeItem('pocketshelf:lang')`);

  // hostile metadata is rendered as text
  await ready(); await search('img');
  eq('no injected elements', await p.eval(`document.querySelectorAll('.row img, #panel img').length`), 0);
  eq('script text stays text', await p.eval(`window.__injected === undefined`), true);
  yes('no script errors at the end', p.errors.length === 0);
  if (p.errors.length) failures.push('errors: ' + p.errors.join(' | '));
  p.close();
} catch (e) { failures.push('exception: ' + e.message); } finally { c.stop(); }
console.log(JSON.stringify({ ok: failures.length === 0, failures, checks }));
