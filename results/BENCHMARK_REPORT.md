# Benchmark report — 2026-09-28

Historical single-run report. The upgraded thesis uses
[`RESEARCH_BENCHMARK_REPORT.md`](RESEARCH_BENCHMARK_REPORT.md), generated from
the October 2026 repeated campaign. Atlas, strict-path audits, optimized DP and
post-exec RSS measurements are documented there; pending gates below describe
the earlier snapshot only.

Environment: Intel Core i9-9980HK (8 physical cores/16 threads), 15 GiB RAM, Linux 6.12.93 x86-64, GCC 14.3.0, Python 3.13.12. C++ flags were `-std=c++20 -O3 -DNDEBUG`. Solver runs were single-process and decomposition generation was outside the timed region.

## Correctness gate

The default deterministic audit completed with zero mismatches:

| Family | Independent comparisons | Mismatches |
|---|---:|---:|
| Random forests | 3,000 | 0 |
| Recursive random TTSP | 2,500 | 0 |
| Random partial 2-trees, arbitrary queries | 1,000 | 0 |
| **Total** | **6,500** | **0** |

An additional 1,000 partial-2-tree comparisons are retained in `correctness-thesis.csv`. Manual tests cover single edges, temporal rejection, equal timestamps, path closed forms, the diamond closed form, triangle counting, and a real join node.

## Forest smoke scaling

These are single-run engineering smoke measurements, not publication-level repeated statistics.

| Path edges | Ranks | Paper ms | Dense-prefix ms | Sparse ms | Paper/dense | Paper/sparse |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 0.00648 | 0.00464 | 0.00692 | 1.40x | 0.94x |
| 40 | 20 | 0.0373 | 0.0136 | 0.0303 | 2.74x | 1.23x |
| 100 | 50 | 0.521 | 0.0924 | 0.305 | 5.64x | 1.71x |
| 250 | 100 | 6.36 | 0.452 | 1.49 | 14.08x | 4.27x |

The increasing speedup is consistent with the expected quadratic-vs-linear rank dependence. On fully dense labels, dense-prefix is expected to outperform the sparse representation because its memory access is simpler; sparse labels are the intended setting for `forest-sparse`.

## Mandatory all-times diamond grid

All 45 transfer cases (`k=1..256` powers of two, `r=2,4,8,16,32`) completed successfully. Tiny cases also agreed with independent brute force. The largest case, `k=256,r=32`, used 1,024 static edges and 32,768 temporal edges, returned a 424-bit answer, and ran in 255.5 ms with reported peak RSS 87.4 MiB. The full table is `ttsp-thesis.csv`.

## Scope not yet claimed

The Graph Atlas and exhaustive temporal-label campaign up to `n=5,r=2` have not been run in this repository. The current results therefore support implementation correctness strongly but do not replace those remaining release gates. The forest timings need repeated runs, CPU affinity, and median/IQR reporting before direct inclusion as final thesis figures.
