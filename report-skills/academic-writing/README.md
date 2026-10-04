# academic-writing

A Claude Code skill for Academic Writing. The principles apply to English academic writing in
every discipline.

## Scope

- **Paper structure**: choosing a question and target journal; titles;
  abstracts; introductions (context → conflict → response); literature
  synthesis; data and methods; results; discussion; conclusions;
  acknowledgments; appendices; plus motivation, outlining, and first-draft
  strategies
- **Prose craft**: paragraphs (unity + coherence, topic/stress positions,
  three coherence devices), sentences (active voice, strong verbs,
  subject–verb distance, tense, parallel structure, comparisons, negatives,
  misplaced modifiers), and words (concision, precision, bias-free writing)
- **Figures, tables, equations**: the five checks from working figure to
  publication figure, grayscale and color, per-chart-type advice, table
  design, captions, discussing figures in the text, typesetting equations
- **Revision and submission**: the writing/editing funnel + CPR, précis,
  final-check lists, citation and reference rules, page proofs, marketing a
  published paper
- **Peer review**: writing referee reports (critical-reading template,
  feedback sandwich), responding to reviewers point by point, handling
  rejection, ICMJE authorship criteria, ethics and misconduct, ESL author
  strategies
- **Presentations**: conference abstracts, storyboarding, headline-style
  slide titles, "one point per five minutes", dive-and-surface for diverse
  audiences, delivery and Q&A, the one-minute-synopsis poster method, media
  interviews
- **Quick lookup**: redundant pairs, wordy → lean replacements, weak nouns,
  empty modifiers, commonly misused terms, comma/hyphen/en-dash/em-dash
  rules

## Layout

```
academic-writing/
├── SKILL.md                        # Entry point: creed, editing funnel, ten principles, task routing table
└── references/
    ├── structure.md                # Paper structure, section by section
    ├── style.md                    # Paragraphs, sentences, words (the core craft)
    ├── figures-tables.md           # Figures, tables, equations, captions
    ├── revision-submission.md      # Revision workflow, citations, checklists, proofs
    ├── peer-review.md              # Reviewing, responding, authorship, ethics, ESL
    ├── presentations.md            # Abstracts, slides, talks, posters, Q&A, media
    └── word-usage.md               # Word-level lookup tables and punctuation
```

Progressive disclosure: SKILL.md stays in context and routes each task type
to the relevant reference file, so Claude loads only what the task needs.

## Triggering

The skill activates automatically for tasks such as:

- Writing, revising, or polishing a journal manuscript, thesis, conference
  abstract, or extended abstract ("tighten my paper", "make this more
  academic", 修改论文, 润色)
- Submission work: journal selection, cover letters, pre-submission checks,
  page proofs
- Peer review: writing referee reports, responding to reviewers, handling
  rejection
- Presentations: slides, posters, talk preparation, Q&A

You can also invoke it explicitly: "use the academic-writing skill".

## Creed

> **We write for our audience, not for ourselves.**
> "Do not write so that you can be understood;
> write so that you cannot be misunderstood." — Epictetus

Always edit top-down (organization → paragraphs → sentences → words), and at
each level apply CPR: Concision → Precision → Revision.
