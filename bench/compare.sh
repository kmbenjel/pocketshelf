#!/usr/bin/env bash
# Head-to-head on 20,000 synthetic books: pocketshelf vs Calibre (content server, CSV catalog) vs Komga.
# Run it on a throw-away Linux machine (it downloads ~350 MB and starts servers):  bash bench/compare.sh [N] [WORKDIR]
# Needs: python3, curl, java 17+ (for Komga; skipped without it), xz, tar. Prints one JSON line per measurement.
set -euo pipefail
N="${1:-20000}"; WORK="${2:-$HOME/ps-compare}"; HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$WORK"; cd "$WORK"
export PYTHONPATH="$HERE/src"
now() { date +%s.%N; }
dur() { python3 -c "print(round($(now)-$1,2))"; }
rss() { ps -o rss= -p "$1" | awk '{printf "%d", $1/1024}'; }
emit() { echo "$1"; }

# 1. the books: a CSV catalog and N one-page PDFs (so file-based servers have real files to scan)
python3 "$HERE/bench/make_inputs.py" "$N" "$WORK/inputs"

# 2. pocketshelf: build from the folder (reads PDF metadata) and from the CSV
s=$(now); python3 -m pocketshelf build "$WORK/inputs/library" -o "$WORK/ps-folder.html" --no-cache >/dev/null 2>&1
emit "{\"tool\":\"pocketshelf\",\"step\":\"build from $N PDFs\",\"seconds\":$(dur "$s"),\"output_bytes\":$(stat -c %s "$WORK/ps-folder.html")}"
s=$(now); python3 -m pocketshelf build "$WORK/inputs/catalog.csv" -o "$WORK/ps-catalog.html" >/dev/null 2>&1
emit "{\"tool\":\"pocketshelf\",\"step\":\"build from CSV\",\"seconds\":$(dur "$s"),\"output_bytes\":$(stat -c %s "$WORK/ps-catalog.html")}"

# 3. Calibre
if [ ! -d calibre ]; then
  V=$(curl -fsSL https://api.github.com/repos/kovidgoyal/calibre/releases/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
  curl -fsSL -o calibre.txz "https://download.calibre-ebook.com/$V/calibre-$V-x86_64.txz" && mkdir calibre && tar -xf calibre.txz -C calibre && echo "$V" > calibre/VERSION
fi
emit "{\"tool\":\"calibre\",\"version\":\"$(cat calibre/VERSION)\",\"installed_mb\":$(du -sm calibre | cut -f1),\"download_mb\":$(( $(stat -c %s calibre.txz) / 1048576 ))}"
rm -rf calibre-lib
s=$(now); ./calibre/calibre-debug "$HERE/bench/calibre_make_library.py" -- "$WORK/inputs/catalog.csv" "$WORK/calibre-lib" >/dev/null 2>&1
emit "{\"tool\":\"calibre\",\"step\":\"import $N records\",\"seconds\":$(dur "$s")}"
s=$(now); QT_QPA_PLATFORM=offscreen timeout 900 ./calibre/calibredb --library-path "$WORK/calibre-lib" catalog "$WORK/calibre-catalog.csv" >/dev/null 2>&1 || true
emit "{\"tool\":\"calibre\",\"step\":\"calibredb catalog (CSV)\",\"seconds\":$(dur "$s"),\"output_bytes\":$(stat -c %s "$WORK/calibre-catalog.csv" 2>/dev/null || echo 0)}"
s=$(now); QT_QPA_PLATFORM=offscreen ./calibre/calibre-server --port 18080 --disable-use-bonjour "$WORK/calibre-lib" >/dev/null 2>&1 & CP=$!
until curl -fs -o /dev/null http://127.0.0.1:18080/mobile; do sleep 0.2; done
emit "{\"tool\":\"calibre\",\"step\":\"content server start to first page\",\"seconds\":$(dur "$s"),\"rss_mb\":$(rss $CP)}"
t=$(curl -s -o /dev/null -w '%{time_total} %{size_download}' "http://127.0.0.1:18080/ajax/search?num=50&query=river")
emit "{\"tool\":\"calibre\",\"step\":\"content server search 'river' (50 rows)\",\"seconds\":\"${t% *}\",\"response_bytes\":${t#* }}"
kill $CP 2>/dev/null || true

# 4. Komga (needs Java 17+)
if command -v java >/dev/null; then
  if [ ! -f komga.jar ]; then
    URL=$(curl -fsSL https://api.github.com/repos/gotson/komga/releases/latest | python3 -c "import sys,json;print([a['browser_download_url'] for a in json.load(sys.stdin)['assets'] if a['name'].endswith('.jar')][0])")
    curl -fsSL -o komga.jar "$URL"
  fi
  emit "{\"tool\":\"komga\",\"jar_mb\":$(( $(stat -c %s komga.jar) / 1048576 ))}"
  rm -rf komga-conf; mkdir komga-conf
  s=$(now); java -jar komga.jar --komga.config-dir="$WORK/komga-conf" --server.port=18081 >komga.log 2>&1 & KP=$!
  until curl -fs -o /dev/null http://127.0.0.1:18081/actuator/health; do sleep 0.5; done
  curl -s -X POST http://127.0.0.1:18081/api/v1/users -H 'Content-Type: application/json' -d '{"email":"a@b.c","password":"benchpass1"}' -o /dev/null || true
  curl -s -u a@b.c:benchpass1 -X POST http://127.0.0.1:18081/api/v1/libraries -H 'Content-Type: application/json' \
    -d "{\"name\":\"bench\",\"root\":\"$WORK/inputs/library\"}" -o /dev/null
  s=$(now)
  while :; do c=$(curl -s -u a@b.c:benchpass1 "http://127.0.0.1:18081/api/v1/books?size=1" | python3 -c "import sys,json;print(json.load(sys.stdin).get('totalElements',0))" 2>/dev/null || echo 0); [ "$c" -ge "$N" ] && break; sleep 2; done
  emit "{\"tool\":\"komga\",\"step\":\"scan $N PDFs to the last book listed\",\"seconds\":$(dur "$s"),\"rss_mb\":$(rss $KP)}"
  t=$(curl -s -u a@b.c:benchpass1 -o /dev/null -w '%{time_total} %{size_download}' "http://127.0.0.1:18081/api/v1/books?search=river&size=50")
  emit "{\"tool\":\"komga\",\"step\":\"search 'river' (50 rows)\",\"seconds\":\"${t% *}\",\"response_bytes\":${t#* }}"
  kill $KP 2>/dev/null || true
else
  emit "{\"tool\":\"komga\",\"skipped\":\"java not installed\"}"
fi
