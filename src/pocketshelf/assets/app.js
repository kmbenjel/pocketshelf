(async function () {
'use strict';
const $ = id => document.getElementById(id);
const store = {
  get(k, d) { try { return localStorage.getItem('pocketshelf:' + k) ?? d; } catch (_) { return d; } },
  set(k, v) { try { localStorage.setItem('pocketshelf:' + k, v); } catch (_) {} }
};
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = n => Number(n).toLocaleString('en-US');

/* ---------------------------------------------------------------------------------------------- i18n */
const T = {
  en: {
    dir: 'ltr', name: 'English', search: 'Search books, authors…', filters: 'Filters', settings: 'Settings', sort: 'Sort',
    relevance: 'Best match', title: 'Title', author: 'Author', year: 'Year', size: 'Size', added: 'Recently added',
    browse: 'Books', categories: 'Categories', authors: 'Authors', stats: 'Stats',
    n_works: { one: '{n} book', other: '{n} books' }, n_works_of: '{n} of {m} books', n_authors: { one: '{n} author', other: '{n} authors' }, n_cats: { one: '{n} category', other: '{n} categories' },
    editions: { one: '{n} edition', other: '{n} editions' }, volumes: { one: '{n} volume', other: '{n} volumes' }, open: 'Open', no_file: 'Listed without a file', edition: 'Edition', editor: 'Editor',
    publisher: 'Publisher', place: 'Place', pubyear: 'Year', series: 'Series', isbn: 'ISBN', pages: 'Pages', language: 'Language',
    format: 'Format', category: 'Category', tags: 'Tags', notes: 'Notes', ids: 'Identifiers', century: 'Century', died: 'd. {y}',
    all: 'All', only_multi: 'Only books with several editions', reset: 'Clear all', done: 'Show results', close: 'Close',
    no_results: 'Nothing found', no_results_hint: 'Try fewer words, another spelling, or clear the filters.', clear: 'Clear search and filters',
    unknown: 'Unknown date', ui_language: 'Language', theme: 'Theme', auto: 'Auto', light: 'Light', dark: 'Dark', palette: 'Palette',
    lapis: 'Lapis', paper: 'Paper', about: 'This catalog was generated {d} with pocketshelf {v}. It is one file: no server, no network.',
    all_cats: 'All categories', files: 'files', total_size: 'total size', largest: 'Largest files', top_authors: 'Most represented authors',
    by_cat: 'Books by category', by_cent: 'Authors by century', by_fmt: 'Formats', by_lang: 'Languages', by_year: 'Books by publication decade',
    quality: 'What the catalog knows', with_author: 'with an author', with_year: 'with a year', with_cat: 'with a category', with_file: 'with a file',
    with_death: 'authors with a death year', multi: 'books with several editions', loading_err: 'This browser cannot read the catalog (it needs DecompressionStream). Rebuild with --no-compress or update the browser.',
    ah: 'AH', ce: 'CE', bce: 'BCE', cent: n => ordEn(n) + ' c.', jump: 'Jump to century', books_n: { one: '{n} book', other: '{n} books' },
    pick_author: 'Show only this author', pick_cat: 'Show this category',
  },
  ar: {
    dir: 'rtl', name: 'العربية', search: 'ابحث في الكتب والمؤلفين…', filters: 'تصفية', settings: 'الإعدادات', sort: 'الترتيب',
    relevance: 'الأقرب', title: 'العنوان', author: 'المؤلف', year: 'السنة', size: 'الحجم', added: 'الأحدث إضافة',
    browse: 'الكتب', categories: 'الأقسام', authors: 'المؤلفون', stats: 'إحصاءات',
    n_works: { one: 'كتاب واحد', two: 'كتابان', few: '{n} كتب', many: '{n} كتابًا', other: '{n} كتاب' }, n_works_of: '{n} من {m} كتابًا',
    n_authors: { one: 'مؤلف واحد', two: 'مؤلفان', few: '{n} مؤلفين', many: '{n} مؤلفًا', other: '{n} مؤلف' }, n_cats: { one: 'قسم واحد', two: 'قسمان', few: '{n} أقسام', many: '{n} قسمًا', other: '{n} قسم' },
    editions: { one: 'طبعة واحدة', two: 'طبعتان', few: '{n} طبعات', many: '{n} طبعة', other: '{n} طبعة' }, volumes: { one: 'مجلد واحد', two: 'مجلدان', few: '{n} مجلدات', many: '{n} مجلدًا', other: '{n} مجلد' }, open: 'افتح', no_file: 'مُدرَج بلا ملف', edition: 'الطبعة', editor: 'المحقق',
    publisher: 'الناشر', place: 'المكان', pubyear: 'سنة النشر', series: 'السلسلة', isbn: 'ردمك', pages: 'الصفحات', language: 'اللغة',
    format: 'الصيغة', category: 'القسم', tags: 'الوسوم', notes: 'ملاحظات', ids: 'المعرّفات', century: 'القرن', died: 'ت {y}',
    all: 'الكل', only_multi: 'الكتب ذات الطبعات المتعددة فقط', reset: 'مسح الكل', done: 'اعرض النتائج', close: 'إغلاق',
    no_results: 'لا نتائج', no_results_hint: 'جرّب كلمات أقل أو إملاءً آخر، أو أزل التصفية.', clear: 'امسح البحث والتصفية',
    unknown: 'تاريخ غير معروف', ui_language: 'اللغة', theme: 'المظهر', auto: 'تلقائي', light: 'فاتح', dark: 'داكن', palette: 'الألوان',
    lapis: 'لازوردي', paper: 'ورقي', about: 'أُنشئ هذا الفهرس في {d} بأداة pocketshelf {v}. هو ملف واحد: بلا خادم ولا شبكة.',
    all_cats: 'كل الأقسام', files: 'ملفًا', total_size: 'الحجم الكلي', largest: 'أكبر الملفات', top_authors: 'أكثر المؤلفين حضورًا',
    by_cat: 'الكتب حسب القسم', by_cent: 'المؤلفون حسب القرن', by_fmt: 'الصيغ', by_lang: 'اللغات', by_year: 'الكتب حسب عقد النشر',
    quality: 'ما يعرفه الفهرس', with_author: 'لها مؤلف', with_year: 'لها سنة', with_cat: 'لها قسم', with_file: 'لها ملف',
    with_death: 'مؤلفون لهم سنة وفاة', multi: 'كتب بطبعات متعددة', loading_err: 'لا يستطيع هذا المتصفح قراءة الفهرس (يحتاج DecompressionStream). أعد البناء بخيار --no-compress أو حدّث المتصفح.',
    ah: 'هـ', ce: 'م', bce: 'ق.م', cent: n => 'القرن ' + n, jump: 'اقفز إلى قرن', books_n: { one: 'كتاب واحد', two: 'كتابان', few: '{n} كتب', many: '{n} كتابًا', other: '{n} كتاب' },
    pick_author: 'اعرض هذا المؤلف فقط', pick_cat: 'اعرض هذا القسم',
  },
  fr: {
    dir: 'ltr', name: 'Français', search: 'Titre, auteur…', filters: 'Filtres', settings: 'Réglages', sort: 'Tri',
    relevance: 'Pertinence', title: 'Titre', author: 'Auteur', year: 'Année', size: 'Taille', added: 'Ajoutés récemment',
    browse: 'Livres', categories: 'Catégories', authors: 'Auteurs', stats: 'Chiffres',
    n_works: { one: '{n} livre', other: '{n} livres' }, n_works_of: '{n} sur {m} livres', n_authors: { one: '{n} auteur', other: '{n} auteurs' }, n_cats: { one: '{n} catégorie', other: '{n} catégories' },
    editions: { one: '{n} édition', other: '{n} éditions' }, volumes: { one: '{n} volume', other: '{n} volumes' }, open: 'Ouvrir', no_file: 'Listé sans fichier', edition: 'Édition', editor: 'Éditeur scientifique',
    publisher: 'Éditeur', place: 'Lieu', pubyear: 'Année', series: 'Collection', isbn: 'ISBN', pages: 'Pages', language: 'Langue',
    format: 'Format', category: 'Catégorie', tags: 'Mots-clés', notes: 'Notes', ids: 'Identifiants', century: 'Siècle', died: 'm. {y}',
    all: 'Tous', only_multi: 'Seulement les livres en plusieurs éditions', reset: 'Tout effacer', done: 'Voir les résultats', close: 'Fermer',
    no_results: 'Aucun résultat', no_results_hint: 'Essayez moins de mots, une autre orthographe, ou retirez les filtres.', clear: 'Effacer recherche et filtres',
    unknown: 'Date inconnue', ui_language: 'Langue', theme: 'Thème', auto: 'Auto', light: 'Clair', dark: 'Sombre', palette: 'Palette',
    lapis: 'Lapis', paper: 'Papier', about: 'Ce catalogue a été généré le {d} avec pocketshelf {v}. C’est un seul fichier : ni serveur ni réseau.',
    all_cats: 'Toutes les catégories', files: 'fichiers', total_size: 'taille totale', largest: 'Plus gros fichiers', top_authors: 'Auteurs les plus présents',
    by_cat: 'Livres par catégorie', by_cent: 'Auteurs par siècle', by_fmt: 'Formats', by_lang: 'Langues', by_year: 'Livres par décennie de publication',
    quality: 'Ce que le catalogue sait', with_author: 'avec auteur', with_year: 'avec année', with_cat: 'avec catégorie', with_file: 'avec fichier',
    with_death: 'auteurs avec année de décès', multi: 'livres en plusieurs éditions', loading_err: 'Ce navigateur ne peut pas lire le catalogue (DecompressionStream requis). Reconstruisez avec --no-compress ou mettez à jour le navigateur.',
    ah: 'H', ce: 'EC', bce: 'av. J.-C.', cent: n => (n === 1 ? '1er' : n + 'e') + ' s.', jump: 'Aller au siècle', books_n: { one: '{n} livre', other: '{n} livres' },
    pick_author: 'Voir seulement cet auteur', pick_cat: 'Voir cette catégorie',
  },
};
function ordEn(n) { const m = n % 100; if (m >= 11 && m <= 13) return n + 'th'; return n + ({ 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'); }

/* ------------------------------------------------------------------------------------------------ load */
async function loadData() {
  const el = $('data'), enc = el.dataset.enc, raw = el.textContent;
  if (enc === 'json') return JSON.parse(raw);
  const bin = atob(raw), u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  const text = await new Response(new Blob([u8]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
  return JSON.parse(text);
}
const t0 = performance.now();
let D;
const uiDefault = document.documentElement.lang;
let lang = store.get('lang', null) || (new URLSearchParams(location.hash.slice(1)).get('lang')) || uiDefault;
if (!T[lang]) lang = 'en';
try { D = await loadData(); } catch (e) {
  $('boot').textContent = T[lang].loading_err; console.error(e); return;
}
const tLoad = performance.now() - t0;

/* ------------------------------------------------------------------------------------------------ model */
const A = D.a.map((a, i) => ({ i, n: a[0], d: a[1], cal: a[2] ? 'ah' : 'ce', f: '' }));
const centOf = y => y > 0 ? Math.ceil(y / 100) : y < 0 ? -Math.ceil(-y / 100) : 0;
const ceOf = (y, cal) => cal === 'ah' ? Math.round(y * 0.970229 + 621.57) : y;
A.forEach(a => { a.c = a.d ? centOf(a.d) : 0; a.sort = a.d ? ceOf(a.d, a.cal) : 1e9; a.ck = a.d ? a.cal + ':' + a.c : ''; });
const B = D.b.map((r, i) => ({ i, t: r[0], a: r[1], c: r[2], w: r[3], y: r[4], s: r[5], l: r[6], f: r[7], fl: r[8], d: r[9] || {}, mt: r[10] }));
const catHue = new Map();
const hueOf = s => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h; };
const topCat = c => c < 0 ? '' : D.c[c].split('/')[0];
const W = []; const wById = new Map();
for (const b of B) {
  b.tf = ''; b.af = '';
  let w = wById.get(b.w);
  if (!w) { w = { id: W.length, bs: [], rep: b }; wById.set(b.w, w); W.push(w); }
  w.bs.push(b);
}
for (const w of W) {
  w.h = '';
  w.size = w.bs.reduce((s, b) => s + b.s, 0);
  w.year = Math.max(...w.bs.map(b => b.y));
  w.mt = Math.max(...w.bs.map(b => b.mt));
  w.hue = w.rep.c >= 0 ? hueOf(D.c[w.rep.c]) : 210;
}
// The folded search texts are built lazily (right after the first paint, or at the first query): the page opens
// before the index exists, which is what keeps a 20,000-book catalog quick to open on a phone.
let indexed = false;
function buildIndex() {
  if (indexed) return; indexed = true;
  for (const a of A) a.f = fold(a.n);
  for (const b of B) { b.tf = fold(b.t); b.af = b.a >= 0 ? A[b.a].f : ''; }
  for (const w of W) {
    const parts = [];
    for (const b of w.bs) parts.push(b.tf, b.af, fold([b.d.e, b.d.p, b.d.pl, b.d.ed, b.d.s, b.d.i, (b.d.t || []).join(' '), b.d.x ? Object.values(b.d.x).join(' ') : '', b.c >= 0 ? D.c[b.c] : ''].join(' ')));
    w.h = parts.join(' ');
  }
}
const HASFILES = B.some(b => b.fl && b.fl.length);
const tModel = performance.now() - t0 - tLoad;
const catPaths = D.c.map(c => c.split('/'));

/* ------------------------------------------------------------------------------------------------ state */
const S = { view: 'browse', q: '', cat: '', author: -1, lang: '', fmt: '', cent: '', multi: false, sort: 'rel', open: '' };
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  S.view = ['browse', 'cats', 'authors', 'stats'].includes(p.get('v')) ? p.get('v') : 'browse';
  S.q = p.get('q') || ''; S.cat = p.get('cat') || ''; S.author = p.has('au') ? +p.get('au') : -1;
  S.lang = p.get('lg') || ''; S.fmt = p.get('fm') || ''; S.cent = p.get('ce') || ''; S.multi = p.get('mu') === '1';
  S.sort = p.get('so') || 'rel'; S.open = p.get('b') || '';
}
function writeHash(push) {
  const p = new URLSearchParams();
  if (S.view !== 'browse') p.set('v', S.view);
  if (S.q) p.set('q', S.q); if (S.cat) p.set('cat', S.cat); if (S.author >= 0) p.set('au', S.author);
  if (S.lang) p.set('lg', S.lang); if (S.fmt) p.set('fm', S.fmt); if (S.cent) p.set('ce', S.cent); if (S.multi) p.set('mu', '1');
  if (S.sort !== 'rel') p.set('so', S.sort); if (S.open) p.set('b', S.open);
  const h = p.toString() ? '#' + p.toString() : location.pathname + location.search;
  try { push ? history.pushState(null, '', h) : history.replaceState(null, '', h); } catch (_) {}
}
readHash();

/* ------------------------------------------------------------------------------------------------ helpers */
function plural(n) {
  if (lang === 'ar') { const m = n % 100; return n === 1 ? 'one' : n === 2 ? 'two' : m >= 3 && m <= 10 ? 'few' : m >= 11 ? 'many' : 'other'; }
  return n === 1 || (lang === 'fr' && n === 0) ? 'one' : 'other';
}
const tr = (k, o) => {
  let s = T[lang][k] ?? T.en[k] ?? k;
  if (typeof s === 'function') return s(o);
  if (typeof s === 'object') { const n = typeof o === 'object' ? +String(o.n).replace(/,/g, '') : +o; s = s[plural(n)] ?? s.other; }
  if (o !== undefined && typeof o === 'object') return s.replace(/\{(\w+)\}/g, (_, x) => o[x]);
  return s;
};
const bytes = n => n >= 1e9 ? (n / 1e9).toFixed(1) + ' GB' : n >= 1e6 ? (n / 1e6).toFixed(n < 1.6e7 ? 1 : 0) + ' MB' : n >= 1e3 ? Math.round(n / 1e3) + ' KB' : n ? n + ' B' : '';
const centLabel = (c, cal) => c === 0 ? tr('unknown') : c < 0 ? tr('cent', -c) + ' ' + tr('bce') : tr('cent', c) + ' ' + tr(cal);
const lifeLabel = a => !a.d ? '' : tr('died', { y: Math.abs(a.d) + ' ' + (a.d < 0 ? tr('bce') : tr(a.cal)) }) + (a.cal === 'ah' ? ' (' + ceOf(a.d, 'ah') + ' ' + tr('ce') + ')' : '');
const href = p => /^[a-z][a-z0-9+.-]*:/i.test(p) ? p : (D.m.base || '') + p.split('/').map(encodeURIComponent).join('/');
const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICON = {
  books: svg('<path d="M5 4h4v16H5zM11 4h4v16h-4zM17.5 5.5l3.5 1-4 14-3.5-1z"/>'),
  cats: svg('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'),
  authors: svg('<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.5-6 8-6s8 2 8 6"/>'),
  stats: svg('<path d="M5 20V10M12 20V4M19 20v-7"/>'),
  gear: svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>'),
  x: svg('<path d="M6 6l12 12M18 6 6 18"/>'),
};
const VIEWS = [['browse', 'books'], ['cats', 'cats'], ['authors', 'authors'], ['stats', 'stats']];

/* --------------------------------------------------------------------------------------------- filtering */
let catSet = null;
function computeCatSet() {
  if (!S.cat) return catSet = null;
  catSet = new Set(); D.c.forEach((c, i) => { if (c === S.cat || c.startsWith(S.cat + '/')) catSet.add(i); });
}
let RES = [];
function matchWork(w, toks) {
  for (let i = 0; i < toks.length; i++) if (w.h.indexOf(toks[i]) < 0) return false;
  return true;
}
function filterWorks() {
  computeCatSet();
  const toks = fold(S.q).split(' ').filter(Boolean);
  if (toks.length || S.sort === 'author') buildIndex();
  const out = [];
  for (const w of W) {
    if (toks.length && !matchWork(w, toks)) continue;
    if (S.multi && w.bs.length < 2) continue;
    if (catSet || S.author >= 0 || S.lang || S.fmt || S.cent) {
      let ok = false;
      for (const b of w.bs) {
        if (catSet && !catSet.has(b.c)) continue;
        if (S.author >= 0 && b.a !== S.author) continue;
        if (S.lang && (b.l < 0 || D.l[b.l] !== S.lang)) continue;
        if (S.fmt && (b.f < 0 || D.f[b.f] !== S.fmt)) continue;
        if (S.cent && (b.a < 0 || A[b.a].ck !== S.cent)) continue;
        ok = true; break;
      }
      if (!ok) continue;
    }
    out.push(w);
  }
  if (toks.length && S.sort === 'rel') {
    for (const w of out) {
      let s = 0;
      for (const tk of toks) {
        const p = w.rep.tf.indexOf(tk);
        if (p === 0) s += 6; else if (p > 0 && w.rep.tf[p - 1] === ' ') s += 4; else if (p > 0) s += 2;
        else if (w.rep.af.indexOf(tk) >= 0) s += 2;
      }
      if (w.rep.tf === toks.join(' ')) s += 10;
      w.score = s;
    }
    out.sort((a, b) => b.score - a.score || a.id - b.id);
  } else if (S.sort === 'author') out.sort((a, b) => (a.rep.af || '￿').localeCompare(b.rep.af || '￿') || a.id - b.id);
  else if (S.sort === 'year') out.sort((a, b) => (b.year || -1) - (a.year || -1) || a.id - b.id);
  else if (S.sort === 'size') out.sort((a, b) => b.size - a.size || a.id - b.id);
  else if (S.sort === 'added') out.sort((a, b) => b.mt - a.mt || a.id - b.id);
  RES = out;
}

/* ------------------------------------------------------------------------------------------ virtual list */
const VL = { rows: [], offs: [0], total: 0, first: -1, last: -1, ver: 0 };
const host = $('vl'), inner = $('vl-in');
function setRows(rows, heights) {
  VL.rows = rows; VL.offs = new Array(rows.length + 1); VL.offs[0] = 0;
  for (let i = 0; i < rows.length; i++) VL.offs[i + 1] = VL.offs[i] + heights(rows[i]);
  VL.total = VL.offs[rows.length]; VL.first = VL.last = -1; VL.ver++;
  renderVL();
}
function findRow(y) { let lo = 0, hi = VL.rows.length; while (lo < hi) { const m = (lo + hi) >> 1; if (VL.offs[m + 1] <= y) lo = m + 1; else hi = m; } return lo; }
function renderVL(force) {
  if (host.hidden) return;
  const top = host.getBoundingClientRect().top, vh = window.innerHeight, over = 500;
  const y0 = Math.max(0, -top - over), y1 = Math.min(VL.total, -top + vh + over);
  const first = findRow(y0), last = Math.min(VL.rows.length, findRow(y1) + 1);
  if (!force && first === VL.first && last === VL.last) return;
  VL.first = first; VL.last = last;
  inner.style.paddingTop = VL.offs[first] + 'px';
  inner.style.height = VL.total + 'px';
  let h = '';
  for (let i = first; i < last; i++) h += rowHTML(VL.rows[i]);
  inner.innerHTML = h;
}
let raf = 0;
const onScroll = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; renderVL(); }); };
addEventListener('scroll', onScroll, { passive: true });
addEventListener('resize', onScroll);

/* --------------------------------------------------------------------------------------------------- rows */
let TOK = [];
const hl = s => highlight(s, TOK, esc);
function rowHTML(r) {
  if (r.k === 'w') {
    const w = r.w, b = w.rep, a = b.a >= 0 ? A[b.a] : null, files = w.bs.reduce((n, x) => n + (Array.isArray(x.fl) ? x.fl.length : x.fl ? 1 : 0), 0);
    const ed = b.d.e || b.d.p || '';
    const tags = [];
    if (w.bs.length > 1) tags.push(`<span class="tag ed">${esc(tr('editions', { n: w.bs.length }))}</span>`);
    if (b.f >= 0) tags.push(`<span class="tag">${esc(D.f[b.f].toUpperCase())}</span>`);
    if (Array.isArray(b.fl)) tags.push(`<span class="tag">${esc(tr('volumes', { n: b.fl.length }))}</span>`);
    if (!files && HASFILES) tags.push(`<span class="tag nofile">—</span>`);
    if (w.size) tags.push(`<span>${bytes(w.size)}</span>`);
    if (w.year) tags.push(`<span>${w.year}</span>`);
    const sub = [a ? hl(a.n) : '', a && a.d ? esc(lifeLabel(a)) : ''].filter(Boolean).join(' · ');
    return `<article class="row" role="button" tabindex="0" data-w="${w.id}" style="--h:${w.hue}"><span class="t"><bdi>${hl(b.t)}</bdi></span><span class="a"><bdi>${sub}${!a && ed ? esc(ed) : ''}</bdi></span><div class="m">${tags.join('')}</div></article>`;
  }
  if (r.k === 'hd') return `<div class="row hd"><span>${esc(r.label)}</span><small>${esc(tr('n_authors', { n: num(r.n) }))}</small></div>`;
  if (r.k === 'au') {
    const a = r.a;
    return `<article class="row au" role="button" tabindex="0" data-au="${a.i}" style="--h:${a.c ? (Math.abs(a.c) * 37) % 360 : 210}"><span class="t"><bdi>${hl(a.n)}</bdi></span><span class="a"><bdi>${esc(lifeLabel(a))}${a.d ? ' · ' : ''}${esc(tr('books_n', { n: num(a.nb) }))}</bdi></span></article>`;
  }
  if (r.k === 'cat') {
    const pad = 12 + r.depth * 20;
    return `<article class="row cat" role="button" tabindex="0" data-cat="${esc(r.path)}" style="--h:${hueOf(r.path.split('/')[0])};padding-inline-start:${pad + 6}px"><span class="car ${r.open ? 'open' : ''}" data-tg="${esc(r.path)}">${r.kids ? '›' : ''}</span><span class="t"><bdi>${hl(r.name)}</bdi></span><span class="n">${num(r.n)}</span></article>`;
  }
  return '';
}
const ROWH = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--row')) || 78;

/* ----------------------------------------------------------------------------------------------- views */
const expanded = new Set();
let TREE = null;
function buildTree() {
  const root = { kids: new Map(), n: 0, path: '', name: '' };
  const count = new Map();
  for (const b of B) if (b.c >= 0) count.set(b.c, (count.get(b.c) || 0) + 1);
  count.forEach((n, ci) => {
    let node = root;
    catPaths[ci].forEach((seg, d) => {
      const path = catPaths[ci].slice(0, d + 1).join('/');
      if (!node.kids.has(seg)) node.kids.set(seg, { kids: new Map(), n: 0, path, name: seg });
      node = node.kids.get(seg); node.n += n;
    });
  });
  return root;
}
function catRows() {
  TREE = TREE || buildTree();
  const toks = fold(S.q).split(' ').filter(Boolean), rows = [];
  const matches = n => toks.every(t => fold(n.path).indexOf(t) >= 0);
  const anyMatch = n => matches(n) || [...n.kids.values()].some(anyMatch);
  const walk = (node, depth) => {
    const kids = [...node.kids.values()].sort((a, b) => a.name.localeCompare(b.name, lang));
    for (const k of kids) {
      if (toks.length && !anyMatch(k)) continue;
      const open = toks.length ? true : expanded.has(k.path);
      rows.push({ k: 'cat', path: k.path, name: k.name, n: k.n, depth, open, kids: k.kids.size > 0 });
      if (open && k.kids.size) walk(k, depth + 1);
    }
  };
  walk(TREE, 0);
  return rows;
}
function authorRows() {
  const toks = fold(S.q).split(' ').filter(Boolean);
  buildIndex();
  const nb = new Map(); for (const b of B) if (b.a >= 0) nb.set(b.a, (nb.get(b.a) || 0) + 1);
  const groups = new Map();
  for (const a of A) {
    if (!nb.has(a.i) || (toks.length && !toks.every(t => a.f.indexOf(t) >= 0))) continue;
    a.nb = nb.get(a.i);
    const key = a.ck || 'none';
    if (!groups.has(key)) groups.set(key, { key, sort: a.sort, label: a.d ? centLabel(a.c, a.cal) : tr('unknown'), list: [] });
    groups.get(key).list.push(a);
  }
  const gs = [...groups.values()].sort((x, y) => x.sort - y.sort);
  const rows = []; RIB = [];
  for (const g of gs) {
    g.list.sort((x, y) => x.f.localeCompare(y.f));
    RIB.push({ label: g.label, n: g.list.length, at: rows.length });
    rows.push({ k: 'hd', label: g.label, n: g.list.length });
    for (const a of g.list) rows.push({ k: 'au', a });
  }
  return rows;
}
let RIB = [];

function render(reset) {
  const v = S.view;
  TOK = fold(S.q).split(' ').filter(Boolean);
  $('stats').hidden = v !== 'stats'; host.hidden = v === 'stats';
  $('sortbox').hidden = v !== 'browse';
  document.querySelectorAll('[data-v]').forEach(b => b.setAttribute('aria-current', b.dataset.v === v ? 'page' : 'false'));
  const old = document.querySelector('.ribbon'); if (old) old.remove();
  if (v === 'browse') {
    filterWorks();
    const total = W.length;
    $('sum').textContent = RES.length === total ? tr('n_works', { n: num(total) }) : tr('n_works_of', { n: num(RES.length), m: num(total) });
    if (!RES.length) { inner.innerHTML = emptyHTML(); inner.style.height = 'auto'; inner.style.paddingTop = '0'; VL.rows = []; VL.total = 0; }
    else setRows(RES.map(w => ({ k: 'w', w })), () => ROWH());
  } else if (v === 'cats') {
    const rows = catRows();
    $('sum').textContent = tr('n_cats', { n: num(D.c.length) });
    if (!rows.length) { inner.innerHTML = emptyHTML(); inner.style.height = 'auto'; inner.style.paddingTop = '0'; VL.rows = []; VL.total = 0; } else setRows(rows, () => 52);
  } else if (v === 'authors') {
    const rows = authorRows();
    $('sum').textContent = tr('n_authors', { n: num(rows.filter(r => r.k === 'au').length) });
    if (RIB.length > 1) {
      const rb = document.createElement('div'); rb.className = 'ribbon'; rb.setAttribute('aria-label', tr('jump'));
      rb.innerHTML = RIB.map((r, i) => `<button type="button" data-rib="${i}">${esc(r.label)}<small>${num(r.n)}</small></button>`).join('');
      host.parentNode.insertBefore(rb, host);
    }
    if (!rows.length) { inner.innerHTML = emptyHTML(); inner.style.height = 'auto'; inner.style.paddingTop = '0'; VL.rows = []; VL.total = 0; } else setRows(rows, r => r.k === 'hd' ? 48 : 68);
  } else {
    $('sum').textContent = '';
    renderStats();
  }
  renderActive();
  if (reset) window.scrollTo(0, 0);
}
function emptyHTML() { return `<div class="empty"><h2>${esc(tr('no_results'))}</h2><div>${esc(tr('no_results_hint'))}</div><button type="button" id="clr">${esc(tr('clear'))}</button></div>`; }

function renderActive() {
  const pills = [];
  const add = (k, label) => pills.push(`<span class="pill"><span>${esc(label)}</span><button type="button" data-rm="${k}" aria-label="${esc(tr('close'))}">×</button></span>`);
  if (S.view === 'browse') {
    if (S.cat) add('cat', S.cat.split('/').join(' › '));
    if (S.author >= 0) add('author', A[S.author].n);
    if (S.lang) add('lang', S.lang.toUpperCase());
    if (S.fmt) add('fmt', S.fmt.toUpperCase());
    if (S.cent) { const [cal, c] = S.cent.split(':'); add('cent', centLabel(+c, cal)); }
    if (S.multi) add('multi', tr('only_multi'));
  }
  $('active').innerHTML = pills.join('');
  const n = ['cat', 'lang', 'fmt', 'cent'].filter(k => S[k]).length + (S.author >= 0) + S.multi;
  $('btn-filter').innerHTML = esc(tr('filters')) + (n ? ` <b>${n}</b>` : '');
  $('btn-filter').hidden = S.view !== 'browse';
}

/* ---------------------------------------------------------------------------------------------- stats */
function renderStats() {
  const books = B.length, works = W.length, files = B.reduce((n, b) => n + (Array.isArray(b.fl) ? b.fl.length : b.fl ? 1 : 0), 0);
  const size = B.reduce((n, b) => n + b.s, 0);
  const cnt = (keyf) => { const m = new Map(); for (const b of B) { const k = keyf(b); if (k !== null && k !== undefined && k !== '') m.set(k, (m.get(k) || 0) + 1); } return [...m.entries()].sort((a, b) => b[1] - a[1]); };
  const bars = (list, max, hue) => { const mx = Math.max(1, ...list.map(x => x[1])); return `<div class="bars">${list.slice(0, max).map(([k, n]) => `<div class="bar"><span class="l"><bdi>${esc(k)}</bdi></span><span class="tr"><i style="width:${Math.max(2, 100 * n / mx)}%;--h:${hue ?? hueOf(String(k))}"></i></span><span class="v">${num(n)}</span></div>`).join('')}</div>`; };
  const pct = (n, of) => of ? Math.round(100 * n / of) + '%' : '0%';
  const withAuthor = B.filter(b => b.a >= 0).length, withYear = B.filter(b => b.y).length, withCat = B.filter(b => b.c >= 0).length, withFile = B.filter(b => b.fl && b.fl.length).length;
  const aDeath = A.filter(a => a.d).length, multi = W.filter(w => w.bs.length > 1).length;
  const bycat = cnt(b => b.c >= 0 ? topCat(b.c) : '');
  const byfmt = cnt(b => b.f >= 0 ? D.f[b.f].toUpperCase() : ''), bylang = cnt(b => b.l >= 0 ? D.l[b.l].toUpperCase() : '');
  const cents = new Map(); for (const a of A) if (a.d) { const k = a.ck; if (!cents.has(k)) cents.set(k, { n: 0, a }); cents.get(k).n++; }
  const cl = [...cents.values()].sort((x, y) => x.a.sort - y.a.sort);
  const mxC = Math.max(1, ...cl.map(c => c.n));
  const dec = cnt(b => b.y > 1000 ? Math.floor(b.y / 10) * 10 : null).sort((a, b) => a[0] - b[0]);
  const big = [...B].sort((a, b) => b.s - a.s).slice(0, 5).filter(b => b.s);
  const nb = new Map(); for (const b of B) if (b.a >= 0) nb.set(b.a, (nb.get(b.a) || 0) + 1);
  const topA = [...nb.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([i, n]) => [A[i].n, n]);
  const kp = (n, l) => `<div class="kpi"><b>${n}</b><span>${esc(l)}</span></div>`;
  const q = (n, l) => `<div class="bar"><span class="l">${esc(l)}</span><span class="tr"><i style="width:${books ? 100 * n / books : 0}%;--h:150"></i></span><span class="v">${pct(n, books)}</span></div>`;
  $('stats').innerHTML = `<div class="kpis">${kp(num(works), tr('browse'))}${files ? kp(num(files), tr('files')) : ''}${size ? kp(bytes(size), tr('total_size')) : ''}${kp(num(A.length), tr('authors'))}${kp(num(D.c.length), tr('categories'))}</div>
  ${bycat.length ? `<section class="card"><h2>${esc(tr('by_cat'))}</h2>${bars(bycat, 12)}</section>` : ''}
  ${cl.length ? `<section class="card"><h2>${esc(tr('by_cent'))}</h2><div class="cols">${cl.map(c => `<div title="${esc(centLabel(c.a.c, c.a.cal))}: ${c.n}"><em>${c.n}</em><i style="height:${Math.max(3, 82 * c.n / mxC)}px"></i><em>${c.a.c < 0 ? -c.a.c + 'b' : c.a.c}${c.a.cal === 'ah' ? 'ه' : ''}</em></div>`).join('')}</div></section>` : ''}
  ${dec.length > 1 ? `<section class="card"><h2>${esc(tr('by_year'))}</h2><div class="cols">${dec.map(([d, n]) => `<div title="${d}s: ${n}"><em>${n}</em><i style="height:${Math.max(3, 82 * n / Math.max(...dec.map(x => x[1])))}px"></i><em>${String(d).slice(2)}</em></div>`).join('')}</div></section>` : ''}
  <div class="kpis"><section class="card" style="grid-column:1/-1"><h2>${esc(tr('quality'))}</h2><div class="bars">${q(withAuthor, tr('with_author'))}${q(withYear, tr('with_year'))}${q(withCat, tr('with_cat'))}${q(withFile, tr('with_file'))}</div><p class="small">${num(aDeath)} / ${num(A.length)} ${esc(tr('with_death'))} · ${num(multi)} ${esc(tr('multi'))}</p></section></div>
  ${byfmt.length || bylang.length ? `<section class="card"><h2>${esc(tr('by_fmt'))} · ${esc(tr('by_lang'))}</h2>${bars(byfmt, 6, 210)}${bylang.length ? '<br>' + bars(bylang, 6, 30) : ''}</section>` : ''}
  ${topA.length ? `<section class="card"><h2>${esc(tr('top_authors'))}</h2>${bars(topA, 8, 270)}</section>` : ''}
  ${big.length ? `<section class="card"><h2>${esc(tr('largest'))}</h2>${bars(big.map(b => [b.t, b.s]), 5, 20).replace(/<span class="v">([\d,]+)<\/span>/g, (m, n) => `<span class="v">${bytes(+n.replace(/,/g, ''))}</span>`)}</section>` : ''}`;
}

/* --------------------------------------------------------------------------------------------- sheet */
let lastFocus = null;
function showSheet(html) {
  lastFocus = document.activeElement;
  $('panel-in').innerHTML = html; $('sheet').hidden = false; $('panel').scrollTop = 0; $('panel').focus();
  document.body.style.overflow = 'hidden';
}
function hideSheet() { $('sheet').hidden = true; document.body.style.overflow = ''; if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true }); }
function kv(pairs) { const rows = pairs.filter(p => p[1]); return rows.length ? `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd><bdi>${esc(v)}</bdi></dd>`).join('')}</dl>` : ''; }
function filesHTML(b) {
  const fl = b.fl;
  if (!fl || !fl.length) return `<p class="small">${esc(tr('no_file'))}</p>`;
  if (!Array.isArray(fl)) return `<a class="open" href="${esc(href(fl))}">${esc(tr('open'))} ${D.f[b.f] ? esc(D.f[b.f].toUpperCase()) : ''}${b.s ? ' · ' + bytes(b.s) : ''}</a>`;
  return `<ul class="vols">${fl.map(([lab, p, sz]) => p ? `<li><a href="${esc(href(p))}"><span>${esc(lab)}</span><small>${bytes(sz)}</small></a></li>` : `<li><span>${esc(lab)}<small>${bytes(sz)}</small></span></li>`).join('')}</ul>`;
}
function openWork(id, push = true) {
  const w = W[id]; if (!w) return;
  const b0 = w.rep, a = b0.a >= 0 ? A[b0.a] : null;
  let h = `<h2><bdi>${esc(b0.t)}</bdi></h2>`;
  if (a) h += `<p class="by"><button type="button" data-pa="${a.i}" title="${esc(tr('pick_author'))}"><bdi>${esc(a.n)}</bdi></button>${a.d ? ' · ' + esc(lifeLabel(a)) : ''}</p>`;
  w.bs.forEach((b, k) => {
    const d = b.d, label = [d.ed, d.e, d.p, b.y || ''].filter(Boolean).join(' · ');
    const cat = b.c >= 0 ? `<button type="button" class="by" style="all:unset;cursor:pointer;color:var(--accent);text-decoration:underline" data-pc="${esc(D.c[b.c])}" title="${esc(tr('pick_cat'))}">${esc(D.c[b.c].split('/').join(' › '))}</button>` : '';
        h += `<div class="${w.bs.length > 1 ? 'ed-card' : ''}">${w.bs.length > 1 ? `<h3>${esc(tr('edition'))} ${k + 1}${label ? ' · ' + esc(label) : ''}</h3>` : ''}${filesHTML(b)}${kv([
      [tr('editor'), d.e], [tr('publisher'), [d.p, d.pl].filter(Boolean).join(' – ')], [tr('edition'), d.ed], [tr('pubyear'), b.y || ''], [tr('series'), d.s], [tr('isbn'), d.i],
      [tr('pages'), d.pg ? num(d.pg) : ''],       [tr('format'), b.f >= 0 ? D.f[b.f].toUpperCase() : ''], [tr('language'), b.l >= 0 ? D.l[b.l].toUpperCase() : ''], [tr('size'), bytes(b.s)],
      [tr('tags'), (d.t || []).join(' · ')], [tr('notes'), d.n], [tr('ids'), d.x ? Object.entries(d.x).map(([k2, v]) => k2 + ': ' + v).join(' · ') : ''],
    ])}${cat ? `<dl class="kv"><dt>${esc(tr('category'))}</dt><dd>${cat}</dd></dl>` : ''}</div>`;
  });
  showSheet(h);
  S.open = String(id); writeHash(push);
}
function closeWork() { if (S.open) { S.open = ''; hideSheet(); writeHash(false); } }

function openFilters() {
  const opts = (items, cur) => `<option value="">${esc(tr('all'))}</option>` + items.map(([v, l]) => `<option value="${esc(v)}"${v === cur ? ' selected' : ''}>${esc(l)}</option>`).join('');
  const cats = [...new Set(D.c.flatMap(c => { const p = c.split('/'); return p.map((_, i) => p.slice(0, i + 1).join('/')); }))].sort((a, b) => a.localeCompare(b, lang)).map(c => [c, ' '.repeat(c.split('/').length - 1) + c.split('/').pop()]);
  const cents = [...new Map(A.filter(a => a.d).sort((x, y) => x.sort - y.sort).map(a => [a.ck, centLabel(a.c, a.cal)])).entries()];
  showSheet(`<h2>${esc(tr('filters'))}</h2>
   <label class="field"><span>${esc(tr('category'))}</span><select id="f-cat">${opts(cats, S.cat)}</select></label>
   ${D.l.length ? `<label class="field"><span>${esc(tr('language'))}</span><select id="f-lang">${opts(D.l.map(l => [l, l.toUpperCase()]), S.lang)}</select></label>` : ''}
   ${D.f.length > 1 ? `<label class="field"><span>${esc(tr('format'))}</span><select id="f-fmt">${opts(D.f.map(l => [l, l.toUpperCase()]), S.fmt)}</select></label>` : ''}
   ${cents.length ? `<label class="field"><span>${esc(tr('century'))}</span><select id="f-cent">${opts(cents, S.cent)}</select></label>` : ''}
   <label class="check"><input type="checkbox" id="f-multi"${S.multi ? ' checked' : ''}><span>${esc(tr('only_multi'))}</span></label>
   <div class="row2"><button class="ghost" type="button" id="f-reset">${esc(tr('reset'))}</button><button class="go" type="button" id="f-done">${esc(tr('done'))}</button></div>`);
  const apply = () => { S.cat = $('f-cat').value; S.lang = $('f-lang') ? $('f-lang').value : ''; S.fmt = $('f-fmt') ? $('f-fmt').value : ''; S.cent = $('f-cent') ? $('f-cent').value : ''; S.multi = $('f-multi').checked; };
  $('f-done').onclick = () => { apply(); hideSheet(); writeHash(true); render(true); };
  $('f-reset').onclick = () => { S.cat = S.lang = S.fmt = S.cent = ''; S.multi = false; S.author = -1; hideSheet(); writeHash(true); render(true); };
}
function openSettings() {
  const seg = (key, items, cur) => `<div class="seg" data-seg="${key}">${items.map(([v, l]) => `<button type="button" data-val="${v}" aria-pressed="${v === cur}">${esc(l)}</button>`).join('')}</div>`;
  showSheet(`<h2>${esc(tr('settings'))}</h2>
   <div class="field"><span>${esc(tr('ui_language'))}</span>${seg('lang', Object.keys(T).map(k => [k, T[k].name]), lang)}</div>
   <div class="field"><span>${esc(tr('theme'))}</span>${seg('theme', [['auto', tr('auto')], ['light', tr('light')], ['dark', tr('dark')]], store.get('theme', 'auto'))}</div>
   <div class="field"><span>${esc(tr('palette'))}</span>${seg('palette', [['lapis', tr('lapis')], ['paper', tr('paper')]], store.get('palette', 'lapis'))}</div>
   <p class="foot">${esc(tr('about', { d: D.m.gen, v: D.m.ver }))}<br>${num(B.length)} · ${tLoad.toFixed(0)} ms</p>`);
}

/* -------------------------------------------------------------------------------------------- chrome */
function applyChrome() {
  const L = T[lang], root = document.documentElement;
  root.lang = lang; root.dir = L.dir;
  const th = store.get('theme', 'auto'); if (th === 'auto') root.removeAttribute('data-theme'); else root.dataset.theme = th;
  root.dataset.palette = store.get('palette', 'lapis');
  $('ttl').textContent = D.m.t; document.title = D.m.t;
  $('q').placeholder = L.search; $('q').value = S.q;
  $('btn-set').innerHTML = ICON.gear; $('btn-set').setAttribute('aria-label', L.settings);
  $('x').innerHTML = ICON.x; $('x').setAttribute('aria-label', L.close);
  const labels = { browse: tr('browse'), cats: tr('categories'), authors: tr('authors'), stats: tr('stats') };
  const tabs = VIEWS.map(([v, ic]) => `<button type="button" data-v="${v}">${ICON[ic]}<span>${esc(labels[v])}</span></button>`).join('');
  $('nav').innerHTML = tabs; $('tabs').innerHTML = tabs;
  $('sort-l').textContent = L.sort;
  $('sort').innerHTML = ['rel', 'title', 'author', 'year', 'size', 'added'].map(k => `<option value="${k}"${S.sort === k ? ' selected' : ''}>${esc(tr(k === 'rel' ? 'relevance' : k === 'title' ? 'title' : k))}</option>`).join('');
}

/* ------------------------------------------------------------------------------------------- events */
const reRender = () => { applyChrome(); render(false); };
function go(view) { S.view = view; S.open = ''; $('sheet').hidden = true; document.body.style.overflow = ''; writeHash(true); render(true); }
document.addEventListener('click', e => {
  const t = e.target;
  const v = t.closest('[data-v]'); if (v) return go(v.dataset.v);
  const rm = t.closest('[data-rm]');
  if (rm) { const k = rm.dataset.rm; if (k === 'author') S.author = -1; else if (k === 'multi') S.multi = false; else S[k] = ''; writeHash(true); return render(true); }
  if (t.closest('#clr')) { S.q = ''; S.cat = S.lang = S.fmt = S.cent = ''; S.author = -1; S.multi = false; $('q').value = ''; writeHash(true); return render(true); }
  const rib = t.closest('[data-rib]'); if (rib) { const at = RIB[+rib.dataset.rib].at; window.scrollTo(0, host.getBoundingClientRect().top + scrollY + VL.offs[at] - 150); return; }
  const pa = t.closest('[data-pa]'); if (pa) { S.open = ''; hideSheet(); S.view = 'browse'; S.author = +pa.dataset.pa; S.q = ''; writeHash(true); return render(true); }
  const pc = t.closest('[data-pc]'); if (pc) { S.open = ''; hideSheet(); S.view = 'browse'; S.cat = pc.dataset.pc; S.q = ''; writeHash(true); return render(true); }
  const seg = t.closest('[data-seg] button');
  if (seg) {
    const key = seg.parentNode.dataset.seg, val = seg.dataset.val;
    if (key === 'lang') { lang = val; store.set('lang', val); } else store.set(key, val);
    applyChrome(); render(false); openSettings(); return;
  }
  if (t.closest('#scrim') || t.closest('#x')) { if (S.open) { history.length > 1 && location.hash.includes('b=') ? history.back() : closeWork(); } else hideSheet(); return; }
  if (t.closest('#btn-set')) return openSettings();
  if (t.closest('#btn-filter')) return openFilters();
  const tg = t.closest('[data-tg]');
  if (tg && S.view === 'cats') { const p = tg.dataset.tg; expanded.has(p) ? expanded.delete(p) : expanded.add(p); const y = scrollY; render(false); scrollTo(0, y); return; }
  const wr = t.closest('[data-w]'); if (wr) return openWork(+wr.dataset.w);
  const au = t.closest('[data-au]'); if (au) { S.view = 'browse'; S.author = +au.dataset.au; S.q = ''; writeHash(true); return render(true); }
  const ct = t.closest('[data-cat]'); if (ct) { S.view = 'browse'; S.cat = ct.dataset.cat; S.q = ''; writeHash(true); return render(true); }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !$('sheet').hidden) { S.open ? (history.back()) : hideSheet(); return; }
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('.row[role=button]')) { e.preventDefault(); e.target.click(); }
  if (e.key === '/' && document.activeElement !== $('q') && $('sheet').hidden) { e.preventDefault(); $('q').focus(); }
});
let qt = 0;
$('q').addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { S.q = $('q').value; writeHash(false); render(true); }, 60); });
$('sort').addEventListener('change', () => { S.sort = $('sort').value; writeHash(false); render(true); });
addEventListener('popstate', () => { const wasOpen = S.open; readHash(); $('q').value = S.q; if (!S.open) { $('sheet').hidden = true; document.body.style.overflow = ''; } render(false); if (S.open) openWork(+S.open, false); });
matchMedia('(prefers-color-scheme:dark)').addEventListener?.('change', () => {});

applyChrome();
$('boot').hidden = true; $('app').hidden = false;
render(false);
if (S.open && W[+S.open]) openWork(+S.open, false);
setTimeout(buildIndex, 30);
window.__pocketshelf = { readyMs: performance.now(), loadMs: tLoad, modelMs: tModel, books: B.length, works: W.length, search: q => { S.q = q; render(true); return RES.length; }, state: S };
})();
