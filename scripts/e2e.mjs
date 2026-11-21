// End-to-end checks of a built catalog in headless Chrome.
//   node scripts/e2e.mjs FILE          the small fixture catalog of tests/test_e2e.py: search, panels, views, languages
//   node scripts/e2e.mjs FILE --big    a synthetic catalog of a few thousand books: virtual list, keyboard, phone widths
// Prints one JSON line {ok, failures:[...], checks:n}. Every step waits for the page's own state, never for a fixed time.
import { launch, open } from './chrome.mjs';

const file = process.argv[2], big = process.argv.includes('--big');
const failures = []; let checks = 0;
const eq = (name, got, want) => { checks++; if (JSON.stringify(got) !== JSON.stringify(want)) failures.push(`${name}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`); };
const yes = (name, v) => { checks++; if (!v) failures.push(name); };
const js = v => JSON.stringify(v);
let c, p;

// Load the catalog (optionally with a URL hash) and wait until the page has started.
async function ready(hash = '') {
  await p.send('Page.navigate', { url: 'about:blank' });
  await p.waitFor(`location.href === 'about:blank'`, 'the blank page');
  await p.send('Page.navigate', { url: 'file://' + file + hash });
  try { await p.waitFor('!!window.__pocketshelf', 'the catalog to start', 20000); }
  catch (e) { throw new Error(`${e.message}; the page says: ${await p.eval(`document.getElementById('boot')?.textContent`)}; errors: ${p.errors.join(' | ')}`); }
}
const search = q => p.eval(`window.__pocketshelf.search(${js(q)})`);
const titles = () => p.eval(`[...document.querySelectorAll('.row[data-w] .t')].map(e=>e.textContent)`);
const sheetShown = () => p.eval(`!document.getElementById('sheet').hidden`);
const click = sel => p.eval(`document.querySelector(${js(sel)}).click()`);
const focused = () => p.eval(`(e => e ? (e.id ? '#' + e.id : e.dataset.w !== undefined ? 'w' + e.dataset.w : e.dataset.cat !== undefined ? 'cat:' + e.dataset.cat : e.tagName) : '')(document.activeElement)`);
// Type into the real search box, as a reader does, and wait for the list to follow.
async function type(text) {
  await p.eval(`(()=>{const q=document.getElementById('q');q.focus();q.value='';q.dispatchEvent(new Event('input'))})()`);
  for (const ch of text) await p.send('Input.insertText', { text: ch });
  await p.waitFor(`window.__pocketshelf.state.q === ${js(text)}`, `the query ${js(text)} to reach the list`);
}

