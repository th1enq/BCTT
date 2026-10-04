# Research contributions and comparison scope

Let n,m,M be vertices, static edges and temporal edges; r is the number of
distinct compressed times; w is underlying treewidth; N is nice-TD node count.

| Result | Earlier bound or baseline | Current bound and condition |
|---|---|---|
| Forest count | Paper O(nT²); literal compressed baseline O(|P|r²) | Dense O(|P|r) or sparse O(|P|+M_P) arithmetic after the path/sorted labels are supplied |
| TTSP pole query | Internal matrix O(mr³), O(mr²) integer cells | Event core O(n+m+M+r), exactly M additions; valid pole orientation and compressed times supplied |
| Cactus arbitrary endpoints | No dedicated baseline claimed from authors | Tarjan block route plus events O(n+m+M+r) after compression |
| Width-w arbitrary endpoints | Internal baseline state ranks exponent w+3 | Terminal quotient exponent w+1; time N(r+1)^(2w+2)2^O(w log w) |
| Arbitrary-terminal series–parallel | Conjecture in paper Section 6 | Width-two specialization O(N(r+1)^6) arithmetic |
| Strict temporal paths on these classes | Previously unimplemented here | Same proofs with strict local comparisons and reversed event-tie order |

Input parsing/compression, exact-count bit costs, and structural validation are
not omitted. Current TG parsing is O(M log M); TTSP validation uses expected
O(m log m) small-to-large hash merging and is included in measured solver time.
The forest C++ map lookups and structural validation add preprocessing costs.
With maximum intermediate count bit length B, event counting has O(B) additions
and copies; the safe treewidth bound uses O(B²) schoolbook multiplication.

The baseline from the paper is an independent reimplementation of its forest
recurrence. Matrix and original treewidth comparisons are internal ablations.
There is no measured comparison against an author MSO implementation.

Evidence is retained in `results/research_audit_summary.json`, the two final raw
benchmark CSVs, summary CSV, seven standalone vector figures and generated
LaTeX tables. Historic smoke measurements and the first 160-cell experiment
are retained but excluded from final aggregation. Exact ratios are read from
`results/research_highlights.json`, not recorded as timeless algorithm facts.

Theorems are proposed, fully written internal results. Mathematical validity
and worldwide novelty are separate questions. Independent proof/novelty review,
full n=5,r=2 exhaustive testing and real-world temporal data are remaining
extensions, not silently marked complete.
