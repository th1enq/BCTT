# Experiment protocol

**Historical handoff protocol.** This file describes the earlier 6,500-instance
campaign, not the October 2026 final measurements. The current protocol is
[`research_protocol_2026-10-04.md`](research_protocol_2026-10-04.md), with the
separately specified [`ladder_protocol.md`](ladder_protocol.md). Run the
`research_*` scripts and `ladder_benchmark.py` for the current manuscript.
Graph Atlas is now completed; exhaustive n<=4,r=2 and n=5,r=1 are completed.
Full n=5,r=2 remains explicitly unexecuted.

All generators use master seed `20260928`. A per-instance seed is the unsigned integer represented by the first eight bytes of

```text
SHA256("20260928:family:grid_cell:replicate")
```

Bernoulli labeling forces one uniformly random rank when an edge receives no label; it therefore preserves the generated static structure. Every result row records the exact decimal answer, answer hash, bit length, wall time, peak RSS, compiler, flags, and machine identifier. Random comparisons stop immediately on the first mismatch and save the failing identity.

The current scripts provide:

- dense forest comparisons among the literal paper recurrence, dense prefix DP, and sparse DP;
- the mandatory all-times diamond-chain grid and closed-form-compatible exact results;
- recursive random TTSP instances checked against independent static-path enumeration;
- partial 2-trees with generated width-2 decompositions and arbitrary terminal pairs;
- a 6,500-instance default audit: 3,000 forests, 2,500 TTSP graphs, and 1,000 partial 2-trees.

Use a 60-second cell timeout for paper forest microbenchmarks and a 300-second timeout for a publication run. Do not omit timeouts from aggregate tables. Report medians and interquartile ranges rather than means alone. Decomposition construction is excluded from solver wall time.

The Graph Atlas and exhaustive `n<=5,r=2` campaigns described in the master handoff remain separate release gates; they are not silently represented by the randomized audit.
