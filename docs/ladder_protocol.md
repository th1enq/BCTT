# Ladder follow-up protocol

Added after the random partial-2-tree measurements, before measuring ladder
instances. The random crossover also showed that enumeration can win on small
graphs, so an explicit exponential-route family is useful alongside it.

Family: two-row ladders with c={4,8,12,16,24,32,64} columns, r={2,4,8},
all-times labels, query top-left to bottom-right. These queries are generally
not the poles of a TTSP expression, and the ladder is not a cactus for c>=3.

Every column cut has only two horizontal edges. A simple terminal path crosses
each cut an odd number of times and cannot use an edge twice, hence crosses
exactly once. It traverses a subset of q odd rungs, giving choose(c,q) routes
of length c-1+q. Thus there are 2^(c-1) static paths and the temporal oracle is
sum over odd q of choose(c,q)*choose(r+c+q-2,c-1+q).
For strict paths use choose(r,c-1+q), with out-of-range binomial zero.

Check these formulas against independent Python Cartesian enumeration for all
c=2..6, r=1..3, both modes before measurements. Measure brute, original DP,
compact DP with the identical timeout, affinity and seven-batch protocol.
Retain timeout records. The 21-cell supplement is stored separately, and the
aggregate combines it with the 169-cell final main run, never the exploratory
160-cell run. The main benchmark controller is unchanged.
