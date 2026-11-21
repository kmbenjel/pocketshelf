// Search folding: the browser twin of pocketshelf/fold.py (the two are tested against each other).
const FOLD_MAP = {
  'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ٲ':'ا','ٳ':'ا','ى':'ي','ی':'ي','ې':'ي','ئ':'ي','ے':'ي','ة':'ه','ۀ':'ه','ھ':'ه','ہ':'ه','ۃ':'ه','ە':'ه','ؤ':'و',
  'ک':'ك','گ':'ك','ڪ':'ك','ڭ':'ك',
  'æ':'ae','œ':'oe','ß':'ss','ø':'o','đ':'d','ð':'d','ł':'l','þ':'th','ı':'i','ς':'σ'
};
const FOLD_MAP_RE = new RegExp('[' + Object.keys(FOLD_MAP).join('') + ']', 'g');
const FOLD_DROP_RE = /[\p{M}\p{Cf}ـءʿʾʻʼʽ'’‘`´ʹʺ]/gu;
const FOLD_DIGITS = {'٠':0,'١':1,'٢':2,'٣':3,'٤':4,'٥':5,'٦':6,'٧':7,'٨':8,'٩':9,'۰':0,'۱':1,'۲':2,'۳':3,'۴':4,'۵':5,'۶':6,'۷':7,'۸':8,'۹':9};
const FOLD_DIGITS_RE = /[٠-٩۰-۹]/g;
const FOLD_NONWORD_RE = /[^\p{L}\p{N}]+/gu;
const FOLD_ASCII_RE = /^[\x00-\x7f]*$/;
const FOLD_TAIL_RE = /[\p{M}ـء]/u;

// Folding is context-free: a string folds one character at a time, so each distinct character is worked out
// once and then looked up ('' = dropped, ' ' = a word break, else its folded letters).
const FOLD_BMP = new Array(0x10000), FOLD_ASTRAL = new Map();
function foldChar(ch) {
  let d = ch.normalize('NFKD').toLowerCase().replace(FOLD_DROP_RE, '');
  d = d.replace(FOLD_MAP_RE, c => FOLD_MAP[c]).replace(FOLD_DIGITS_RE, c => FOLD_DIGITS[c]);
  return d.replace(FOLD_NONWORD_RE, ' ');
}
// Folded text of the character that starts at s[i] (a surrogate pair counts as one character).
function foldAt(s, i) {
  const c = s.charCodeAt(i);
  if (c < 0xd800 || c > 0xdbff) { const f = FOLD_BMP[c]; return f === undefined ? (FOLD_BMP[c] = foldChar(s[i])) : f; }
  const ch = String.fromCodePoint(s.codePointAt(i));
  let f = FOLD_ASTRAL.get(ch);
  if (f === undefined) FOLD_ASTRAL.set(ch, f = foldChar(ch));
  return f;
}

function fold(s) {
  s = s == null ? '' : String(s);
  if (FOLD_ASCII_RE.test(s)) return s.toLowerCase().replace(/['`]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  let out = '', gap = false;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    let f;
    if (c < 0xd800 || c > 0xdbff) { f = FOLD_BMP[c]; if (f === undefined) f = FOLD_BMP[c] = foldChar(s[i]); }
    else { f = foldAt(s, i); if (s.codePointAt(i) > 0xffff) i++; }
    if (f === '') continue;
    if (f === ' ') { gap = true; continue; }
    if (f.length > 1 && f.indexOf(' ') >= 0) {            // a compatibility character that unfolds to several words
      for (const part of f.split(' ')) { if (part) out += (gap && out ? ' ' : '') + part; gap = true; }
      gap = f[f.length - 1] === ' ';
      continue;
    }
    out += gap && out ? ' ' + f : f;
    gap = false;
  }
  return out;
}

// Same folding, but keeps a map from folded positions back to the original string (for highlighting).
function foldMap(s) {
  s = s == null ? '' : String(s);
  let t = '', map = [];
  for (let i = 0; i < s.length; i++) {
    const d = foldAt(s, i), len = s.codePointAt(i) > 0xffff ? 2 : 1;
    for (let k = 0; k < d.length; k++) { t += d[k]; map.push([i, i + len]); }
    i += len - 1;
  }
  return { t, map };
}

// <mark> the parts of `s` that match any folded token (accent- and variant-insensitive); returns escaped HTML.
// A match is marked as one run: the vowel marks, tatweel or hamza inside it and right after it stay in the mark,
// so a vowelled Arabic word is not cut into pieces.
function highlight(s, tokens, esc) {
  s = s == null ? '' : String(s);
  if (!tokens.length || !s) return esc(s);
  const { t, map } = foldMap(s);
  const hit = new Uint8Array(s.length);
  for (const tok of tokens) {
    if (!tok) continue;
    for (let p = t.indexOf(tok); p >= 0; p = t.indexOf(tok, p + 1)) {
      const end = map[p + tok.length - 1][1];
      for (let j = map[p][0]; j < end; j++) hit[j] = 1;
    }
  }
  for (let j = 1; j < s.length; j++) if (hit[j - 1] && !hit[j] && FOLD_TAIL_RE.test(s[j])) hit[j] = 1;
  let out = '', on = false, buf = '';
  const flush = () => { if (buf) out += on ? '<mark>' + esc(buf) + '</mark>' : esc(buf); buf = ''; };
  for (let j = 0; j < s.length; j++) { if (!!hit[j] !== on) { flush(); on = !!hit[j]; } buf += s[j]; }
  flush();
  return out;
}
if (typeof module !== 'undefined') module.exports = { fold, foldMap, highlight };