async function small() {
  await ready();
  yes('no script errors on load', p.errors.length === 0);
  eq('all books listed', await p.eval('window.__pocketshelf.works'), 8);

  // folding: accents, Arabic variants, harakat, transliteration marks
  eq('accent-insensitive', await search('miserables'), 1);
  eq('accent-insensitive reversed', await search('Misérables'), 1);
  eq('arabic hamza/alef variants', await search('احياء علوم الدين'), 1);
  eq('arabic with harakat', await search('إِحْيَاءُ'), 1);
  eq('teh marbuta / heh', await search('مقدمه'), 1);
  eq('transliteration marks', await search('abd al rahman'), 1);
  eq('and across fields (title+author)', await search('emma austen'), 1);
  eq('a joined name finds the name written in two words', await search('عبدالله'), 1);
  eq('ibn finds a name written with bin', await search('ابن المبارك'), 1);
  eq('a direction mark in the query changes nothing', await search('عبد‏الله'), 1);
  eq('another title of the same book', await search('تفسير القرطبي'), 1);
  eq('no match', await search('zzzzqqq'), 0);
  yes('empty state shown', (await p.eval(`document.querySelector('.empty')?.textContent`) || '').length > 0);
  eq('the count is announced to screen readers', await p.eval(`document.getElementById('sum').getAttribute('role')`), 'status');

  // the real search box: typing, highlight, direction of an Arabic query in an English interface
  await type('emma');
  eq('typing filters the list', await titles(), ['Emma']);
  yes('results show highlight', await p.eval(`document.querySelectorAll('.row mark').length > 0`));
  yes('editions badge', (await p.eval(`document.querySelector('.tag.ed')?.textContent`) || '').includes('2'));
  await type('الغزالي');
  eq('an Arabic query is laid out right to left', await p.eval(`getComputedStyle(document.getElementById('q')).direction`), 'rtl');
  eq('a match is one highlight, its final hamza included', await p.eval(`(()=>{window.__pocketshelf.search('احيا');return [...document.querySelectorAll('.row .t mark')].map(m=>m.textContent)})()`), ['إحياء']);
  await type('emma');

  // keyboard: Enter goes from the search box to the first result, Enter opens it, Escape closes it and gives the focus back
  await p.press('Enter');
  eq('Enter moves to the first result', await focused(), 'w' + await p.eval(`document.querySelector('.row[data-w]').dataset.w`));
  const row = await focused();
  await p.press('Enter'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the book panel');
  yes('the page behind the panel is inert', await p.eval(`document.getElementById('app').inert`));
  eq('the panel is named by its heading', await p.eval(`document.getElementById(document.getElementById('panel').getAttribute('aria-labelledby'))?.textContent`), 'Emma');
  const hrefs = await p.eval(`[...document.querySelectorAll('#panel a.open')].map(a=>a.getAttribute('href'))`);
  eq('links are base + encoded relative path', hrefs, ['../lib/Fiction/Emma%20-%20Austen.pdf', '../lib/Fiction/Emma%202.epub']);
  await p.press('Escape'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the panel to close on Escape');
  eq('focus returns to the row', await focused(), row);
  yes('the page is usable again', !(await p.eval(`document.getElementById('app').inert`)));
  await p.press('ArrowUp');
  eq('the up arrow on the first row returns to the search box', await focused(), '#q');

  // the Back button closes a panel instead of leaving the catalog
  await click('.row[data-w]'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the book panel');
  await p.eval('history.back()'); await p.waitFor(`document.getElementById('sheet').hidden`, 'Back to close the book panel');
  yes('still in the catalog after Back', await p.eval('!!window.__pocketshelf'));
  await click('#btn-filter'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the filters');
  await p.eval('history.back()'); await p.waitFor(`document.getElementById('sheet').hidden`, 'Back to close the filters');
  yes('still in the catalog after Back from the filters', await p.eval(`!!window.__pocketshelf && location.protocol === 'file:'`));
  await click('#btn-filter'); await p.waitFor(`!!document.getElementById('f-cat')`, 'the filters');
  await p.eval(`document.getElementById('f-cat').value='Fiction'`); await click('#f-done');
  await p.waitFor(`document.getElementById('sheet').hidden && window.__pocketshelf.state.cat === 'Fiction'`, 'the filter to apply');
  yes('the filter pill says what its button removes', (await p.eval(`document.querySelector('.pill button').getAttribute('aria-label')`) || '').includes('Fiction'));
  await p.eval('history.back()'); await p.waitFor(`window.__pocketshelf.state.cat === ''`, 'Back to undo the filter');
  await click('#btn-set'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the settings');
  await click('#scrim'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the settings to close');

  // a book opened by its link (a bookmark): closing it stays on the page
  const emma = await p.eval(`document.querySelector('.row[data-w]').dataset.w`);
  await ready('#b=' + emma);
  yes('a linked book opens', await sheetShown());
  await p.press('Escape'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the linked book to close');
  yes('closing a linked book stays in the catalog', await p.eval(`!!window.__pocketshelf && location.protocol === 'file:'`));
  await ready('#b=' + emma); await click('#x'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the close button');
  yes('the close button stays in the catalog', await p.eval(`!!window.__pocketshelf && location.protocol === 'file:'`));

  // other titles, file names with a colon, and the note for pages opened from an Android file manager
  await search('القرطبي'); await click('.row[data-w]'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the book panel');
  yes('the other titles are listed', (await p.eval(`document.getElementById('panel').textContent`)).includes('تفسير القرطبي'));
  await click('#x'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the panel to close');
  await search('dune'); const dune = +(await p.eval(`document.querySelector('.row[data-w]').dataset.w`));
  await click('.row[data-w]'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the book panel');
  eq('a colon in a file name is not a URL scheme', await p.eval(`document.querySelector('#panel a.open').getAttribute('href')`), '../lib/Dune%3A%20Messiah.epub');
  yes('no file-manager note on a file:// page', !(await p.eval(`!!document.querySelector('#panel .hint')`)));
  eq('the note is for content:// pages with relative links', await p.eval(`[window.__pocketshelf.linkHint('content:', ${dune}), window.__pocketshelf.linkHint('file:', ${dune})]`), [true, false]);
  await click('#x'); await p.waitFor(`document.getElementById('sheet').hidden`, 'the panel to close');

  // views
  await search('');
  await click('#tabs [data-v=authors]'); await p.waitFor(`document.querySelectorAll('.row.hd').length > 0`, 'the authors view');
  const heads = await p.eval(`[...document.querySelectorAll('.row.hd span')].map(e=>e.textContent)`);
  yes('authors grouped by century (AH and CE)', heads.some(h => /19th/.test(h)) && heads.some(h => /9th.*AH/.test(h)) && heads.some(h => /6th.*AH/.test(h)));
  await click('#tabs [data-v=cats]'); await p.waitFor(`document.querySelectorAll('.row.cat').length >= 2`, 'the category tree');
  // the tree by keyboard: the arrow towards the text end opens a branch, the other one closes it
  const branch = `[...document.querySelectorAll('.row.cat[aria-expanded]')][0]`;
  const path = await p.eval(`${branch}.dataset.cat`), before = await p.eval(`document.querySelectorAll('.row.cat').length`);
  await p.eval(`${branch}.focus()`); await p.press('ArrowRight');
  await p.waitFor(`document.querySelectorAll('.row.cat').length > ${before}`, 'the branch to open');
  eq('an open branch says so', await p.eval(`${branch}.getAttribute('aria-expanded')`), 'true');
  eq('the branch keeps the focus', await focused(), 'cat:' + path);
  await p.press('ArrowLeft'); await p.waitFor(`document.querySelectorAll('.row.cat').length === ${before}`, 'the branch to close');
  await click('#tabs [data-v=stats]'); await p.waitFor(`document.querySelectorAll('.kpi').length >= 3`, 'the statistics');
  await click('#tabs [data-v=browse]'); await p.waitFor(`document.querySelectorAll('.row[data-w]').length > 0`, 'the list');

  // every control has a name a screen reader can say
  eq('unnamed controls', await p.eval(`[...document.querySelectorAll('button, select, input, [role=button]')].filter(e => e.offsetParent && !(e.getAttribute('aria-label') || e.textContent.trim() || e.labels?.length)).map(e => e.outerHTML.slice(0, 80))`), []);

  // state in the URL hash; a hash that does not fit the data (an old bookmark) is ignored, not fatal
  await ready('#cat=Fiction');
  eq('category filter', await p.eval('window.__pocketshelf.state.cat'), 'Fiction');
  yes('filtered list', (await titles()).length >= 1 && (await p.eval(`document.querySelectorAll('.pill').length`)) === 1);
  await ready('#au=99999&so=bogus&ce=nonsense&b=99999&v=nowhere');
  eq('a stale hash shows the whole list', await p.eval(`[window.__pocketshelf.state.author, window.__pocketshelf.state.sort, document.querySelectorAll('.row[data-w]').length, document.getElementById('sheet').hidden]`), [-1, 'rel', 8, true]);

  // interface language and direction
  await p.eval(`localStorage.setItem('pocketshelf:lang','ar')`); await ready();
  eq('arabic UI sets rtl', await p.eval(`document.documentElement.dir`), 'rtl');
  eq('the empty search box follows the interface', await p.eval(`getComputedStyle(document.getElementById('q')).direction`), 'rtl');
  await click('#tabs [data-v=cats]'); await p.waitFor(`document.querySelectorAll('.row.cat').length >= 2`, 'the category tree');
  await p.eval(`${branch}.focus()`); await p.press('ArrowLeft');
  await p.waitFor(`${branch}.getAttribute('aria-expanded') === 'true'`, 'the left arrow to open a branch in a right-to-left page');
  await p.eval(`localStorage.setItem('pocketshelf:lang','fr')`); await ready();
  eq('french UI placeholder', await p.eval(`document.getElementById('q').placeholder`), 'Titre, auteur…');
  await p.eval(`localStorage.removeItem('pocketshelf:lang')`);

  // hostile metadata is rendered as text
  await ready(); await search('img');
  await click('.row[data-w]'); await p.waitFor(`!document.getElementById('sheet').hidden`, 'the book panel');
  eq('no injected elements', await p.eval(`document.querySelectorAll('.row img, #panel img, #panel script').length`), 0);
  eq('script text stays text', await p.eval(`window.__injected === undefined`), true);
}

async function large() {
  await ready();
  const works = await p.eval('window.__pocketshelf.works');
  yes('a few thousand books', works > 2000);
  yes('only the rows near the screen exist', (await p.eval(`document.querySelectorAll('.row').length`)) < 80);
  await p.waitFor('window.__pocketshelf.indexed()', 'the search index to finish in the background');
  yes('a query narrows the list', (n => n > 0 && n < works)(await search('river')));
  await search('');

  // walk down the list with the keyboard, far past the first screen: the focus follows through every redraw
  await p.eval(`document.querySelector('.row[data-w]').focus()`);
  for (let i = 0; i < 60; i++) await p.press('ArrowDown');
  await p.waitFor(`document.activeElement?.dataset.w === '60'`, 'the focus to reach the 61st row');
  yes('the focused row is on screen', await p.eval(`(r => r.top >= 0 && r.bottom <= innerHeight)(document.activeElement.getBoundingClientRect())`));
  yes('the first rows have left the page', await p.eval(`!document.querySelector('.row[data-w="0"]')`));
  for (let i = 0; i < 5; i++) await p.press('ArrowUp');
  await p.waitFor(`document.activeElement?.dataset.w === '55'`, 'the focus to go back up');
  // scrolling by hand redraws the rows under a focused row: it keeps the focus while it is near the screen
  await p.eval(`new Promise(r => { scrollBy(0, 300); requestAnimationFrame(() => requestAnimationFrame(r)); })`);
  eq('the focus survives a scroll', await p.eval(`document.activeElement?.dataset.w`), '55');

  // authors: jump along the century ribbon
  await p.eval(`document.querySelector('#tabs [data-v=authors]').click()`);
  await p.waitFor(`document.querySelectorAll('.ribbon button').length > 3`, 'the century ribbon');
  await p.eval(`[...document.querySelectorAll('.ribbon button')].pop().click()`);
  await p.waitFor(`scrollY > 1000`, 'the jump to the last century');
  yes('the list is drawn where the jump landed', await p.eval(`document.querySelectorAll('.row.au').length > 0`));
  yes('no script errors on the desktop', p.errors.length === 0);

  // small phones, upright and sideways, in both directions: nothing is wider than the screen
  for (const [w, h, lang] of [[320, 568, 'en'], [320, 568, 'ar'], [568, 320, 'ar'], [360, 740, 'fr']]) {
    await p.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
    await p.send('Emulation.setTouchEmulationEnabled', { enabled: true });
    await p.eval(`localStorage.setItem('pocketshelf:lang', ${js(lang)})`);
    for (const view of ['', '#v=cats', '#v=authors', '#v=stats', '#q=a&b=3']) {
      await ready(view);
      eq(`no sideways scroll at ${w}x${h} ${lang} ${view || 'books'}`, await p.eval(`document.documentElement.scrollWidth <= innerWidth`), true);
    }
    if (h < 480) eq('sideways, the header scrolls away', await p.eval(`getComputedStyle(document.getElementById('top')).position`), 'static');
    else {
      await ready();
      await type('river'); await p.press('Enter');
      yes(`on a phone, Enter puts the keyboard away at ${w}x${h}`, await p.eval(`document.activeElement !== document.getElementById('q')`));
      eq(`touch targets under 24 px at ${w}x${h}`, await p.eval(`[...document.querySelectorAll('button, select, input, a')].filter(e => e.offsetParent && (r => r.width < 24 || r.height < 24)(e.getBoundingClientRect())).map(e => e.outerHTML.slice(0, 60))`), []);
    }
  }
  await p.eval(`localStorage.removeItem('pocketshelf:lang')`);
}

try {
  c = await launch();
  p = await open(c.port, { width: 1000, height: 800 });
  await (big ? large() : small());
  yes('no script errors at the end', p.errors.length === 0);
  if (p.errors.length) failures.push('errors: ' + p.errors.join(' | '));
  p.close();
} catch (e) { failures.push('exception: ' + e.message); } finally { c?.stop(); }
console.log(JSON.stringify({ ok: failures.length === 0, failures, checks }));
