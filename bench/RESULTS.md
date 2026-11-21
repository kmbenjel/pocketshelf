# Benchmark results

Run on Google Cloud VMs of one type (c2d-highcpu, AMD EPYC 7B13, Ubuntu 24.04, spot) with `bench/browser_bench.sh`, `bench/scale.sh` and `bench/compare.sh`:
the pocketshelf figures on 2026-11-21 with 16 vCPUs, the Calibre and Komga figures on 2026-11-13 with 32 vCPUs.
Chrome 157.0.8103.78 headless (`--headless=new`), Node 22.11, Java 21 (OpenJDK) for Komga. Raw lines below.

"4x" is `Emulation.setCPUThrottlingRate(4)`: it slows the page's main thread four times, which resembles a mid-range phone but is **not** a real phone.
On an older laptop CPU the same 4x run took 0.73 s (synthetic) and 0.78 s (real titles) to be ready.

## pocketshelf, 20,000 books

Real titles: the first 20,000 texts of the Project Gutenberg catalog (`bench/pg_catalog_to_csv.py`). Synthetic: `pocketshelf bench -n 20000`.

| Input | HTML size | Build | CPU | Page ready | Decode | Model | First query "a" (17k hits, finishes the index) | "river" | "gar" | Arabic "الكتاب" | miss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Real titles | 1.02 MB | 1.2 s | 1x | 75 ms | 37 ms | 10 ms | 53 ms | 3.4 ms | 2.4 ms | 1.0 ms | 0.7 ms |
| Real titles | | | 4x | 283 ms | 145 ms | 30 ms | 196 ms | 13.6 ms | 9.5 ms | 5.6 ms | 4.1 ms |
| Synthetic | 0.87 MB | 0.6 s | 1x | 68 ms | 32 ms | 10 ms | 32 ms | 4.4 ms | 3.1 ms | 2.9 ms | 1.1 ms |
| Synthetic | | | 4x | 270 ms | 131 ms | 38 ms | 126 ms | 21.5 ms | 14.8 ms | 15.7 ms | 6.6 ms |

