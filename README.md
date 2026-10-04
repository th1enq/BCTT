# Counting Temporal Paths — reproducible C++ implementation

This repository implements the research program in
[`TEMPORAL_PATH_RESEARCH_MASTER_HANDOFF.md`](TEMPORAL_PATH_RESEARCH_MASTER_HANDOFF.md): exact counting of simple temporal paths, in both non-strict and strict time, with arbitrary-precision counts. The October 2026 research upgrade includes proofs, independent correctness campaigns, controlled repeated benchmarks, and a Vietnamese thesis.

Implemented solvers:

- `forest-paper`: literal \(O(|P|r^2)\) recurrence corresponding to Theorem 2 of Enright–Meeks–Molter;
- `forest-dense`: prefix-sum \(O(|P|r)\) algorithm;
- `forest-sparse`: \(O(|P|+\sum_{e\in P}|L(e)|)\) after sorted rank compression;
- `ttsp-transfer`: internal transfer-matrix baseline, \(O(mr^3)\), for a supplied two-terminal SP expression;
- `ttsp-events`: \(O(n+m+M+r)\) event-counting core on a valid pole-oriented TTSP DAG;
- `cactus`: block-cut route plus event counting for arbitrary terminal pairs;
- `tw-dp`: connectivity DP with compact terminal states, indexed joins and child-table release, for a supplied normalized nice tree decomposition;
- `tw-dp-baseline`: the unoptimized internal DP baseline;
- `brute`: simple static-path enumeration followed by a label DP (shares a helper with the sparse forest solver);
- `brute-cartesian`: independent direct temporal-edge DFS.

Here \(M\) is the number of temporal edges and \(r\) is the number of distinct compressed timestamps. Arithmetic-operation bounds exclude parsing/rank compression and count bit costs; see the manuscript for full conditions. TG parsing is currently \(O(M\log M)\), and TTSP structural validation is additional.

The code uses a self-contained non-negative arbitrary-precision integer with 32-bit limbs, so Boost is not required. Timestamps are rank-compressed during parsing and duplicate `(u,v,t)` rows are deduplicated.

## Build and test

Requirements: a C++20 compiler and Python 3.10 or later.

```bash
bash scripts/build.sh
```

