# MASTER HANDOFF — Counting Temporal Paths on Forests, Series–Parallel, and Bounded-Treewidth Graphs

> Implementation update — 2026-10-04: the original research handoff below is
> retained as a historical specification. The completed upgrade adds TTSP event
> counting, arbitrary-terminal cactus counting, strict paths, terminal-compacted
> treewidth DP, 741,280 zero-mismatch comparisons and 190 repeated benchmark
> cells. Current proofs and exact comparison conditions are in
> `docs/research_contributions.md`; measured results are in
> `results/RESEARCH_BENCHMARK_REPORT.md`, and the thesis is
> `results/temporal_path_thesis.pdf`. The current bound uses N for nice-TD node
> count, not the input-size N in this earlier document. Full exhaustive n=5,r=2
> and independent proof/novelty review are not marked complete.

**Purpose:** single source of truth for an AI coding/research agent to implement, validate, benchmark, and reproduce the current research direction.

**Research date:** 2026-09-28  
**Target paper:** Jessica Enright, Kitty Meeks, Hendrik Molter, **“Counting Temporal Paths”**, *Algorithmica* 87, 736–782 (2025).  
**DOI:** https://doi.org/10.1007/s00453-025-01301-3  
**Open article:** https://link.springer.com/article/10.1007/s00453-025-01301-3  
**University of Glasgow copy:** https://eprints.gla.ac.uk/348161/  
**STACS 2023 extended abstract:** https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.STACS.2023.30

---

# 0. Executive summary

The original paper studies `#Temporal Path`: given an undirected temporal graph and two vertices \(s,z\), count all simple temporal \(s\)-\(z\) paths whose time labels are nondecreasing.

The paper proves, among other things:

1. `#Temporal Path` is hard in general.
2. It is polynomial-time solvable when the underlying graph is a forest, with the stated bound
   \[
   O(|V|T^2).
   \]
3. It is FPT for the **combined** parameter `(treewidth of the underlying graph + lifetime)`, via an MSO/Courcelle argument.
4. In the conclusion the authors explicitly conjecture that their polynomial-time forest result can be extended to **series–parallel graphs**.

Current research has produced the following results.

## Result A — Faster forest algorithm

The paper's forest recurrence can be evaluated in

\[
\boxed{O(|P|T)}
\]

rather than \(O(|P|T^2)\), where \(P\) is the unique static \(s\)-\(z\) path.

With sorted active-time lists it can be evaluated in

\[
\boxed{
O\!\left(
|P|+\sum_{e\in P}|L(e)|
\right)
}
\]

after sorting / rank compression. This is essentially linear in the relevant temporal input size.

## Result B — Exact two-terminal series–parallel transfer DP

For a two-terminal series–parallel (TTSP) graph whose query vertices are the two poles, define a temporal transfer matrix for every SP component.

Parallel composition becomes matrix addition:

\[
M_{H_1\parallel H_2}=M_{H_1}+M_{H_2}.
\]

Series composition becomes matrix multiplication:

\[
M_{H_1\circ H_2}=M_{H_1}M_{H_2}.
\]

This gives an exact

\[
\boxed{O(mr^3)}
\]

arithmetic-time algorithm with ordinary matrix multiplication, where \(r\) is the number of distinct time ranks and \(m\) is the number of static edges / \(O(m)\) decomposition size.

## Result C — Explicit XP algorithm parameterized only by underlying treewidth

Let

\[
w=\operatorname{tw}(G).
\]

Given a width-\(w\) tree decomposition, an explicit connectivity DP counts all non-strict temporal \(s\)-\(z\) paths in

\[
\boxed{
N\,T^{O(w)}2^{O(w\log w)}
}
\]

arithmetic operations, equivalently \(N^{O(w)}\) after time-rank compression, where

\[
N=|V|+|\mathcal E|.
\]

Therefore

