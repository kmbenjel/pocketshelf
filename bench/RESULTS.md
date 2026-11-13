# Benchmark results

Run on 2026-11-13 on a Google Cloud VM (c2d-highcpu-32, Ubuntu 24.04, 32 vCPU, spot) with `bench/browser_bench.sh` and `bench/compare.sh`.
Chrome 157.0.8103.78 headless (`--headless=new`), Node 22.11, Java 21 (OpenJDK) for Komga. Raw lines below.

"4x" is `Emulation.setCPUThrottlingRate(4)`: it slows the page's main thread four times, which resembles a mid-range phone but is **not** a real phone.
On an older laptop CPU the same 4x run took 0.73 s (synthetic) and 0.78 s (real titles) to be ready.

## pocketshelf, 20,000 books

Real titles: the first 20,000 texts of the Project Gutenberg catalog (`bench/pg_catalog_to_csv.py`). Synthetic: `pocketshelf bench -n 20000`.

| Input | HTML size | Build | CPU | Page ready | Decode | Model | First query "a" (17k hits, builds the index) | "river" | "gar" | Arabic "الكتاب" | miss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Real titles | 1.01 MB | 1.8 s | 1x | 77 ms | 34 ms | 10 ms | 88 ms | 4.5 ms | 3.0 ms | 1.2 ms | 1.1 ms |
| Real titles | | | 4x | 299 ms | 135 ms | 28 ms | 356 ms | 21 ms | 17 ms | 7.7 ms | 9.5 ms |
| Synthetic | 0.86 MB | 1.1 s | 1x | 76 ms | 31 ms | 10 ms | 61 ms | 5.4 ms | 4.4 ms | 3.5 ms | 1.2 ms |
| Synthetic | | | 4x | 288 ms | 126 ms | 29 ms | 237 ms | 28 ms | 19 ms | 16 ms | 7.5 ms |