On systems with a CMake backend (`ninja` or `make`):

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DTPCOUNT_NATIVE=ON
cmake --build build -j
ctest --test-dir build --output-on-failure
```

## CLI

```bash
build/tpcount info tests/data/triangle.tg
build/tpcount count --solver forest-sparse INSTANCE.tg
build/tpcount count --solver ttsp-transfer INSTANCE.tg --decomp INSTANCE.sp
build/tpcount count --solver ttsp-events INSTANCE.tg --decomp INSTANCE.sp
build/tpcount count --solver cactus INSTANCE.tg
build/tpcount count --solver tw-dp INSTANCE.tg --td INSTANCE.ntd
build/tpcount verify --solver tw-dp INSTANCE.tg --td INSTANCE.ntd --reference cartesian
build/tpcount count --solver tw-dp INSTANCE.tg --td INSTANCE.ntd --strict --repeat 20
python3 python/decompose.py INSTANCE.tg INSTANCE.ntd
```

Count commands emit JSON containing the exact decimal count, bit length, per-solve wall/CPU time, separate parse time, post-exec peak RSS, instance dimensions, and solver-specific counters. The automatic decomposition script recognizes width at most two; it is not a general treewidth optimizer.

## Reproduce the research upgrade

Run the complete release workflow (including manuscript and vector figures):

```bash
bash scripts/research_pipeline.sh
```

Or run the stages separately:

```bash
bash scripts/build.sh
python3 python/research_audit.py
python3 python/research_benchmark.py
python3 python/ladder_benchmark.py
python3 python/research_aggregate.py
bash thesis/build_pdf.sh
python3 python/research_validate.py
```

The final campaign has 190 benchmark instances: 169 main cells and 21 separately specified ladder cells. Each successful solver cell has one warm-up and seven randomized-order measured batches, CPU affinity, median/IQR reporting, exact-count checks, and explicit timeout/budget records. The 741,280 correctness comparisons have zero mismatches: exhaustive \(n\le4,r=2\) and \(n=5,r=1\), independent Python DFS, randomized width 1–4 graphs, metamorphic tests, and all 495 width-at-most-two Graph Atlas graphs with at least two vertices. These are comparison counts, not counts of distinct graphs. Full exhaustive \(n=5,r=2\) remains future work.

Primary artifacts:

- [`results/temporal_path_thesis.pdf`](results/temporal_path_thesis.pdf): thesis;
- [`results/RESEARCH_BENCHMARK_REPORT.md`](results/RESEARCH_BENCHMARK_REPORT.md): generated benchmark report;
- [`results/research_benchmark.csv`](results/research_benchmark.csv) and [`results/research_ladder.csv`](results/research_ladder.csv): raw measurements;
- [`results/research_benchmark_summary.csv`](results/research_benchmark_summary.csv): medians, quartiles and telemetry;
- [`docs/research_protocol_2026-10-04.md`](docs/research_protocol_2026-10-04.md) and [`docs/ladder_protocol.md`](docs/ladder_protocol.md): protocols;
- [`docs/research_contributions.md`](docs/research_contributions.md): complexity/comparison scope;
- [`docs/novelty_review.md`](docs/novelty_review.md): dated primary-source review and priority limitations.

The CSV controller records source/binary/input/decomposition hashes and deterministic seeds. Censored cells remain in the report and are not averaged into speedup claims. RSS measurements made before the Linux post-exec fix are archived and excluded from final aggregation.
The final integrity check verifies counts/hashes, seven unique samples, summary statistics, unchanged inputs/controllers/binary, audit digests, and up-to-date figures/PDF; it writes `results/research_release_validation.json`.

## Historical handoff campaigns

Fast commit-level campaign:

```bash
python3 python/benchmark.py --suite smoke
```

Full seeded correctness targets from the handoff:

```bash
python3 python/audit.py
```

Full diamond grid (all \(k\in\{1,2,4,8,16,32,64,128,256\}\), \(r\in\{2,4,8,16,32\}\)):

```bash
python3 python/benchmark.py --suite ttsp --thesis
```

The forest thesis grid is intentionally separate because literal paper-baseline cells can time out:

```bash
python3 python/benchmark.py --suite forest --thesis
```

Generated instances go to `benchmarks/generated/`; result tables go to `results/`. The master seed is `20260928`, and each random seed is derived with SHA-256 exactly as specified in the handoff.

## Scientific scope

No official runtime artifact or benchmark dataset was identified in the inspected Algorithmica paper and associated sources. This repository provides a paper-faithful reproducible benchmark suite, not “official paper instances.” `forest-paper` is our reimplementation of the paper recurrence. Matrix/treewidth comparisons are internal baselines, not measurements against authors' code.

`tw-dp` is XP in underlying treewidth, not FPT in treewidth alone. Compact terminal states give the explicit arithmetic bound \(N(r+1)^{2w+2}2^{O(w\log w)}\), hence \(O(N(r+1)^6)\) at width two. Both `<=` and strict `<` semantics are implemented and audited. Theorems are fully written internal results; independent proof review and worldwide novelty verification are still needed. See [`docs/proof.md`](docs/proof.md).

## Thesis manuscript

The complete Vietnamese LaTeX manuscript is in `thesis/`. Build it with:

```bash
bash thesis/build_pdf.sh
```

The compiled PDF is written to `results/temporal_path_thesis.pdf`. Figure/PDF builds require Tectonic and installed DejaVu/FreeMono fonts, or Nix with the cached Tectonic package. Before submission, replace the personal/university placeholders in `thesis/main.tex`, complete an independent proof/novelty review, and follow university rules on attribution and AI assistance. No grade or publication acceptance is inferred from benchmarks.