\[
\boxed{\#TemporalPath\in XP\text{ parameterized by underlying treewidth}.}
\]

As an immediate corollary, every fixed-treewidth graph class is polynomial-time solvable.

Since undirected series–parallel / partial-2-tree graphs have treewidth at most \(2\),

\[
\boxed{\#TemporalPath\in P\text{ on series–parallel graphs}.}
\]

This resolves the explicit series–parallel conjecture from the 2025 paper, **provided the proof survives independent/external review and the novelty search remains clear**.

## Evidence already obtained in the research process

Prototype/reference implementations were checked against brute force on:

| Family | Comparisons | Mismatches |
|---|---:|---:|
| Random temporal paths / forests | 3,000 | 0 |
| Random TTSP instances | 2,500 | 0 |
| Random partial 2-trees | 550 | 0 |
| Graph Atlas, \(tw\le2,n\le7\), many \((s,z)\) queries | 6,088 | 0 |
| Exhaustive temporal labels, \(tw\le2,n\le5,T=2\) | 97,635 | 0 |
| **Total** | **109,773** | **0** |

These figures are **research-log evidence**, not a substitute for rerunning everything in the final repository. The implementation agent must reproduce them from scratch.

---

# 1. What is officially in the original paper

This section distinguishes paper-supported claims from our new research.

## 1.1 Problem

A temporal graph is

\[
\mathcal G=(V,\mathcal E,T),
\]

where a time-edge is a pair \((e,t)\), \(e\) is a static edge and \(t\in[T]\).

The paper focuses on **non-strict** temporal paths: if

\[
((e_1,t_1),\ldots,(e_k,t_k))
\]

is a temporal path, then the underlying edges form a simple static path and

\[
t_1\le t_2\le\cdots\le t_k.
\]

The query is:

> Given \((\mathcal G,s,z)\), count all temporal \(s\)-\(z\) paths.

## 1.2 Paper's forest theorem

The paper's Theorem 2 states:

\[
\boxed{
\#TemporalPath\text{ is solvable in }O(|V|T^2)
\text{ if the underlying graph is a forest}.
}
\]

For the unique static path

\[
P=(v_0=s,v_1,\ldots,v_\ell=z),
\]

the paper defines

\[
F(v_0,t)=1
\]

and

\[
F(v_i,t)
=
\sum_{\substack{(\{v_{i-1},v_i\},t')\in\mathcal E\\t'\le t}}
F(v_{i-1},t').
\]

Source: Section 4.1 / Theorem 2 of the Algorithmica article.

## 1.3 Paper's treewidth+lifetime result

Theorem 6 states that `#Temporal Path` is FPT parameterized by the **combination** of:

- treewidth of the underlying graph;
- temporal lifetime \(T\).

The proof is based on an MSO encoding and a counting form of Courcelle's theorem.

This is a theoretical meta-algorithm; the paper does **not** provide a practical implementation benchmark for it.

## 1.4 Paper's explicit open conjecture

The conclusion says that the authors conjecture that the forest polynomial-time algorithm can be extended to the case in which the underlying graph is **series–parallel**, mentioning the possibility of extending the dynamic program to parallel compositions.

This is the exact open direction targeted by the present research.

## 1.5 Important reproducibility fact: the original paper has no official benchmark suite

The University of Glasgow repository entry for the final Algorithmica paper states:

> **Data Availability Statement: No**

Source:
https://eprints.gla.ac.uk/348161/

The article also contains no experimental/implementation section and the searches performed for the paper title + GitHub / code / benchmark / artifact did not locate an author-provided implementation or benchmark archive.

**Therefore there are no “official paper instances” or official runtime tables to download and reproduce.**

This matters for the thesis:

- Do **not** claim that a synthetic suite is “the official benchmark of Enright et al.”
- The correct comparison with the paper is:
  1. reproduce the paper's stated forest recurrence as a baseline;
  2. verify its output against our algorithms;
  3. compare asymptotic and measured runtime on a new, fully specified reproducible benchmark suite;
  4. compare theoretically against the paper's Theorems 2 and 6;
  5. state explicitly that the original paper is theoretical and supplies no runtime dataset/code.

---

# 2. Required notation

Use these names consistently in code and write-up.

- \(V\): vertices.
- \(E\): static underlying edges.
- \(\mathcal E\): time-edges.
- \(T\): original maximum time label / lifetime.
- \(r\): number of distinct time values after rank compression.
- \(L(e)\): sorted list of active time ranks of static edge \(e\).
- \(s,z\): query endpoints.
- \(G=(V,E)\): static underlying graph.
- \(N=|V|+|\mathcal E|\): convenient input-size proxy.
- \(w=\operatorname{tw}(G)\).

Counts must use arbitrary-precision integers.

C++ recommendation:

```cpp
boost::multiprecision::cpp_int
```

Python reference code naturally uses arbitrary-precision `int`.

---

# 3. Preprocessing theorem: time-rank compression

## Lemma

Let the distinct timestamps that actually occur in \(\mathcal E\) be

\[
\tau_1<\tau_2<\cdots<\tau_r.
\]

Replace every timestamp \(\tau_i\) by rank \(i\).

Then the map is a bijection between temporal paths before and after compression.

## Proof

Temporal feasibility uses only comparisons of the form

\[
t_i\le t_{i+1}.
\]

The rank map is strictly order preserving:

\[
\tau_i\le\tau_j
\iff
i\le j.
\]

The underlying static path and the selected time-edge for each static edge are unchanged. Hence every temporal path maps to exactly one temporal path and vice versa.

\[
\boxed{\#\text{paths is unchanged}.}
\]

## Implementation

Always rank-compress first unless a benchmark explicitly measures behavior versus an uncompressed raw timestamp domain.

After compression:

\[
r\le|\mathcal E|.
\]

Use ranks `1..r`.

---

# 4. Algorithm A0 — paper-faithful forest baseline

This baseline exists solely for correctness/runtime comparison with Theorem 2.

Given a forest, obtain the unique static \(s\)-\(z\) path. If \(s,z\) are disconnected, answer 0.

Let:

\[
P=(v_0=s,\ldots,v_\ell=z),\quad e_i=\{v_{i-1},v_i\}.
\]

Implement the recurrence exactly:

```text
F[0][t] = 1 for all t

for i = 1..ell:
    for t = 1..r:
        F[i][t] = 0
        for each t' in L(e_i):
            if t' <= t:
                F[i][t] += F[i-1][t']

return F[ell][r]
```

A deliberately literal implementation costs roughly

\[
O(|P|r^2)
\]

in the dense worst case.

### Important

Do not optimize this baseline accidentally. It is needed to empirically demonstrate the improvement.

Name it:

```text
forest_paper
```

---

# 5. Algorithm A1 — dense prefix forest DP

The paper recurrence satisfies:

\[
F_i(t)
=
F_i(t-1)
+
\mathbf 1[t\in L(e_i)]F_{i-1}(t).
\]

Therefore:

```text
prev[t] = 1 for all t

for edge e_i along P:
    cur[0] = 0
    for t = 1..r:
        cur[t] = cur[t-1]
        if e_i is active at t:
            cur[t] += prev[t]
    swap(prev, cur)

return prev[r]
```

Runtime:

\[
\boxed{O(|P|r)}
\]

with \(O(r)\) working memory.

Precompute each \(L(e)\) as a bitset / Boolean array only for the dense implementation.

Name:

```text
forest_dense_prefix
```

---

# 6. Algorithm A2 — sparse forest DP

This should be the preferred forest implementation.

Define:

\[
C_i(t)=
\#\{\text{temporal prefixes reaching }v_i
\text{ whose last edge is used exactly at }t\}
\]

for \(t\in L(e_i)\).

Base:

\[
C_1(t)=1
\quad
\forall t\in L(e_1).
\]

For \(i>1\):

\[
\boxed{
C_i(t)
=
\sum_{\substack{\tau\in L(e_{i-1})\\\tau\le t}}
C_{i-1}(\tau).
}
\]

Since both lists are sorted, scan using one pointer and a running sum:

```text
times_prev = L(e_{i-1})
count_prev = C_{i-1}

prefix = 0
j = 0

for t in L(e_i) increasing:
    while j < len(times_prev) and times_prev[j] <= t:
        prefix += count_prev[j]
        j += 1
    count_cur[t] = prefix
```

Final answer:

\[
\sum_{t\in L(e_\ell)}C_\ell(t).
\]

Runtime after sorted labels:

\[
\boxed{
O\left(
|P|+\sum_{e\in P}|L(e)|
\right).
}
\]

Memory can be only two consecutive sparse vectors.

Name:

```text
forest_sparse
```

---

# 7. Closed-form correctness oracles for paths

These are mandatory unit tests.

If a path has \(\ell\) static edges and **every edge is active at every rank** \(1,\ldots,r\), then every nondecreasing length-\(\ell\) sequence is valid.

Therefore:

\[
\boxed{
\#TP(P_\ell)=
\binom{r+\ell-1}{\ell}.
}
\]

Example:

- one edge, \(r=3\): 3;
- two edges, \(r=3\): \(\binom42=6\).

Another manual case:

```text
L(e1) = {1,2}
L(e2) = {2,3}
```

valid pairs are:

```text
(1,2), (1,3), (2,2), (2,3)
```

so expected answer = 4.

---

# 8. Algorithm B — TTSP transfer matrices

This is an exact algorithm for a **two-terminal series–parallel decomposition** whose poles equal the query endpoints.

For each SP component \(H\) with poles \(x,y\), define:

\[
M_H[a,b]
=
\#\{
\text{temporal }x\!-\!y\text{ paths inside }H:
\text{ first time}\ge a,\,
\text{ last time}=b
\}.
\]

Indices:

\[
a,b\in[r].
\]

## 8.1 Base edge

For a single static edge \(e=xy\):

\[
M_e[a,b]
=
\begin{cases}
1,&b\in L(e)\text{ and }a\le b,\\
0,&\text{otherwise}.
\end{cases}
\]

## 8.2 Parallel composition

If:

\[
H=H_1\parallel H_2,
\]

the branches share only the poles.

A simple path from one pole to the other must lie entirely inside one branch.

Thus:

\[
\boxed{
M_H=M_{H_1}+M_{H_2}.
}
\]

## 8.3 Series composition

If:

\[
H=H_1\circ H_2,
\]

and \(q\) is the identified intermediate pole, then every simple pole-to-pole path decomposes uniquely into one path in \(H_1\) followed by one path in \(H_2\).

If \(H_1\) ends at rank \(k\), the path in \(H_2\) must have first rank at least \(k\).

Hence:

\[
M_H[a,b]
=
\sum_{k=1}^{r}
M_{H_1}[a,k]M_{H_2}[k,b].
\]

So:

\[
\boxed{M_H=M_{H_1}M_{H_2}.}
\]

## 8.4 Final answer

For the root component:

\[
\boxed{
\#TP(s,z)=
\sum_{b=1}^{r}M_G[1,b].
}
\]

## 8.5 Complexity

An SP decomposition has \(O(m)\) nodes.

- base/parallel: \(O(r^2)\);
- series: \(O(r^3)\) with ordinary multiplication.

Thus:

\[
\boxed{O(mr^3)}
\]

arithmetic operations.

Optional future optimization: exploit triangular/monotone matrix structure before considering generic fast matrix multiplication.

Name:

```text
ttsp_transfer
```

---

# 9. Closed-form TTSP oracle: diamond chains

A diamond contains two internally vertex-disjoint length-2 branches between its poles.

A chain of \(k\) diamonds has:

\[
2^k
\]

static pole-to-pole paths, each of static length \(2k\).

If every static edge is active at every one of \(r\) time ranks, then each static path has

\[
\binom{r+2k-1}{2k}
\]

nondecreasing timestamp assignments.

Therefore:

\[
\boxed{
\#TP=
2^k
\binom{r+2k-1}{2k}.
}
\]

This is a key scalability oracle because the number of static paths is exponential while the answer is available in closed form.

Mandatory benchmark values:

```text
k = 1,2,4,8,16,32,64,128,256
r = 2,4,8,16,32
```

where memory/time permits.

---

# 10. Main theorem — XP by underlying treewidth

## Theorem

Let \((\mathcal G,s,z)\) be a non-strict `#Temporal Path` instance and let

\[
w=\operatorname{tw}(G)
\]

for the static underlying graph.

Given a width-\(w\) tree decomposition, the exact number of temporal \(s\)-\(z\) paths can be computed in

\[
\boxed{
N\,T^{O(w)}2^{O(w\log w)}
}
\]

arithmetic operations.

After time-rank compression this is

\[
\boxed{N^{O(w)}}.
\]

Consequently:

\[
\boxed{\#TemporalPath\in XP\text{ parameterized by }w.}
\]

---

# 11. Local temporal lemma

Orient any selected static \(s\)-\(z\) path from \(s\) toward \(z\).

At every internal vertex \(v\), let:

\[
t_{\rm in}(v)
\]

be the timestamp of its incoming selected edge and

\[
t_{\rm out}(v)
\]

the timestamp of its outgoing selected edge.

Then:

\[
\boxed{
P\text{ is temporal}
\iff
t_{\rm in}(v)\le t_{\rm out}(v)
\text{ for every internal }v.
}
\]

Proof is immediate by chaining the adjacent inequalities.

This is the critical reason the temporal constraint can be handled locally in a tree-decomposition DP.

---

# 12. Tree-decomposition normalization

For the cleanest correctness proof:

1. obtain a width-\(w\) tree decomposition of \(G\);
2. add \(s\) and \(z\) to every bag;
3. width rises by at most 2;
4. convert to a nice tree decomposition with:
   - leaf,
   - introduce-vertex,
   - introduce-edge,
   - forget-vertex,
   - join nodes;
5. introduce every **static edge exactly once**.

If the original width is \(w\), normalized bag size is at most:

\[
b=w+3.
\]

For generated benchmark graphs, always output a decomposition alongside the graph so decomposition computation is not part of solver timing.

---

# 13. Partial-solution invariants

At a tree-decomposition node \(x\), let \(E_x\) be the static edges introduced in its subtree.

A partial realization chooses a subset of \(E_x\), and for each selected static edge:

- one active time rank from \(L(e)\);
- one orientation.

Maintain:

### I1. Degree

\[
d^-(v)\le1,\qquad d^+(v)\le1.
\]

### I2. No static cycle

Selected underlying edges form a forest.

### I3. Local temporal validity

Whenever both selected incident path edges of a vertex are known:

\[
t_{\rm in}\le t_{\rm out}.
\]

### I4. Forgotten used vertices are complete

Every selected vertex outside the current bag has:

\[
d^-=d^+=1.
\]

### I5. No selected component disappears from the separator

Every connected component of the selected partial forest intersects the current bag.

These invariants are sufficient for the final object to be one simple temporal \(s\)-\(z\) path.

---

# 14. Bag state

For each bag vertex \(v\), store one local status:

```text
ZERO
IN(t)     for t in 1..r
OUT(t)    for t in 1..r
BOTH
```

Meaning:

- `ZERO`: no selected incident processed edge;
- `IN(t)`: one incoming selected edge at rank `t`;
- `OUT(t)`: one outgoing selected edge at rank `t`;
- `BOTH`: exactly one incoming and one outgoing edge are already present and the local temporal inequality has passed.

Important:

> `BOTH` does not need to remember either timestamp.

Once a vertex reaches `BOTH`, no additional selected incident edge is legal.

Local-state count per bag vertex:

\[
2r+2.
\]

Also store a connectivity partition \(\Pi\) of active bag vertices (`status != ZERO`):

two vertices are in the same block iff they belong to the same selected partial component.

Full state:

\[
\boxed{(\sigma,\Pi)}.
\]

The table value is an arbitrary-precision count.

---

# 15. Leaf transition

Use root/leaf convention consistently.

With \(s,z\) present globally, an empty starting bag may be normalized to contain \(s,z\) only.

Initial state:

```text
s = ZERO
z = ZERO
partition = empty
count = 1
```

---

# 16. Introduce-vertex transition

A newly introduced vertex has no selected processed incident edge.

Set:

```text
status[v] = ZERO
```

and copy the child state.

---

# 17. Introduce-edge transition

For static edge:

\[
e=\{u,v\},
\]

choices are:

1. skip;
2. select as \(u\to v\) at each \(t\in L(e)\);
3. select as \(v\to u\) at each \(t\in L(e)\).

## Endpoint update helper

Adding an outgoing edge at rank \(t\):

```text
ZERO   -> OUT(t)
IN(a)  -> BOTH if a <= t
OUT(a) -> invalid
BOTH   -> invalid
```

Adding an incoming edge at rank \(t\):

```text
ZERO    -> IN(t)
OUT(a)  -> BOTH if t <= a
IN(a)   -> invalid
BOTH    -> invalid
```

Note the inequality direction.

## Cycle test

Before selecting \(uv\):

- if both endpoints are active and are already in the same connectivity block, reject;
- otherwise merge/create blocks appropriately.

This preserves the selected graph as a forest.

---

# 18. Forget-vertex transition

Only nonterminals are forgotten, because \(s,z\) were added globally.

For a vertex \(v\):

- `ZERO` is allowed;
- `BOTH` is allowed;
- `IN(t)` or `OUT(t)` is rejected.

Reason: once forgotten, no future bag can contain \(v\), hence no future incident static edge can be introduced. A used nonterminal must already have exactly one incoming and one outgoing edge.

## Component disappearance rule

If \(v\) is the **last bag vertex** belonging to its selected connected component, reject.

Otherwise remove \(v\) from its partition block.

This enforces invariant I5.

---

# 19. Join transition

A join node has two children with identical bag \(B\). Their introduced static-edge sets are disjoint.

## 19.1 Local-status compatibility

For each bag vertex:

```text
ZERO + X = X
IN(a) + OUT(b) = BOTH iff a <= b
OUT(b) + IN(a) = BOTH iff a <= b
IN + IN = invalid
OUT + OUT = invalid
BOTH + nonZERO = invalid
BOTH + ZERO = BOTH
ZERO + BOTH = BOTH
```

## 19.2 Join-cycle test

This is the most delicate part and must be implemented exactly.

Let child selected forests be \(F_1,F_2\).

Construct a bipartite **incidence multigraph** \(J\):

- one left node for every selected connected component of \(F_1\) touching the bag;
- one right node for every selected connected component of \(F_2\) touching the bag;
- for every bag vertex active in **both** children, add an edge joining the child-1 component containing it and the child-2 component containing it.

Parallel incidence edges count as a length-2 cycle in the multigraph.

Then:

\[
\boxed{
F_1\cup F_2\text{ is acyclic}
\iff
J\text{ is acyclic}.
}
\]

Reject iff \(J\) contains a cycle.

### Proof sketch

- If \(J\) has a cycle, consecutive incidence edges correspond to two bag vertices in the same child component. Since each child component is a tree, their unique internal paths combine around the incidence cycle to form a static cycle in \(F_1\cup F_2\). Parallel edges give two different shared bag vertices and two distinct child paths between them, also forming a cycle.
- Conversely, any cycle in \(F_1\cup F_2\) cannot lie in one child because each child is a forest. Break it into maximal alternating child subpaths and contract each to its child component. This gives a closed walk in \(J\), hence \(J\) contains a cycle.

## 19.3 New partition

If accepted, the new partition is the transitive closure of child connectivity relations:

\[
\Pi=\operatorname{closure}(\Pi_1\cup\Pi_2).
\]

## 19.4 Count

```text
parent[new_state] += left[state1] * right[state2]
```

---

# 20. Root acceptance

At the root all nonterminals have been forgotten.

Accept exactly states with:

```text
s = OUT(a) for some a
z = IN(b)  for some b
partition = { {s,z} }
```

Sum counts over all possible endpoint ranks.

No other selected component can exist because of invariant I5.

---

# 21. Correctness proof

The implementation should carry a theorem-level proof in documentation/tests.

## 21.1 Soundness

Every accepted DP realization has:

- acyclic selected underlying graph;
- every used internal vertex degree 2;
- \(s,z\) degree 1;
- one connected component containing \(s,z\);
- no hidden/disappeared component.

Therefore the selected underlying graph is exactly a simple static \(s\)-\(z\) path.

Degree/orientation constraints imply:

- \(s\) has one outgoing and no incoming;
- \(z\) has one incoming and no outgoing;
- each internal vertex has one incoming and one outgoing.

On an undirected path this forces the orientation from \(s\) to \(z\).

Every internal vertex has already passed:

\[
t_{\rm in}\le t_{\rm out}.
\]

By the local temporal lemma, the complete timestamp sequence is nondecreasing.

Hence every accepted realization is a temporal \(s\)-\(z\) path.

## 21.2 Completeness

Take any temporal \(s\)-\(z\) path.

At the unique introduce-edge node of each path edge, choose exactly:

- that edge;
- its temporal-path timestamp;
- its \(s\)-to-\(z\) orientation.

Skip all other static edges.

Because the path is simple:

- no degree rule fails;
- no introduce-edge cycle test fails;
- no join incidence cycle test fails.

Because it is temporal, every local timestamp test succeeds.

When an internal path vertex is forgotten, both its path edges must already have been introduced by the connectedness property of a tree decomposition, so its status is `BOTH`.

Thus every temporal path induces an accepting computation.

## 21.3 No double counting

Each temporal path uniquely determines for every static edge:

- skip, or
- one orientation and one timestamp.

Each static edge is introduced exactly once.

The two join subtrees have disjoint introduced-edge sets.

Therefore the same temporal path cannot correspond to two different DP derivations.

So the DP counts every temporal path exactly once.

---

# 22. Complexity proof

Normalized bag size:

\[
b\le w+3.
\]

Local signatures:

\[
(2r+2)^b.
\]

Number of partitions of at most \(b\) active elements:

\[
B_b
\]

(the Bell number), with

\[
B_b\le b^b=2^{O(b\log b)}.
\]

States per bag:

\[
S_b\le(2r+2)^bB_b.
\]

Introduce/forget transitions are polynomial in \(S_b,r,b\).

A deliberately simple join tries all pairs:

\[
O(S_b^2\operatorname{poly}(b)).
\]

Thus:

\[
\boxed{
O\!\left(
N(2r+2)^{2(w+3)}
B_{w+3}^2\operatorname{poly}(w)
\right)
}
\]

is a concrete safe bound for the naive implementation.

Asymptotically:

\[
\boxed{
N\,r^{O(w)}2^{O(w\log w)}.
}
\]

Since \(r\le|\mathcal E|\le N\),

\[
\boxed{N^{O(w)}}.
\]

Therefore the problem is in XP parameterized by underlying treewidth.

---

# 23. Bit complexity

Do not hide large-integer cost.

For every static edge there are at most:

- one skip choice;
- \(2r\) orientation/time choices.

A crude upper bound on a DP count is:

\[
(1+2r)^{|E|}.
\]

Hence a count needs at most

\[
O(|E|\log r)
\]

bits.

For fixed \(w\), all arithmetic remains polynomial-bit complexity.

Benchmark both:

- wall time;
- maximum answer bit length.

---

# 24. Series–parallel corollary

Undirected series–parallel / partial-2-tree graphs have treewidth at most 2.

Substitute:

\[
w=2.
\]

The XP algorithm becomes polynomial.

Thus:

\[
\boxed{
\#TemporalPath\text{ is polynomial-time solvable on series–parallel graphs}.
}
\]

A very coarse explicit bound from the naive join implementation has bag size at most 5 and contains a factor on the order of \(r^{10}\), but **do not present \(r^{10}\) as optimized**. It is only a simple proof-of-polynomiality bound.

For practical SP instances, use either:

- `ttsp_transfer` when the query matches TTSP poles;
- `tw_dp` for arbitrary query endpoints.

---

# 25. Relationship to the original paper's hardness result

The paper proves strong evidence against an FPT algorithm parameterized only by underlying feedback vertex number, which also rules out an FPT algorithm parameterized only by treewidth under the relevant assumptions.

Our result is:

\[
N^{O(w)},
\]

which is **XP**, not FPT.

There is no contradiction.

This distinction must be explicit in the thesis.

---

# 26. Repository architecture for the implementation agent

Recommended:

```text
temporal-path-counting/
├── README.md
├── CITATION.cff
├── CMakeLists.txt
├── src/
│   ├── temporal_graph.hpp
│   ├── temporal_graph.cpp
│   ├── rank_compress.hpp
│   ├── forest_paper.hpp
│   ├── forest_paper.cpp
│   ├── forest_dense.hpp
│   ├── forest_dense.cpp
│   ├── forest_sparse.hpp
│   ├── forest_sparse.cpp
│   ├── ttsp.hpp
│   ├── ttsp.cpp
│   ├── tree_decomposition.hpp
│   ├── tree_decomposition.cpp
│   ├── nice_td.hpp
│   ├── nice_td.cpp
│   ├── tw_dp.hpp
│   ├── tw_dp.cpp
│   └── main.cpp
├── python/
│   ├── brute_force.py
│   ├── static_path_reference.py
│   ├── generators.py
│   ├── gen_partial_ktree.py
│   ├── gen_ttsp.py
│   ├── benchmark.py
│   ├── aggregate.py
│   └── plots.py
├── tests/
│   ├── test_manual.py
│   ├── test_forest_exhaustive.py
│   ├── test_ttsp_random.py
│   ├── test_tw2_exhaustive.py
│   └── test_join_cases.py
├── benchmarks/
│   ├── manifest.json
│   ├── generated/
│   └── external/
├── results/
└── docs/
    ├── proof.md
    └── experiment_protocol.md
```

Use C++20 for final timings and Python for independent reference/generation.

---

# 27. Required command-line interface

Implement one executable, for example:

```text
tpcount
```

Suggested commands:

```bash
tpcount count --solver forest-paper instance.tg
tpcount count --solver forest-dense instance.tg
tpcount count --solver forest-sparse instance.tg
tpcount count --solver ttsp-transfer instance.tg --decomp instance.sp
tpcount count --solver tw-dp instance.tg --td instance.td

tpcount verify instance.tg --solver tw-dp --reference brute
tpcount info instance.tg
```

Output JSON:

```json
{
  "solver": "tw-dp",
  "count": "123456789...",
  "count_bits": 417,
  "wall_ms": 12.31,
  "peak_rss_mb": 18.7,
  "n": 50,
  "m_static": 83,
  "m_temporal": 421,
  "time_ranks": 12,
  "treewidth_input": 2,
  "states_created": 15320,
  "states_peak_bag": 1840,
  "join_pairs_tested": 99102
}
```

---

# 28. Input format

Define and document a simple canonical format:

```text
p n m_temporal s z
u v t
u v t
...
```

Example:

```text
p 3 4 0 2
0 1 1
0 1 2
1 2 2
1 2 3
```

Treat edges as undirected.

Deduplicate identical triples `(min(u,v), max(u,v), t)`.

Reject self-loops.

Rank-compress timestamps after parsing.

Static edge \(uv\) exists iff at least one time-edge \(uv,t\) exists.

---

# 29. Independent brute-force validators

At least two independent reference methods are recommended.

## B0 — full brute force

For tiny graphs:

1. enumerate every simple static \(s,z\) path by DFS;
2. enumerate Cartesian product of active-time lists on its edges;
3. count nondecreasing assignments.

This is slow but maximally independent.

## B1 — static-path + label-DP reference

For each simple static \(s,z\) path:

1. run a tiny path temporal DP to count valid labels;
2. sum.

This scales farther than B0 while remaining structurally independent from the treewidth DP.

Never use the same state-transition code in solver and validator.

---

# 30. Mandatory unit tests

## U1. Single edge

```text
L(sz) = {1,3}
expected = 2
```

## U2. Two-edge path

```text
L(e1) = {1,2}
L(e2) = {2,3}
expected = 4
```

## U3. Dense path

For path length \(\ell\), all ranks active:

\[
expected=\binom{r+\ell-1}{\ell}.
\]

## U4. One diamond, all ranks active

\[
expected=
2\binom{r+1}{2}.
\]

## U5. Diamond chain

\[
expected=
2^k\binom{r+2k-1}{2k}.
\]

## U6. Triangle, all edges active only at time 1

For \(s,z\) two triangle vertices, static simple paths are:

```text
s-z
s-a-z
```

Expected = 2.

## U7. Temporal ordering rejection

Path:

```text
e1 only at 2
e2 only at 1
```

Expected = 0.

## U8. Equal timestamps accepted

Path:

```text
e1 at 5
e2 at 5
```

Expected = 1 for the non-strict problem.

---

# 31. Focused join-node tests

Join logic deserves its own exhaustive micro-suite.

Construct child partitions manually and verify:

1. one shared bag vertex → no cycle;
2. same two child components share two different bag vertices → reject via parallel incidence edges;
3. incidence square → reject;
4. incidence tree/path → accept;
5. local `IN(a)+OUT(b)`:
   - accept if \(a\le b\);
   - reject otherwise;
6. `IN+IN`, `OUT+OUT`, `BOTH+nonZERO` reject.

Run these without needing full temporal graphs.

---

# 32. Benchmark reality: there is no official instance pack from the paper

This section is critical.

The original Algorithmica paper is primarily theoretical. The Glasgow repository explicitly says:

```text
Data Availability Statement: No
```

No author benchmark archive or implementation was found in the literature/code search performed up to **2026-09-28**.

Therefore the experimental chapter must introduce a **new reproducible benchmark suite**.

Use the phrase:

> “paper-faithful reproducible benchmark suite”

not:

> “official instances of the original paper”.

The official comparison targets are the **paper's algorithms/theorems**, especially Theorem 2.

---

# 33. Benchmark Suite F — forests

Goal:

1. validate the asymptotic improvement
   \[
   O(nT^2)\to O(nT)\to O(|\mathcal E_P|);
   \]
2. compare to the paper-faithful recurrence.

## F1. Dense paths

Grid:

```text
path_edges L = 10, 20, 50, 100, 200, 500, 1000
r            = 10, 20, 50, 100, 200, 500, 1000
```

All static edges active at all ranks.

Use closed-form answer.

Run solvers:

```text
forest_paper
forest_dense_prefix
forest_sparse
```

The `forest_paper` solver will timeout for large cells. Record timeout rather than reducing the grid silently.

Recommended timeout:

```text
60 s per instance
```

## F2. Sparse paths

Grid:

```text
L = 100, 500, 1000, 5000, 10000
r = 100, 1000, 5000, 10000
labels_per_edge k = 1, 2, 4, 8, 16, 32
```

For every static edge choose exactly `min(k,r)` distinct ranks uniformly.

Run:

```text
forest_dense_prefix
forest_sparse
```

Expected story: sparse solver scales with the number of time-edges rather than \(Lr\).

## F3. Random trees

Generate random labeled trees using Prüfer sequences.

```text
n = 100, 500, 1000, 5000
r = 16, 64, 256
labels_per_edge = 1,4,16
queries per tree = 20
```

Only the unique static \(s,z\) path is relevant.

Report runtime both including and excluding static-path extraction.

---

# 34. Benchmark Suite S — TTSP

## S1. Diamond chains

Mandatory:

```text
k diamonds = 1,2,4,8,16,32,64,128,256
r          = 2,4,8,16,32
```

Temporal modes:

```text
ALL       : every edge at every rank
FIXED-k   : exactly q labels/edge, q=1,2,4,8
BERNOULLI : each (edge,time) active independently p=0.1,0.5,0.9
```

For `ALL`, verify against the closed form.

Compare:

- `ttsp_transfer`;
- `tw_dp`;
- brute force only for tiny k.

## S2. Random TTSP decomposition trees

Generate recursively with a fixed random seed.

Avoid accidental multiedges if the target model is a simple graph. Safest option:

- use edge-disjoint fresh internal vertices;
- when creating a parallel operation, ensure branches are not both single identical pole edges;
- alternatively merge duplicate static edges by unioning their time labels and document this.

Grid:

```text
static edges approximately = 20, 50, 100, 200, 500, 1000
r                          = 4, 8, 16, 32, 64
parallel probability       = 0.25, 0.5, 0.75
```

10 instances per cell.

---

# 35. Benchmark Suite P2 — arbitrary partial 2-trees / series–parallel-width instances

This is the main benchmark for the conjecture because query endpoints are arbitrary.

Generate a 2-tree:

1. start with a triangle;
2. repeatedly pick an existing edge \(uv\);
3. add new vertex \(x\) adjacent to \(u,v\).

Optionally delete static edges while preserving connectivity. Edge deletion cannot increase treewidth.

Save the decomposition/elimination construction with the instance.

Grid:

```text
n = 10, 20, 50, 100, 200, 500
r = 2, 4, 8, 16, 32
edge-delete probability = 0.0, 0.2, 0.5
temporal mode = fixed-label or Bernoulli
```

For each static graph:

```text
20 random (s,z) pairs
```

For small cases compare with brute/static-path reference.

For large cases run only `tw_dp`.

Metrics:

- runtime;
- peak memory;
- number of DP states;
- peak states per bag;
- join candidate pairs;
- output bit length.

---

# 36. Benchmark Suite W — fixed treewidth beyond the conjecture

This demonstrates the theorem is stronger than series–parallel.

Generate partial \(k\)-trees for:

```text
w = 3,4,5
```

Construction:

1. start with \(K_{w+1}\);
2. choose an existing \(w\)-clique;
3. add a new vertex adjacent to all vertices of that clique;
4. optionally delete edges afterward.

Keep a known width-\(w\) decomposition.

Suggested grid:

```text
w = 3: n = 10,20,40,80,160 ; r = 2,4,8,16
w = 4: n = 10,20,40,80     ; r = 2,4,8
w = 5: n = 10,20,40        ; r = 2,4,8
```

Do not hide timeouts.

This suite empirically illustrates XP behavior as \(w\) grows.

---

# 37. Correctness-audit suite

Reproduce from scratch rather than trusting historical numbers.

## C1. Random forests

Target:

```text
>= 3,000 brute-force comparisons
```

## C2. Random TTSP

Target:

```text
>= 2,500 comparisons
```

## C3. Random partial 2-trees

Target:

```text
>= 1,000 comparisons
```

if compute budget allows.

## C4. Graph Atlas

Using NetworkX Graph Atlas:

- enumerate connected graphs up to 7 vertices;
- keep those with certified \(tw\le2\);
- assign small random temporal labels;
- test all unordered \(s,z\) pairs.

## C5. Exhaustive temporal label assignments

For all connected \(tw\le2\) graphs up to 5 vertices, use:

```text
r = 2
```

and assign every static edge one of the three nonempty active sets:

```text
{1}, {2}, {1,2}
```

Test all \(s,z\).

The previous research log obtained 97,635 comparisons here; the final repository must recalculate this number and report the exact generated count.

**Hard rule:** if any mismatch occurs, stop the benchmark campaign and minimize the counterexample before continuing.

---

# 38. Deterministic random seeds

Use one master seed:

```text
MASTER_SEED = 20260928
```

Derive per-instance seeds deterministically:

```text
seed = uint64(first_8_bytes(
    SHA256(f"{MASTER_SEED}:{family}:{grid_cell}:{replicate}")
))
```

This prevents generator/library version changes from silently changing seed scheduling.

Record the actual derived seed in every result row.

---

# 39. Temporal-label generators

Implement at least three.

## L1. Fixed number of labels per edge

For every static edge, choose exactly:

\[
q
\]

distinct ranks uniformly without replacement.

Good for controlling \(|\mathcal E|\).

## L2. Bernoulli density

For every pair `(static edge, rank)`, activate independently with probability \(p\).

If no rank activates for an edge, either:

- remove the static edge, or
- force one random rank.

Pick one policy and state it clearly.

Recommended for structure-preserving benchmarks:

> force one uniformly random label if none activated.

## L3. All times

Every edge active at every rank.

Useful for closed forms and dense worst cases.

Optional later: bursty labels based on short random intervals, but this is not required for the first thesis version.

---

# 40. What can actually be compared to the original paper experimentally?

## Direct fair comparison

### Paper Theorem 2

Implement:

```text
forest_paper
```

from the recurrence in Section 4.1.

Compare against:

```text
forest_dense_prefix
forest_sparse
```

on identical instances.

Report:

- exact answer agreement;
- runtime;
- peak memory;
- empirical scaling exponent.

This is the strongest runtime comparison to the original paper.

## Theorem 6 comparison

The paper's treewidth+lifetime result is obtained through MSO/Courcelle and does not give an author implementation/runtime benchmark.

Therefore:

- compare **theoretical parameter dependence**, not fabricated runtime;
- state that our algorithm is explicit and XP in treewidth alone;
- do not claim to experimentally beat an implementation that does not exist.

## Series–parallel comparison

There is no paper solver, because series–parallel is stated as a conjecture/open direction.

Comparison is therefore:

```text
paper: open conjecture
ours : explicit exact polynomial-time algorithm
```

with brute force used only as a correctness reference on small instances.

---

# 41. Required experimental plots

Produce at least:

1. **Forest dense:** runtime vs \(r\), separate lines for paper / dense-prefix / sparse.
2. **Forest sparse:** runtime vs number of temporal edges \(|\mathcal E_P|\).
3. **Forest speedup:** `paper_time / our_time`.
4. **TTSP diamond:** runtime vs number of diamonds \(k\).
5. **TTSP:** runtime vs \(r\).
6. **General partial-2-tree:** runtime vs \(n\).
7. **General partial-2-tree:** runtime vs \(r\).
8. **Treewidth scaling:** runtime vs \(w\) for fixed \(n,r\).
9. **Peak states** vs \(r\) grouped by \(w\).
10. **Memory** vs \(r\)/\(w\).
11. Optional: answer bit length vs instance scale.

Use medians plus interquartile ranges over random repetitions.

Do not plot means alone for heavy-tailed runtime.

---

# 42. Required result-table schema

CSV/Parquet fields:

```text
family
instance_id
seed
solver
status              # ok / timeout / oom / wrong
n
m_static
m_temporal
r
treewidth
s
z
count_decimal
count_bits
wall_ms
cpu_ms
peak_rss_mb
states_total
states_peak
join_pairs
answer_sha256
git_commit
compiler
compiler_flags
machine_id
```

For very large counts, keep both decimal count and SHA256 if storage is acceptable. At minimum keep:

```text
count_bits
answer_sha256
```

plus decimal for correctness instances.

---

# 43. Experimental environment

For publication-quality comparison record:

```text
CPU model
physical cores
RAM
OS/kernel
compiler version
compile flags
Python version
Boost version
git commit
```

C++ recommended flags:

```text
-O3 -DNDEBUG -march=native
```

If portability is important, publish a second build without `-march=native`.

Pin CPU affinity if possible.

Warm-up before microbenchmarks.

Use wall-clock monotonic timer.

Run each small instance enough times to exceed 100 ms aggregate timing and divide, so timer noise does not dominate.

---

# 44. External public temporal datasets

These are **not benchmarks from the Enright–Meeks–Molter paper**. Use them only as an external-validity supplement.

## SNAP — email-Eu-core temporal

Official dataset page:

https://snap.stanford.edu/data/email-Eu-core-temporal.html

Published statistics on the page include:

- 986 nodes;
- 332,334 temporal edges;
- 24,929 static edges;
- 803-day span.

Format:

```text
SRC DST UNIXTS
```

The dataset is directed; our current problem/implementation is undirected. If used, explicitly state the preprocessing:

> direction is ignored and parallel same-pair/same-time events are deduplicated.

Do not silently change semantics.

## SNAP — CollegeMsg

Official page:

https://snap.stanford.edu/data/CollegeMsg.html

Published statistics include:

- 1,899 nodes;
- 59,835 temporal edges;
- 20,296 static edges;
- 193-day span.

Also directed; same preprocessing warning applies.

## SocioPatterns

Dataset portal:

https://sociopatterns.org/datasets

Good undirected contact datasets include:

- Hypertext 2009;
- hospital ward contacts;
- primary school temporal network;
- high-school dynamic contact networks;
- workplace contacts.

These typically represent an active undirected contact during a 20-second interval and are more naturally aligned with the undirected temporal-graph model.

Example official pages:

https://sociopatterns.org/datasets/primary-school-temporal-network-data/

https://sociopatterns.org/datasets/high-school-dynamic-contact-networks/

## How to use real data fairly

Most full real-world underlying graphs will have treewidth much larger than 2.

Do **not** claim the series–parallel algorithm solves the full real network if it does not.

Permitted experiments:

1. identify connected components / blocks whose certified treewidth is at most a chosen \(w\);
2. sample vertex-induced subgraphs and certify their treewidth before running;
3. extract naturally occurring low-treewidth components;
4. report coverage:
   - fraction of nodes;
   - fraction of temporal edges;
   - exact treewidth bound used.

Synthetic structured benchmarks remain the main experiment for the theorem.

---

# 45. How to obtain decompositions

For generated partial \(k\)-trees, the generator must emit a valid decomposition. This avoids mixing decomposition-search time with counting time.

For external graphs:

- decomposition computation is a separate preprocessing problem;
- use a recognized exact/heuristic treewidth package if available;
- record whether width is exact or merely an upper bound;
- do not report an approximate width as exact treewidth.

For the core thesis theorem, “given a width-\(w\) decomposition” is sufficient.

---

# 46. Optimization roadmap after correctness

Implement in this order.

## O0 — correctness-first hash-map DP

Canonical state serialization; simple join pair loop.

## O1 — compact status encoding

Pack local status into integers.

Example:

```text
0          ZERO
1..r       IN(t)
r+1..2r    OUT(t)
2r+1       BOTH
```

## O2 — canonical partition encoding

Use restricted-growth-string or small union-find canonical vector.

Hash only canonical form.

## O3 — precompute local join compatibility

Table:

```text
compat[status1][status2] -> merged status / invalid
```

## O4 — join bucketing

Bucket states by coarse compatible signatures to avoid testing every state pair.

## O5 — incidence-cycle test optimized for small bags

Since bag size is \(O(w)\), use tiny union-find. A parallel incidence edge can be detected immediately.

## O6 — sparse maps / state pruning

Do not allocate theoretical state space.

Only reachable states are stored.

## O7 — terminal handling optimization

The proof adds \(s,z\) to every bag, increasing width by at most 2.

A later engineering optimization may keep terminals only where needed, but **do not implement this before the reference version is validated**.

## O8 — specialized TTSP fast path

Detect/use known SP decomposition when available.

---

# 47. Potential TTSP matrix optimizations

Only after the base version is correct:

1. store matrices row-wise as arbitrary-precision integers;
2. skip zero ranges;
3. exploit that base matrices have suffix structure in `a`;
4. test whether transfer matrices preserve exploitable monotonic/triangular structure;
5. blocked multiplication;
6. parallelize top-level independent SP subtrees.

Do not claim \(O(mr^\omega)\) practical improvement without implementing and measuring it.

---

# 48. Formal theorem statements for the thesis

## Theorem A — dense forest improvement

> For a `#Temporal Path` instance whose underlying graph contains a unique static \(s\)-\(z\) path \(P\), the number of non-strict temporal \(s\)-\(z\) paths can be computed in \(O(|P|r)\) arithmetic time and \(O(r)\) working memory after rank compression.

## Theorem B — sparse forest improvement

> Given sorted active-time lists for the edges of the unique static \(s\)-\(z\) path \(P\), the count can be computed in
> \[
> O\!\left(|P|+\sum_{e\in P}|L(e)|\right)
> \]
> arithmetic time.

## Theorem C — TTSP

> Given a two-terminal series–parallel decomposition whose poles are \(s,z\), `#Temporal Path` can be solved in \(O(mr^3)\) arithmetic time using temporal transfer matrices.

## Theorem D — bounded treewidth

> Given a width-\(w\) tree decomposition of the underlying graph, non-strict `#Temporal Path` can be solved in
> \[
> N\,r^{O(w)}2^{O(w\log w)}
> \]
> arithmetic time; therefore it belongs to XP parameterized by underlying treewidth.

## Corollary — series–parallel

> `#Temporal Path` is polynomial-time solvable when the underlying graph is series–parallel / has treewidth at most 2.

---

# 49. Claims that must NOT be made prematurely

Do not write any of these without further work:

- “The result has been peer reviewed.”  
  It has not.
- “This is definitely the first solution in the literature.”  
  Current searches did not locate a follow-up, but a systematic novelty review and external check are still required.
- “We beat the paper's implementation.”  
  No author implementation/benchmark was located.
- “The treewidth algorithm is FPT in treewidth.”  
  It is XP in \(w\), not FPT.
- “The general #Temporal Path problem is polynomial.”  
  False.
- “All real temporal networks are covered.”  
  False.
- “Series–parallel runtime is practically \(O(NT^{10})\).”  
  \(T^{10}\) is only a crude proof bound from naive states/joins.
- “Strict temporal paths are already covered.”  
  The current proof is written for non-strict paths. A strict variant likely changes local comparisons to `<`, but it must be stated and audited separately.

---

# 50. Novelty/literature audit status

Searches performed up to **2026-09-28** included variants of:

```text
"Counting Temporal Paths" series-parallel
"#Temporal Path" series-parallel
"temporal path" "bounded treewidth" counting
"Counting Temporal Paths" 2026
paper title + GitHub / code / benchmark / artifact
```

The searches surfaced the original 2025 Algorithmica paper, the 2023 STACS version, and related temporal-graph work, but did not surface a later paper clearly resolving the same series–parallel conjecture or giving the same treewidth-XP theorem.

This is promising but **not sufficient for a final publication novelty statement**.

Before thesis submission:

1. search DBLP;
2. Google Scholar “cited by” the Algorithmica and STACS papers;
3. Semantic Scholar;
4. Scopus/Web of Science if institution access exists;
5. arXiv by keywords;
6. author publication pages;
7. ideally send the theorem/proof to the supervisor or an external temporal-graphs researcher for review.

---

# 51. Comparison table to include in thesis

Use a table conceptually like:

| Setting | Original paper | This work |
|---|---|---|
| Forest | \(O(|V|T^2)\) | \(O(|P|r)\), sparse \(O(|P|+\sum |L(e)|)\) |
| TTSP, poles = query | Open as part of SP conjecture | \(O(mr^3)\) transfer DP |
| Treewidth \(w\)+lifetime \(T\) | FPT via MSO/Courcelle | explicit DP also works |
| Treewidth \(w\) alone | no FPT expected | XP: \(N r^{O(w)}2^{O(w\log w)}\) |
| Series–parallel | explicitly conjectured polynomial | polynomial as \(w\le2\) corollary |

Be careful:

- the original paper does **not** claim there is no XP algorithm;
- our result complements, rather than contradicts, their hardness theorem.

---

# 52. Experiment hypotheses

Pre-register these before running final benchmarks.

## H1 — dense forest scaling

Paper baseline empirical runtime grows approximately quadratically in \(r\); dense-prefix grows approximately linearly.

## H2 — sparse advantage

At fixed large \(r\), sparse runtime is primarily explained by:

\[
\sum |L(e)|
\]

rather than \(Lr\).

## H3 — exponential route compression

On diamond chains, `ttsp_transfer` remains polynomial while brute force becomes impossible as \(2^k\) static paths grow.

## H4 — arbitrary-query SP tractability

`tw_dp` handles arbitrary \(s,z\) on partial 2-trees and agrees with brute force on all small cases.

## H5 — XP signature

Holding \(n,r\) roughly fixed, runtime/state count rises rapidly with \(w\), consistent with \(r^{O(w)}2^{O(w\log w)}\).

If data contradict a hypothesis, report it.

---

# 53. Timeout policy

Recommended final benchmark:

```text
timeout = 300 s
memory  = 16 GiB or machine-appropriate fixed cap
```

For microbenchmarks/paper forest comparison:

```text
timeout = 60 s
```

Always report censored/time-out instances.

Never drop difficult instances from averages without stating it.

---

# 54. Statistical reporting

For each randomized grid cell:

```text
replicates = 10
```

or 20 when cheap.

Report:

- median;
- IQR;
- min/max optionally;
- number solved;
- number timed out;
- peak memory median/IQR.

For speedups, compare paired instances.

Use geometric mean of positive speedup ratios as an optional aggregate, but always retain per-family medians.

---

# 55. Reproducing the original paper's forest baseline exactly

The final paper-comparison script should produce a table:

| \(L\) | \(r\) | \(|\mathcal E|\) | paper recurrence ms | dense prefix ms | sparse ms | speedup dense | speedup sparse | counts equal |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|

The paper recurrence must be based on:

\[
F(v_i,t)=
\sum_{\substack{t'\le t\\(e_i,t')\in\mathcal E}}
F(v_{i-1},t').
\]

Do not substitute the optimized prefix version into the “paper” column.

---

# 56. Ablation study for `tw_dp`

Required versions:

```text
TW0: correctness-first hash map + naive join
TW1: packed statuses
TW2: canonical compact partitions
TW3: precomputed local compatibility
TW4: join bucketing/indexing
```

Table:

| Variant | Correct? | Runtime | Peak RSS | States | Join pairs |
|---|---:|---:|---:|---:|---:|

Use the same benchmark instances.

This turns implementation engineering into a defensible algorithmic contribution rather than undocumented optimization.

---

# 57. Proof-audit checklist before freezing the thesis theorem

A human/independent agent should verify each point separately.

- [ ] Temporal-path definition matches the 2025 paper exactly.
- [ ] Non-strict comparison is `<=`, not `<`.
- [ ] Each static edge is introduced exactly once.
- [ ] Selecting a static edge chooses at most one timestamp.
- [ ] Degree constraints prevent branching.
- [ ] Introduce-edge cycle test is correct.
- [ ] Forgotten used nonterminals must be `BOTH`.
- [ ] No component can disappear from the separator.
- [ ] Join incidence multigraph lemma is correct, including parallel edges.
- [ ] New connectivity partition is correct after join.
- [ ] Root condition excludes extra components.
- [ ] Every accepted graph is exactly one path, not a disjoint union.
- [ ] Orientation necessarily runs from \(s\) to \(z\).
- [ ] Local time inequalities imply global nondecreasing times.
- [ ] Completeness uses the tree-decomposition connectedness property correctly.
- [ ] Each temporal path is counted exactly once.
- [ ] State-count bound includes partitions.
- [ ] Big-integer bit complexity is polynomial for fixed \(w\).
- [ ] Series–parallel terminology is aligned with the thesis definition.
- [ ] Novelty claim has been separately literature-checked.

---

# 58. Failure protocol

If the implementation finds a discrepancy:

1. save the instance immediately;
2. save:
   - graph;
   - temporal labels;
   - \(s,z\);
   - decomposition;
   - solver outputs;
   - seed;
3. run both brute-force references;
4. delta-debug:
   - remove unused vertices;
   - remove static edges;
   - remove time labels;
   - reduce time ranks;
5. minimize to the smallest counterexample;
6. identify whether the problem is:
   - implementation bug;
   - decomposition bug;
   - proof/state insufficiency;
   - ambiguous problem definition.

Do not continue performance experiments until correctness is restored.

---

# 59. Suggested milestone order for the coding agent

## Milestone 1 — parser + reference

Deliver:

- parser;
- rank compression;
- brute force;
- manual unit tests.

## Milestone 2 — forest

Deliver:

- paper baseline;
- dense-prefix;
- sparse;
- path closed-form tests;
- preliminary scaling plot.

## Milestone 3 — TTSP

Deliver:

- SP expression/decomposition;
- transfer matrices;
- random TTSP generator;
- diamond closed-form tests;
- brute force agreement.

## Milestone 4 — tree decomposition core

Deliver:

- generated partial \(k\)-tree decomposition;
- nice-decomposition conversion;
- state encoding;
- introduce/forget.

## Milestone 5 — join

Deliver:

- incidence-cycle test;
- focused join tests;
- complete `tw_dp`.

## Milestone 6 — exhaustive audit

Deliver:

- Graph Atlas tests;
- exhaustive \(r=2\) temporal labeling tests;
- zero mismatch report.

## Milestone 7 — optimization

Deliver:

- packed states;
- join indexing;
- ablation.

## Milestone 8 — full benchmark

Deliver all F/S/P2/W families and result CSVs.

## Milestone 9 — external data

Optional, only after theorem benchmark is stable.

---

# 60. Acceptance criteria for the final repository

The repository is ready for thesis experiments only if:

1. all manual tests pass;
2. forest algorithms agree;
3. TTSP agrees with brute force on at least 2,500 seeded small cases;
4. `tw_dp` agrees with brute force on all exhaustive small cases;
5. zero known unresolved mismatch;
6. every benchmark can be reproduced from one command;
7. results contain git commit + environment metadata;
8. all generators are deterministic;
9. paper baseline is clearly separated from our algorithms;
10. README states that the original paper supplies no official benchmark archive.

---

# 61. Suggested one-command reproducibility

Target:

```bash
python python/benchmark.py --suite correctness
python python/benchmark.py --suite forest
python python/benchmark.py --suite ttsp
python python/benchmark.py --suite partial2tree
python python/benchmark.py --suite width
python python/aggregate.py results/
python python/plots.py results/
```

And ideally:

```bash
make reproduce
```

to produce all thesis tables/plots that fit within a documented compute budget.

---

# 62. Thesis narrative

A clean chapter progression is:

1. `#Temporal Path` and original paper.
2. Faster evaluation on forests:
   \[
   O(nT^2)\to O(nT)\to O(|\mathcal E_P|).
   \]
3. Temporal transfer algebra for TTSP.
4. Locality of temporal constraints.
5. Explicit bounded-treewidth connectivity DP.
6. XP theorem.
7. Series–parallel corollary resolving the conjecture.
8. Exhaustive correctness audit.
9. Experimental evaluation.
10. Limitations and future work:
    - tighter SP runtime;
    - join optimization;
    - strict temporal paths;
    - other path notions;
    - practical low-treewidth temporal networks.

---

# 63. Recommended wording of the main contribution

Safe wording before peer review:

> We give an explicit dynamic program for counting non-strict temporal paths on graphs of bounded underlying treewidth. Given a width-\(w\) tree decomposition, the algorithm runs in \(N\,T^{O(w)}2^{O(w\log w)}\) arithmetic time, placing #Temporal Path in XP parameterized by underlying treewidth. As a consequence, the problem is polynomial-time solvable on series–parallel graphs, resolving the series–parallel conjecture posed by Enright, Meeks, and Molter, subject to independent verification of the proof and novelty claim.

For the final thesis after supervisor audit, the final qualification can be removed if approved.

---

# 64. Source list

## Original research paper

Jessica Enright, Kitty Meeks, Hendrik Molter.  
**Counting Temporal Paths.**  
Algorithmica 87, 736–782 (2025).  
DOI: https://doi.org/10.1007/s00453-025-01301-3  
Springer: https://link.springer.com/article/10.1007/s00453-025-01301-3  
Glasgow repository: https://eprints.gla.ac.uk/348161/

## Earlier version

Jessica Enright, Kitty Meeks, Hendrik Molter.  
**Counting Temporal Paths.** STACS 2023.  
https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.STACS.2023.30

## Public temporal datasets for optional external validation

SNAP email-Eu-core temporal:  
https://snap.stanford.edu/data/email-Eu-core-temporal.html

SNAP CollegeMsg:  
https://snap.stanford.edu/data/CollegeMsg.html

SocioPatterns dataset portal:  
https://sociopatterns.org/datasets

SocioPatterns primary school:  
https://sociopatterns.org/datasets/primary-school-temporal-network-data/

SocioPatterns high school:  
https://sociopatterns.org/datasets/high-school-dynamic-contact-networks/

---

# 65. Final status

### Strong / implementation-ready

- Time-rank compression.
- Paper forest baseline.
- \(O(|P|r)\) forest DP.
- Sparse forest DP.
- TTSP transfer-matrix algorithm.
- Closed-form path and diamond-chain oracles.

### Theorem-level proof completed internally, pending independent review

\[
\boxed{\#TemporalPath\in XP(tw)}
\]

via explicit tree-decomposition DP.

### Immediate corollary

\[
\boxed{\#TemporalPath\in P\text{ on series–parallel graphs}.}
\]

### Benchmark status

The original paper provides **no official benchmark dataset or implementation**. The final project must therefore use the paper-faithful benchmark protocol defined above and compare directly against the paper's Theorem-2 recurrence on forests, while treating the series–parallel result as an exact solution to an open case rather than a runtime competition against nonexistent author code.

---

# 66. Agent's first action

Before optimizing anything:

1. implement B0 brute force;
2. implement `forest_paper`, `forest_dense_prefix`, `forest_sparse`;
3. reproduce all manual path formulas;
4. implement TTSP transfer and diamond formulas;
5. implement the correctness-first treewidth DP;
6. rerun the entire exhaustive audit from zero;
7. only after **zero mismatches** begin performance optimization.

**Correctness is the release gate.**
