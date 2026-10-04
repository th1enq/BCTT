# Literature review log — 2026-10-04

Primary sources read during the upgrade:

| Source | Relevance |
|---|---|
| Enright, Meeks, Molter, [Counting Temporal Paths, Algorithmica 2025](https://link.springer.com/article/10.1007/s00453-025-01301-3) | Forest recurrence; combined treewidth/lifetime FPT; Section 6 conjectures extension to series–parallel. Non-strict model is the main comparison. |
| [STACS 2023 version](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.STACS.2023.30) | Earlier version of the same paper, not a separate new baseline. |
| Döring et al., [FO and MSO Model Checking on Temporal Graphs, SAND 2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol373-sand2026/html/LIPIcs.SAND.2026.9/LIPIcs.SAND.2026.9.html) | Broader logical encodings and tractability parameters; useful context, not evidence of our first-publication claim. |
| Enright et al., [Families of Tractable Problems with Respect to Vertex-Interval-Membership Width and Its Generalisations, SAND 2026](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAND.2026.4) | Different temporal membership-width parameters and a general DP framework. |
| Tang et al., [Efficient Temporal Simple Path Graph Generation, arXiv:2507.10017](https://arxiv.org/abs/2507.10017) | Generates a union of temporal simple paths; distinguish that output from counting all time-labelled paths. |

Queries included:

- `"counting temporal paths" "treewidth" "series"`
- `"temporal paths" counting series parallel polynomial 2025 2026`
- `"temporal" "series-parallel" counting algorithm paths`
- `"counting temporal paths" "bounded treewidth" XP`
- `"counting temporal paths" "cactus"`
- `"temporal paths" "acyclic" "counting"`
- `"counting temporal paths" "XP"`

The inspected results did not identify a paper giving this exact explicit XP
algorithm/terminal quotient or settling the same arbitrary-terminal conjecture.
This is a limited search outcome, not proof that no such paper exists. Citation
indexes, unpublished work, alternative terminology, and full related-paper
proofs can reveal overlaps. Independent novelty review remains necessary for
an international priority claim.

Topological DP, prefix sums, Tarjan blocks, small-to-large merging, partition DP,
and degree indexing are standard techniques. Contributions should be framed as
their explicit application and proofs for this counting problem, the sharper
terminal state quotient, extension to strict/cactus cases, and reproducible
validation—not invention of those standard techniques.

No collaborator/referee has been contacted or represented as approving the
proof. Publication status and a university grade are not inferred from audits.
