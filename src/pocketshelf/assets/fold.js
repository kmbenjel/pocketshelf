// Search folding: the browser twin of pocketshelf/fold.py (the two are tested against each other).
const FOLD_MAP = {
  'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ٲ':'ا','ٳ':'ا','ى':'ي','ی':'ي','ې':'ي','ئ':'ي','ة':'ه','ۀ':'ه','ھ':'ه','ہ':'ه','ؤ':'و','ک':'ك','گ':'ك',
  'æ':'ae','œ':'oe','ß':'ss','ø':'o','đ':'d','ð':'d','ł':'l','þ':'th','ı':'i'
};
const FOLD_MAP_RE = new RegExp('[' + Object.keys(FOLD_MAP).join('') + ']', 'g');
const FOLD_DROP_RE = /[\p{M}ـءʿʾʻʼʽ'’‘`´ʹʺ]/gu;
const FOLD_DIGITS = {'٠':0,'١':1,'٢':2,'٣':3,'٤':4,'٥':5,'٦':6,'٧':7,'٨':8,'٩':9,'۰':0,'۱':1,'۲':2,'۳':3,'۴':4,'۵':5,'۶':6,'۷':7,'۸':8,'۹':9};
const FOLD_DIGITS_RE = /[٠-٩۰-۹]/g;
const FOLD_NONWORD_RE = /[^\p{L}\p{N}]+/gu;
const FOLD_ASCII_RE = /^[\x00-\x7f]*$/;

function fold(s) {
  s = s == null ? '' : String(s);
  if (FOLD_ASCII_RE.test(s)) return s.toLowerCase().replace(/['`]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  s = s.normalize('NFKD').toLowerCase().replace(FOLD_DROP_RE, '');
  s = s.replace(FOLD_MAP_RE, c => FOLD_MAP[c]).replace(FOLD_DIGITS_RE, c => FOLD_DIGITS[c]);
  return s.replace(FOLD_NONWORD_RE, ' ').trim();
}

// Same folding, but keeps a map from folded positions back to the original string (for highlighting).
function foldMap(s) {
  s = s == null ? '' : String(s);
  let t = '', map = [], i = 0;
  for (const ch of s) {
    const len = ch.length;
    let d = ch.normalize('NFKD').toLowerCase().replace(FOLD_DROP_RE, '');
    d = d.replace(FOLD_MAP_RE, c => FOLD_MAP[c]).replace(FOLD_DIGITS_RE, c => FOLD_DIGITS[c]).replace(FOLD_NONWORD_RE, ' ');
    for (let k = 0; k < d.length; k++) { t += d[k]; map.push([i, i + len]); }
    i += len;
  }
  return { t, map };
}

// <mark> the parts of `s` that match any folded token (accent- and variant-insensitive); returns escaped HTML.
function highlight(s, tokens, esc) {
  s = s == null ? '' : String(s);
  if (!tokens.length || !s) return esc(s);
  const { t, map } = foldMap(s);
  const hit = new Uint8Array(s.length);
  for (const tok of tokens) {
    if (!tok) continue;
    for (let p = t.indexOf(tok); p >= 0; p = t.indexOf(tok, p + 1)) {
      for (let k = p; k < p + tok.length; k++) for (let j = map[k][0]; j < map[k][1]; j++) hit[j] = 1;
    }
  }
  let out = '', on = false, buf = '';
  const flush = () => { if (buf) out += on ? '<mark>' + esc(buf) + '</mark>' : esc(buf); buf = ''; };
  for (let j = 0; j < s.length; j++) { if (!!hit[j] !== on) { flush(); on = !!hit[j]; } buf += s[j]; }
  flush();
  return out;
}
if (typeof module !== 'undefined') module.exports = { fold, foldMap, highlight };
