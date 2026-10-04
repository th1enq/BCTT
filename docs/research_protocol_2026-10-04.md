# Research upgrade protocol (fixed before the repeated measurements)

This campaign evaluates exact counting, not approximate counting. The baseline
`forest-paper` is our literal implementation of the published forest recurrence
after identical rank compression; it is not author-provided code. `ttsp-transfer`
and `tw-dp-baseline` are earlier algorithms in this project, not algorithms from
Enright–Meeks–Molter. No timing comparison against an unimplemented MSO algorithm
is claimed.

## Hypotheses and primary outcomes

1. Dense forest prefixes reduce quadratic dependence on ranks to linear.
2. Sparse forest processing scales with actual label incidences on the path.
3. For TTSP pole queries, the event DAG algorithm uses O(M) additions, versus
   cubic-rank matrix composition. Its structural-validation cost is measured.
4. Erasing terminal timestamps reduces the treewidth state-bound rank exponent
   by two. Join indexing and releasing child tables improve practical costs.
5. The same algorithms support strict comparisons when equal-time events are
   ordered correctly and all internal local comparisons are strict.

Primary measurements: median solver wall and CPU time, IQR, peak process RSS,
states created and peak live states, attempted/possible join pairs, exact answer
hash and bit length. Solver wall time excludes reading/rank-compressing the TG
file and constructing the decomposition; it includes reading and validating the
supplied decomposition. Parse time and whole subprocess time are recorded
separately. RSS includes parsing and allocator retention and is not live DP
memory. Source/binary hashes, compiler, machine, seed and CPU affinity are saved.

Linux RSS uses `/proc/self/status` VmHWM in the C++ address space after exec.
During review, inherited fork-time `ru_maxrss` from Python was found to inflate
small C++ memory measurements. The complete main and ladder campaigns are
rerun after that measurement-only fix. Pre-fix CSVs are archived separately and
excluded from all final memory summaries. Solver algorithms and counts did not
change at this step.

## Measurement design

Every completed solver/cell has one calibration/warm-up and seven recorded
independent subprocess batches, in deterministically shuffled order. Very short
calls are batched inside C++ to target 10 ms, capped at 256 iterations. Every
iteration constructs a fresh solver state and must return the same answer.
Reported per-call time is batch elapsed time divided by iteration count.
Confidence intervals are not inferred from a single historical smoke run.

The runner is pinned to the first permitted CPU when supported. CPU frequency is
not fixed. Audits and benchmark measurements are run sequentially. A child has
a 1.5 GiB virtual-address-space limit. Default solver timeout is 3 seconds per
subprocess; larger matrix cases with r>128 are explicitly skipped by policy.
Timeout/error/policy skips stay in raw and summary CSVs, with empty measurements,
and are never averaged as successful timings.

## Planned families

- Dense paths: the 7x7 length/rank grid {10,20,50,100,200,500,1000}.
- Sparse paths: fixed cardinalities with a planted shared timestamp, including
  large nominal time domains; actual compressed r is reported.
- All-times diamonds: k in {1,2,4,8,16,32,64,128,256},
  r in {2,4,8,16,32}; independent closed-form oracle for every cell.
- Additional dense/strict diamonds and sparse large-rank diamonds.
- Partial 2-trees: varying n and r, arbitrary endpoints and fixed seeds.
- Width sensitivity: widths 1..4, n=12, r in {2,4,8}; report timeouts.
- Ablation: identical width-2 instances with individual terminal compaction,
  terminal pruning, join indexing, or table release disabled.
- Cactus: arbitrary endpoints, scaling, and comparison with treewidth DP.

## Correctness gates

Run core tests, exhaustive time-edge configurations for all n<=4,r=2 and n=5,r=1,
all ordered queries and both time semantics, selected Graph Atlas width<=2
graphs with three label configurations, random forests/TTSP/width1..4/cactus,
and order-preserving timestamp/vertex renamings. Python oracle enumerates actual
time-edge sequences and uses Python integers; it shares no solver recurrence.
Any mismatch stops the campaign and records the failing input.

The full n=5,r=2 Cartesian campaign remains outside this bounded campaign and
must not be described as completed. A successful audit is implementation
evidence, not independent proof review or an assertion of worldwide novelty.

## Follow-up density control

After the original 160-cell run, a fixed-rank density control was added because
the planted single timestamp in the d=1 sparse path compresses to r=1. Five new
cells keep length=1000 and compressed r=1000, and vary path-label cardinality
d in {1,4,16,100,1000}. A pendant edge outside the s-z path carries all ranks.
The original raw measurements are retained; the new measurements are stored in
`research_density_control.csv`. This control isolates path-label density from
the number of distinct global ranks and is reported as a follow-up experiment.

The final repeat of the complete campaign includes these controls (165 cells)
and four enumeration-crossover cells (169 cells total). Every width-sensitivity
cell also measures independent static-path enumeration. `no-prune` disables
terminal compaction as well because compaction requires terminal pruning; the
isolated pruning effect compares `no-prune` against `no-compact`. The first
160-cell raw run is retained as `research_benchmark_initial.csv`, is exploratory,
and is excluded from the final aggregate. The final controller and generator
hashes are recorded alongside the unchanged C++ source and binary hashes.
