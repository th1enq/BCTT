# Implementation invariant and proof map

This document maps the theorem-level argument to the implementation in `src/tw_dp.cpp`.

The first argument below describes the non-strict baseline. The optimized
default, strict variant, and sharper complexity bound are stated afterward.

For every bag vertex, a state stores `ZERO`, `IN(t)`, `OUT(t)`, or `BOTH`, plus a canonical partition of active vertices. Selecting an edge chooses exactly one active time rank and one orientation. Endpoint transitions enforce indegree and outdegree at most one. A vertex becomes `BOTH` only after its local inequality `incoming_time <= outgoing_time` succeeds.

The selected partial graph remains a forest. At an introduce-edge node, endpoints already in the same partition block are rejected. At a join, the code constructs the child-component incidence multigraph implicitly with a disjoint-set structure: each bag vertex active in both children contributes one incidence edge; attempting to join two incidence nodes already connected detects ordinary and parallel-edge cycles. The parent partition is the transitive closure of both child partitions.

Forgetting a used nonterminal requires `BOTH`. It is rejected when it is the last bag representative of its component, so no selected component disappears behind the separator. The root bag is exactly `{s,z}` and accepts only `s=OUT(a)`, `z=IN(b)`, in one component. Thus an accepted object is a connected acyclic graph with terminal degree one and internal degree two: exactly one simple oriented `s`–`z` path. Chaining the checked local inequalities gives a nondecreasing global timestamp sequence.

Conversely, any temporal path determines one unique skip/orientation/rank choice at the unique introduction of each edge. Simplicity makes all cycle and degree checks pass; temporality makes all local comparisons pass; tree-decomposition connectedness ensures an internal vertex is complete before it is forgotten. Unique edge introduction also proves no double counting.

The parser validates that the decomposition is a rooted tree, contains both terminals in every bag, introduces every static edge exactly once, and ends with exactly the two terminals. Counts use unbounded integers.

For the baseline with normalized bag size `b <= w+3`, the state space is bounded by `(2r+2)^b B_b`; the correctness-first join checks state pairs. This gives the safe XP bound

```text
N (2r+2)^(2(w+3)) B_(w+3)^2 poly(w)
```

and hence `N r^{O(w)} 2^{O(w log w)}` arithmetic operations.

## Complete incidence lemma proof

Let q be the number of active vertices shared by the two edge-disjoint child
forests, and let c1,c2 be their component counts. Shared selected vertices occur
only in the bag by running intersection. The incidence multigraph J has c1+c2
vertices and q edges, including isolated component-nodes. Components of the
union correspond bijectively to components of J. Since Ei=Vi-ci,

```
beta(F1 union F2) = E1+E2-(V1+V2-q)+c(J)
                  = q-c1-c2+c(J) = beta(J).
```

Here beta=E-V+c is cycle rank, valid for multigraphs. The union is a forest iff
J is a forest. Two parallel incidence edges have cycle rank one. This avoids
the invalid shortcut that every closed walk contains a cycle (a walk can
backtrack over the same edge).

## Terminal pruning and quotient states

A final solution has no incoming edge at s and no outgoing edge at z. Degrees
only increase, so these edges can be rejected immediately. There is no local
time comparison at either terminal. Edge times remain remembered at adjacent
internal vertices until their IN/OUT inequality has been checked. Therefore
s and z need only ZERO/OUT* and ZERO/IN* respectively. In the implementation,
r+1 and 1 are placeholders for the used-terminal statuses, never timestamps
used in a terminal comparison. This quotient is enabled only with pruning.

At most b-2<=w+1 vertices carry timed signatures, so

```
S <= 4 (2r+2)^(w+1) B_(w+3)
time <= N (2r+2)^(2(w+1)) B_(w+3)^2 poly(w)
     = N (r+1)^(2w+2) 2^O(w log w).
```

For width two the arithmetic bound is O(N(r+1)^6). Introduce-edge costs r*S;
join costs S^2. Degree-shape indexing removes incompatible buckets but does not
improve the worst-case exponent. Releasing child tables gives safe O(h*S) live
state memory for decomposition height h, instead of retaining N*S states.

For strict paths change every internal IN/OUT comparison to `<`. Chaining the
local strict inequalities proves global strict temporality. All forest,
connectivity, uniqueness and quotient arguments are unchanged.

Let L be total input size (including M temporal labels and N decomposition
nodes). r<=M<=L and N<=L; do not assert M<=N. Integer bit length is polynomial:
all partial realizations are bounded by (1+2r)^m. If B is the maximum intermediate
bit length, schoolbook arithmetic adds an O(B^2) factor to this safe DP bound.

## Event DAG and cactus algorithms

Induction on a valid pole-to-pole TTSP expression gives an acyclic orientation
whose directed paths are exactly its undirected simple terminal paths. For each
time-edge retain a count of prefixes ending with that edge. At a vertex in
topological order, incoming events add these counts to a time-prefix sum and
outgoing events copy the sum. Incoming ties precede outgoing ties for non-strict;
reverse those groups for strict. Compressed-rank counting sort costs M+r.
The core performs exactly M count additions, O(n+m+M+r) operations/storage, and
no count multiplications. Input parsing/compression costs O(M log M), and the
current small-to-large hash-set TTSP validation has expected O(m log m) cost.
These costs are stated separately and auxiliary validation is timed.

For cactus arbitrary queries, a simple path must follow the unique block-cut
route. Each cycle contributes either of its two simple entry-exit arcs. Orient
that route toward the query target, then use the same event counter. Tarjan and
route extraction cost n+m. Off-route blocks cannot be visited without repeating
an articulation vertex. This argument does not extend to all arbitrary-terminal
SP queries: the Wheatstone graph requires both directions of an internal edge.

Proofs are internal mathematical arguments supported by audits. They are not
an independent referee verdict or a verified claim of first publication.
