#!/usr/bin/env bash
# How the page scales from 5,000 to 100,000 books: build the catalogs, time them in headless Chrome at 1x and 4x
# CPU throttling, and draw docs/media/scale.svg from the results.
# Needs: pocketshelf importable (pip install -e .), node >= 22, Chrome/Chromium.   bash bench/scale.sh [WORKDIR] [RUNS]
set -euo pipefail
WORK="${1:-$HOME/ps-scale}"; RUNS="${2:-7}"; HERE="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$WORK"; cd "$WORK"
export PS_DIRECT_CHROME=1
OUT="$HERE/bench/scale-results.jsonl"; : > "$OUT"
FILES=()
for n in 5000 10000 20000 50000 100000; do
  pocketshelf bench -n "$n" -o "synth-$n.html" | tee -a "$OUT"; FILES+=("$WORK/synth-$n.html")
done
# every text of the Project Gutenberg catalog: real titles and authors, about 78,000 rows
[ -f pg_catalog.csv ] || curl -fsSL -o pg_catalog.csv https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv
python3 "$HERE/bench/pg_catalog_to_csv.py" pg_catalog.csv 1000000 pg-all.csv
s=$(date +%s.%N); pocketshelf build pg-all.csv -o pg-all.html 2>/dev/null
echo "{\"build\":\"pg-all\",\"seconds\":$(python3 -c "print(round($(date +%s.%N)-$s,2))"),\"html_bytes\":$(stat -c %s pg-all.html)}" | tee -a "$OUT"
FILES+=("$WORK/pg-all.html")
echo "{\"chrome\":\"$( (google-chrome --version || chromium --version) 2>/dev/null)\",\"cpus\":$(nproc),\"load_1min\":$(cut -d' ' -f1 /proc/loadavg)}" | tee -a "$OUT"
for slow in 1 4; do node "$HERE/bench/scale.mjs" "$slow" "$RUNS" "${FILES[@]}" | tee -a "$OUT"; done
python3 "$HERE/bench/chart.py" "$OUT" "$HERE/docs/media/scale.svg"