"Page ready" is the time from navigation to the first rendered list (`performance.now()` at the end of start-up); "decode" is base64, gunzip and `JSON.parse`; "model" is grouping 20,000 books into works.
The search index is built after the first paint in slices of 8 ms, so the page stays responsive while it grows; a query that arrives before it is complete finishes it first, which is what the first-query column measures.
Building from a *folder* of 20,000 one-page PDFs (reading each file's Info dictionary, 8 threads): 4.5 s, 0.71 MB. `pocketshelf demo` (3,018 books): 0.21 s, 0.23 MB.

## pocketshelf, 5,000 to 100,000 books (`bench/scale.sh`)

Synthetic catalogs of `pocketshelf bench -n N`, and every text of the Project Gutenberg catalog (78,518 rows). Median of 7 runs; the files are visited in turn on every run.

| Books | HTML file | Build | Ready, 1x | Ready, 4x | Decode, 4x | Longest block after the first paint, 4x | Search "river", 4x | Broad query "a", 4x | Sort by author, 4x | Statistics view, 4x | JS heap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 synthetic | 0.28 MB | 0.14 s | 39 ms | 142 ms | 51 ms | under 50 ms | 8 ms | 9 ms | 10 ms | 14 ms | 5 MB |
| 10,000 synthetic | 0.48 MB | 0.28 s | 54 ms | 200 ms | 81 ms | under 50 ms | 11 ms | 17 ms | 17 ms | 18 ms | 8 MB |
| 20,000 synthetic | 0.87 MB | 0.59 s | 85 ms | 317 ms | 144 ms | under 50 ms | 17 ms | 31 ms | 29 ms | 25 ms | 15 MB |
| 50,000 synthetic | 2.03 MB | 1.5 s | 169 ms | 629 ms | 324 ms | under 50 ms | 33 ms | 48 ms | 63 ms | 44 ms | 35 MB |
| 78,518 real titles | 4.02 MB | 4.7 s | 285 ms | 1,094 ms | 688 ms | 52 ms | 47 ms | 168 ms | 219 ms | 84 ms | 63 MB |
| 100,000 synthetic | 3.93 MB | 3.2 s | 302 ms | 1,154 ms | 745 ms | under 50 ms | 49 ms | 82 ms | 130 ms | 82 ms | 69 MB |

"Longest block" is the longest single task Chrome reports (`longtask`, from 50 ms up) between the first paint and the end of the background indexing: the longest time a tap or a keystroke could have waited.
The broad query "a" matches most of each catalog (17,434 of the 20,000 synthetic books); its time is matching, ranking and drawing the list.
The 20,000-book line is a little slower here than in the table above (317 ms against 270 ms at 4x): this harness visits six files in turn and records long tasks, the other reloads one file nine times.
Start-up is dominated by unpacking the data (gunzip and `JSON.parse`), which grows in a straight line with the catalog.

## Head to head, 20,000 synthetic books (metadata and one-page PDFs, `bench/compare.sh`)

| Step | Calibre 9.18.0 | Komga 1.30.1 | pocketshelf |
|---|---|---|---|
| Download / install | 229 MB download, 910 MB installed | 121 MB jar (+ a Java runtime) | 179 KB wheel, no dependencies |
| Make the library searchable | 581 s to create 20,000 records through the Python API (metadata only, no files) | 44.8 s from start to all 20,000 PDFs listed | 1.2 s from CSV, 4.5 s from a folder of PDFs |
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
{"tool":"pocketshelf","step":"build from 20000 PDFs","seconds":4.49,"output_bytes":714946}
{"tool":"pocketshelf","step":"build from CSV","seconds":1.2,"output_bytes":770490}
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
{"build":"pg20k","seconds":1.2,"bytes":1019220}
{"books": 20000, "html_bytes": 871795, "html_gzip_bytes": 630647, "generate_s": 0.23, "build_s": 0.58, "file": "synth20k.html"}
{"chrome":"Google Chrome 157.0.8103.78 ","cpus":16}
{"file":"./pg20k.html","cpuSlowdown":1,"runs":9,"pageReadyMs":75,"decodeMs":37,"modelMs":10,"searchMs":{"a":{"ms":53.2,"results":17468},"river":{"ms":3.4,"results":51},"gar":{"ms":2.4,"results":438},"الكتاب":{"ms":1,"results":0},"jardin hiv":{"ms":0.9,"results":0},"zzzz":{"ms":0.7,"results":0}}}
{"file":"./pg20k.html","cpuSlowdown":4,"runs":9,"pageReadyMs":283,"decodeMs":145,"modelMs":30,"searchMs":{"a":{"ms":195.7,"results":17468},"river":{"ms":13.6,"results":51},"gar":{"ms":9.5,"results":438},"الكتاب":{"ms":5.6,"results":0},"jardin hiv":{"ms":5.2,"results":0},"zzzz":{"ms":4.1,"results":0}}}
{"file":"./synth20k.html","cpuSlowdown":1,"runs":9,"pageReadyMs":68,"decodeMs":32,"modelMs":10,"searchMs":{"a":{"ms":32,"results":17434},"river":{"ms":4.4,"results":2035},"gar":{"ms":3.1,"results":2101},"الكتاب":{"ms":2.9,"results":788},"jardin hiv":{"ms":2,"results":180},"zzzz":{"ms":1.1,"results":0}}}
{"file":"./synth20k.html","cpuSlowdown":4,"runs":9,"pageReadyMs":270,"decodeMs":131,"modelMs":38,"searchMs":{"a":{"ms":125.9,"results":17434},"river":{"ms":21.5,"results":2035},"gar":{"ms":14.8,"results":2101},"الكتاب":{"ms":15.7,"results":788},"jardin hiv":{"ms":13,"results":180},"zzzz":{"ms":6.6,"results":0}}}
--- bench/scale.sh (also kept as bench/scale-results.jsonl) ---
{"books": 5000, "html_bytes": 280798, "html_gzip_bytes": 183301, "generate_s": 0.05, "build_s": 0.14, "file": "synth-5000.html"}
{"books": 10000, "html_bytes": 481011, "html_gzip_bytes": 334688, "generate_s": 0.11, "build_s": 0.28, "file": "synth-10000.html"}
{"books": 20000, "html_bytes": 871795, "html_gzip_bytes": 630647, "generate_s": 0.23, "build_s": 0.59, "file": "synth-20000.html"}
{"books": 50000, "html_bytes": 2026155, "html_gzip_bytes": 1504712, "generate_s": 0.59, "build_s": 1.5, "file": "synth-50000.html"}
{"books": 100000, "html_bytes": 3925520, "html_gzip_bytes": 2943135, "generate_s": 1.22, "build_s": 3.18, "file": "synth-100000.html"}
{"build":"pg-all","seconds":4.65,"html_bytes":4016793}
{"chrome":"Google Chrome 157.0.8103.78 ","cpus":16,"load_1min":3.77}
{"file":"synth-5000.html","books":5000,"cpuSlowdown":1,"runs":7,"readyMs":38.7,"decodeMs":14.1,"modelMs":6.5,"blockedMs":0,"missMs":0.5,"wordMs":1.9,"arabicMs":1.8,"broadMs":2.5,"sortAuthorMs":2.5,"authorsMs":2.3,"catsMs":1.6,"statsMs":3.2,"heapMB":4.8}
{"file":"synth-10000.html","books":10000,"cpuSlowdown":1,"runs":7,"readyMs":53.9,"decodeMs":22.6,"modelMs":9.6,"blockedMs":0,"missMs":0.7,"wordMs":3.6,"arabicMs":2.9,"broadMs":4,"sortAuthorMs":4,"authorsMs":3.1,"catsMs":1.8,"statsMs":5.1,"heapMB":8.1}
{"file":"synth-20000.html","books":20000,"cpuSlowdown":1,"runs":7,"readyMs":84.8,"decodeMs":37.5,"modelMs":16.3,"blockedMs":0,"missMs":1.9,"wordMs":4.3,"arabicMs":3.7,"broadMs":9.9,"sortAuthorMs":8.1,"authorsMs":3.8,"catsMs":1.9,"statsMs":6.4,"heapMB":14.9}
{"file":"synth-50000.html","books":50000,"cpuSlowdown":1,"runs":7,"readyMs":168.7,"decodeMs":82.8,"modelMs":41.4,"blockedMs":0,"missMs":2.5,"wordMs":7.9,"arabicMs":6.5,"broadMs":17.1,"sortAuthorMs":15.3,"authorsMs":4.8,"catsMs":2.9,"statsMs":11.1,"heapMB":35}
{"file":"synth-100000.html","books":100000,"cpuSlowdown":1,"runs":7,"readyMs":302.5,"decodeMs":187.2,"modelMs":60.1,"blockedMs":0,"missMs":3.3,"wordMs":12,"arabicMs":10.6,"broadMs":24.4,"sortAuthorMs":32.1,"authorsMs":7.1,"catsMs":5.3,"statsMs":26.1,"heapMB":69}
{"file":"pg-all.html","books":78518,"cpuSlowdown":1,"runs":7,"readyMs":285.4,"decodeMs":174.1,"modelMs":54.1,"blockedMs":0,"missMs":4.3,"wordMs":10,"arabicMs":3.6,"broadMs":37.3,"sortAuthorMs":53.6,"authorsMs":30.2,"catsMs":4.3,"statsMs":22.9,"heapMB":63.9}
{"file":"synth-5000.html","books":5000,"cpuSlowdown":4,"runs":7,"readyMs":142.2,"decodeMs":50.7,"modelMs":24,"blockedMs":0,"missMs":1.9,"wordMs":7.5,"arabicMs":6.1,"broadMs":9.4,"sortAuthorMs":9.9,"authorsMs":9.3,"catsMs":5.9,"statsMs":14.1,"heapMB":4.9}
{"file":"synth-10000.html","books":10000,"cpuSlowdown":4,"runs":7,"readyMs":200.3,"decodeMs":81,"modelMs":34,"blockedMs":0,"missMs":4.7,"wordMs":10.9,"arabicMs":8.9,"broadMs":17.2,"sortAuthorMs":17.2,"authorsMs":11.9,"catsMs":6.6,"statsMs":18.4,"heapMB":8.4}
{"file":"synth-20000.html","books":20000,"cpuSlowdown":4,"runs":7,"readyMs":316.7,"decodeMs":143.5,"modelMs":56.6,"blockedMs":0,"missMs":6.5,"wordMs":17.1,"arabicMs":13.1,"broadMs":30.7,"sortAuthorMs":29.2,"authorsMs":13.9,"catsMs":8.5,"statsMs":24.8,"heapMB":14.9}
{"file":"synth-50000.html","books":50000,"cpuSlowdown":4,"runs":7,"readyMs":628.7,"decodeMs":324.1,"modelMs":145.9,"blockedMs":0,"missMs":12.4,"wordMs":33.4,"arabicMs":25.8,"broadMs":47.7,"sortAuthorMs":62.6,"authorsMs":19.9,"catsMs":12.7,"statsMs":44.3,"heapMB":35}
{"file":"synth-100000.html","books":100000,"cpuSlowdown":4,"runs":7,"readyMs":1154.5,"decodeMs":744.7,"modelMs":192.3,"blockedMs":0,"missMs":13.9,"wordMs":49,"arabicMs":47.5,"broadMs":81.5,"sortAuthorMs":130.3,"authorsMs":31.2,"catsMs":17.2,"statsMs":82.1,"heapMB":69}
{"file":"pg-all.html","books":78518,"cpuSlowdown":4,"runs":7,"readyMs":1093.5,"decodeMs":687.5,"modelMs":180.6,"blockedMs":52,"missMs":23.4,"wordMs":47.2,"arabicMs":20.7,"broadMs":168.1,"sortAuthorMs":218.8,"authorsMs":139.8,"catsMs":19.1,"statsMs":83.7,"heapMB":63.2}
```
