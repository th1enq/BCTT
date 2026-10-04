# Final research benchmark report

Generated from the final CSV; historical/exploratory CSVs are excluded.

Correctness: 741,280 solver/oracle comparisons, zero mismatches; 495 Atlas graphs.
Measurements: 190 cells, 3308 raw records; statuses {'ok': 3290, 'timeout': 15, 'skipped_budget': 3}.
Seven subprocess batches per completed cell; median/IQR, pinning, child CPU time, exact counts and hashes.

The paper comparison is the literal forest recurrence after equal rank compression, not author code.
Transfer matrices and the unoptimized treewidth DP are internal baselines.

| Family | Paired cells | Geometric mean speedup | Min | Max |
|---|---:|---:|---:|---:|
| forest_dense | 47 | 16.1x | 1.92x | 185x |
| ttsp_dense | 45 | 5.24x | 1.08x | 52x |
| partial2 | 24 | 3.8x | 1.32x | 17.6x |
| cactus | 8 | 78.9x | 43x | 145x |

No censored cell enters a speedup average. Geometric means summarize this grid, not all graphs.

TTSP k=256,r=32: matrix 365 ms vs events 7.53 ms (48.4x); maximum process RSS 92.6 vs 8.01 MiB.

## Censored solver/cells

| Family | Instance | Solver | Status |
|---|---|---|---|
| forest_dense | L500-r1000 | forest-paper | timeout |
| forest_dense | L1000-r1000 | forest-paper | timeout |
| forest_sparse | L1000-r1000-d1000 | forest-paper | timeout |
| forest_density_control | L1000-r1000-d1000 | forest-paper | timeout |
| ttsp_extra | k64-r128-strict0 | ttsp-transfer | timeout |
| ttsp_sparse | k64-r1000-d4 | ttsp-transfer | skipped_budget |
| ttsp_sparse | k256-r10000-d4 | ttsp-transfer | skipped_budget |
| ttsp_sparse | k1024-r10000-d4 | ttsp-transfer | skipped_budget |
| width | w4-n12-r8 | tw-dp-baseline | timeout |
| ladder | c24-r2 | brute | timeout |
| ladder | c24-r4 | brute | timeout |
| ladder | c24-r8 | brute | timeout |
| ladder | c32-r2 | brute | timeout |
| ladder | c32-r4 | brute | timeout |
| ladder | c32-r8 | brute | timeout |
| ladder | c64-r2 | brute | timeout |
| ladder | c64-r4 | brute | timeout |
| ladder | c64-r8 | brute | timeout |

Remaining limits: no full n=5,r=2 exhaustive campaign, no independent proof referee, no real-world temporal dataset in this campaign.
CPU frequency is not locked. RSS includes input parsing and allocator retention. Strict timings cover a subset, correctness audits cover both modes.