"Page ready" is the time from navigation to the first rendered list (`performance.now()` at the end of start-up); "decode" is base64, gunzip and `JSON.parse`; "model" is grouping 20,000 books into works.
The search index is built right after the first paint (30 ms timer) or at the first query, whichever is first; the first query row includes it when the query comes before the timer.
Building from a *folder* of 20,000 one-page PDFs (reading each file's Info dictionary, 8 threads): 5.0 s, 0.70 MB.

## Head to head, 20,000 synthetic books (metadata and one-page PDFs, `bench/compare.sh`)

| Step | Calibre 9.18.0 | Komga 1.30.1 | pocketshelf |
|---|---|---|---|
| Download / install | 229 MB download, 910 MB installed | 121 MB jar (+ a Java runtime) | 167 KB wheel, no dependencies |
| Make the library searchable | 581 s to create 20,000 records through the Python API (metadata only, no files) | 44.8 s from start to all 20,000 PDFs listed | 1.6 s from CSV, 5.0 s from a folder of PDFs |
| Output you carry to a phone | needs `calibre-server` running: 0.81 s to the first page, 191 MB resident | needs the Komga server running: 1,036 MB resident | one 0.7 MB HTML file, no process |
| Server-side search "river", 50 rows | 0.14 s (ids only) | 0.21 s (54 KB JSON) | in the page: 1-30 ms |
| Static catalog export | `calibredb catalog` CSV: 2.4 s, 1.3 MB, 3 fields; no search UI | none | the HTML file |

Search probes, run on a 300-book library with three probe titles ("Les Misérables", "إحياء علوم الدين", "Œuvres complètes"):

| Query | Calibre content server | Komga | pocketshelf |
|---|---|---|---|
| `miserables` | 1 hit | 1 hit | 1 hit |
| `oeuvres` | 1 hit | 1 hit | 1 hit |
| `احياء علوم` (no hamza on alef, no hamza after ya) | **0 hits** | **0 hits** | 1 hit |

Not measured: Calibre-Web, Kavita and Ubooquity (they need an interactive first-run setup), Kiwix (it reads ZIM archives, not folders of PDFs).

## Raw output

Lines from `bench/compare.sh` (20,000 books, steps run as `STEPS=...` in turn; the CSV export line is the `calibredb catalog` command it
shows, timed on the same library) and from `bench/browser_bench.sh`.

```
{"tool":"pocketshelf","step":"build from 20000 PDFs","seconds":5.01,"output_bytes":700745}
{"tool":"pocketshelf","step":"build from CSV","seconds":1.63,"output_bytes":756333}
{"tool":"calibre","version":"9.18.0","installed_mb":910,"download_mb":229}
{"tool":"calibre","step":"import 20000 records","seconds":581.12}
{"tool":"calibre","step":"calibredb catalog (CSV), by hand: calibredb catalog out.csv --library-path LIB --fields title,authors,publisher","seconds":2.4,"output_bytes":1318831}
{"tool":"calibre","step":"content server start to first page","seconds":0.81,"rss_mb":191}
{"tool":"calibre","step":"content server search 'river' (50 rows)","seconds":"0.138371","response_bytes":547}
{"tool":"komga","jar_mb":121}
{"tool":"komga","step":"scan 20000 PDFs to the last book listed","seconds":44.79,"rss_mb":1036}
{"tool":"komga","step":"search 'river' (50 rows)","seconds":"0.214827","response_bytes":53894}
--- 300-book run with the three probe titles ---
{"tool":"calibre","step":"import 300 records","seconds":8.81}
{"tool":"calibre","probe":{"miserables":1,"احياء علوم":0,"oeuvres":1}}
{"tool":"komga","probe":{"miserables":1,"احياء علوم":0,"oeuvres":1}}
--- bench/browser_bench.sh ---
20000 rows -> pg20k.csv
{"build":"pg20k","seconds":1.79,"bytes":1006231}
{"books": 20000, "html_bytes": 858806, "html_gzip_bytes": 625315, "generate_s": 0.65, "build_s": 1.08, "file": "synth20k.html"}
{"chrome":"Google Chrome 157.0.8103.78 ","cpus":32}
{"file":"./pg20k.html","cpuSlowdown":1,"runs":9,"pageReadyMs":77,"decodeMs":34,"modelMs":10,"searchMs":{"a":{"ms":88.2,"results":17468},"river":{"ms":4.5,"results":51},"gar":{"ms":3,"results":438},"الكتاب":{"ms":1.2,"results":0},"jardin hiv":{"ms":1.2,"results":0},"zzzz":{"ms":1.1,"results":0}}}
{"file":"./pg20k.html","cpuSlowdown":4,"runs":9,"pageReadyMs":299,"decodeMs":135,"modelMs":28,"searchMs":{"a":{"ms":355.5,"results":17468},"river":{"ms":21.1,"results":51},"gar":{"ms":16.7,"results":438},"الكتاب":{"ms":7.7,"results":0},"jardin hiv":{"ms":8.4,"results":0},"zzzz":{"ms":9.5,"results":0}}}
{"file":"./synth20k.html","cpuSlowdown":1,"runs":9,"pageReadyMs":76,"decodeMs":31,"modelMs":10,"searchMs":{"a":{"ms":60.6,"results":17434},"river":{"ms":5.4,"results":2035},"gar":{"ms":4.4,"results":2101},"الكتاب":{"ms":3.5,"results":788},"jardin hiv":{"ms":2.5,"results":180},"zzzz":{"ms":1.2,"results":0}}}
{"file":"./synth20k.html","cpuSlowdown":4,"runs":9,"pageReadyMs":288,"decodeMs":126,"modelMs":29,"searchMs":{"a":{"ms":236.9,"results":17434},"river":{"ms":27.9,"results":2035},"gar":{"ms":18.8,"results":2101},"الكتاب":{"ms":15.6,"results":788},"jardin hiv":{"ms":10.5,"results":180},"zzzz":{"ms":7.5,"results":0}}}
```
