#!/usr/bin/env bash
# Build the two 20,000-book catalogs and time them in headless Chrome at 1x and 4x CPU throttling.
# Needs: pocketshelf importable (pip install -e .), node >= 22, Chrome/Chromium.   bash bench/browser_bench.sh [WORKDIR]
set -euo pipefail
WORK="${1:-$HOME/ps-browser}"; HERE="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$WORK"; cd "$WORK"
export PS_DIRECT_CHROME=1
[ -f pg_catalog.csv ] || curl -fsSL -o pg_catalog.csv https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv
python3 "$HERE/bench/pg_catalog_to_csv.py" pg_catalog.csv 20000 pg20k.csv
s=$(date +%s.%N); pocketshelf build pg20k.csv -o pg20k.html 2>/dev/null; echo "{\"build\":\"pg20k\",\"seconds\":$(python3 -c "print(round($(date +%s.%N)-$s,2))"),\"bytes\":$(stat -c %s pg20k.html)}"
pocketshelf bench -n 20000 -o synth20k.html
echo "{\"chrome\":\"$( (google-chrome --version || chromium --version) 2>/dev/null)\",\"cpus\":$(nproc)}"
for f in pg20k synth20k; do for slow in 1 4; do node "$HERE/bench/load_time.mjs" "$WORK/$f.html" "$slow" 9; done; done
