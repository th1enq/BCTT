# Figures, Tables, and Equations

A third of a typical natural-science article is graphics. A single great
figure (the Bergen cyclone model) can carry a theory into textbooks. But 50
cheap computer-generated figures ≠ 50,000 words — each figure must earn its
place.

## From working figure to publication figure

The software-default plot that produced your "Eureka!" is a *working
figure*. Publication figures are rebuilt — often stripped to the data and
redrawn, through several iterations (half a day per figure is normal).
Five checks, in order:

### 1. Design
- Choose the right graphic type for the data (see below).
- Square plots when both axes share units and range.
- Line graphs: choose the aspect ratio so slopes bank to ~45° — maximizes
  slope perception (Cleveland).
- Combine same-design figures into multipanel figures; order panels like
  reading a book; label (a), (b), (c) inside the panel area (saves space).

### 2. Size
- Design at final journal size (e.g., single column ~7.9 cm, double ~16.5
  cm). Fonts ≥ 8 pt after reduction; dotted lines often vanish when shrunk.
- Sans serif fonts (Arial, Helvetica) survive rescaling, photocopying, and
  distance viewing better than serif.
- Print at publication size as a final check.

### 3. Aesthetics — take control back from the software
- Data must dominate: line-width ratio grid : axes : data = 1 : √2 : 2 (or
  1:2:4); data black, grid gray; most default gridlines should die. Avoid
  Tufte's *chartjunk* (decoration, moiré, 3D effects on bars/pies).
- Minimize empty space: axis range fits the data (a scatter of 31–34 doesn't
  need to start at 0).
- Axis titles accurate, concise, with units, avoiding bare symbols:
  "2-m air temperature (°C)" beats "T". Consistent capitalization style.
- Moderate, physically meaningful tick marks (3-hourly ticks on 24-h data;
  no sub-year ticks on annual data; never auto-intervals like 1.292°C).
- Standard units; exponent labels as "10⁻⁵ m" (never "m × 10⁵" — ambiguous);
  log axes labeled 10⁴, 10⁵, not 4, 5.
- Unambiguous dates (10/12/04 could be two dates).

### 4. Consistency
- Text–figure inconsistency is among the errors reviewers hate most. Check
  variable names, symbols, units, terminology across text and all figures.
- Same-family figures share size, axis ranges, line types, contour
  intervals, symbols.
- Follow journal style: scalars italic, vectors bold; m s⁻¹ not m/s; no
  Comic Sans.

### 5. Annotation — make the figure self-contained
The reader should understand the figure without hunting through the caption;
self-contained figures also survive being lifted into talks and textbooks.
Add: direct line labels (better than a legend), length scales, reference
lines (0°C, the 1:1 line), geographic names mentioned in the text, insets
for detail, error bars/confidence intervals, panel letters, arrows/circles
marking features the text discusses. Never let annotation overprint data;
place it close to its target.

## Grayscale and color

- Color is for clarity and emphasis, never decoration. Many readers print in
  black and white — design with that in mind.
- Continuous color scales for continuous imagery; **discrete scales when
  readers need to extract numbers** (≤ ~5 gray levels, ≥20% apart).
- Avoid rainbow scales (false gradients at yellow–green). Anomalies: light
  red→dark red positive, light blue→dark blue negative.
- Warm colors pop forward, cool colors recede; warm overprints cool at
  crossings.
- ~10% of men are red–green colorblind: check figures with a colorblindness
  simulator; beware red/green encodings.
- Projectors/printers shift colors (yellows and light greens vanish on
  white); verify at page proofs.

## Common figure types — key points

- **Line graphs:** mark actual data points so readers see what's
  interpolated; distinguish multiple lines by type/width/color; twin axes
  can merge related plots.
- **Scatterplots:** control symbol size (visible but minimal overlap);
  closed round symbols usually best; open symbols where data overlap
  heavily; equal-area symbols for multiple classes (a "+" visually outweighs
  a "−"); add 1:1 or regression lines, defined in the caption.
- **Linear regression:** first ask whether the relationship should even be
  linear; beware outliers (Anscombe's quartet: four datasets, same mean, SD,
  regression line, and r — only one suits linear regression); report fits
  with and without outliers; r ≠ r²; correlation ≠ causation; reserve the
  word "correlation" for computed coefficients.
- **Bar charts:** for countable/categorical data; **order the bars to make
  the point** (descending usually beats alphabetical); horizontal bars for
  long labels or time/distance; stacked bars for subsets (put small or
  fast-changing categories where visible); bars wider than gaps; label
  boundary ambiguity in the caption ("bar '2' = 2.0–2.9 cm"); "frequency"
  only for events per unit time; trends read better on line graphs.
- **Box-and-whisker:** compare distributions; always define the convention
  (quartiles, whiskers, outliers) in caption or inset; overlapping boxes =
  statistically indistinguishable.
- **Maps/cross sections:** balance data density vs domain; annotate
  place-names used in the text; include a length scale; show section
  endpoints on a companion map.
- **Pie charts:** generally avoid (bars/tables carry numbers better);
  exception: many small pies across a map.
- **Small multiples:** repeated mini-panels reveal evolution and patterns.
- **Instrument figures:** line drawings beat cluttered lab photos; a paid
  graphic artist is usually worth it.
- **Schematics/conceptual models:** the paper's synthesis; may be reproduced
  in textbooks — accurate, artistic, not overgeneralized.
- **Photos:** crop hard; before/after pairs are powerful; overlay
  quantitative grids where possible.

## Figures from other sources

Get the original digital file if possible; obtain copyright permission;
caption: "From Jones (1995, her Fig. 5)", "Adapted from…" if altered, full
disclosure if redrawn with changes, "Courtesy of…" for unpublished gifts.

## Tables

Prefer figures; never show the same data in both. Tables win for: precise
values, alphanumeric listings, data too big for figures, organized summaries
of scattered points. Reconsider tables of negative/undiscussed results.

Design: several small focused tables > one monster; numbers read best in
columns; order rows/columns meaningfully (explain in caption); open layout
(minimal rules); every column has a concise parallel heading with units;
align decimals; leading zeros (0.23); highlight what matters (bold/asterisk
for significance); letter footnotes (numbers look like exponents); define
abbreviations.

## Captions

The text discusses results; **the caption teaches how to read the figure.**
Begin with a phrase capturing the essence, unique among captions. Be
complete — every element, every panel, even the self-evident. Then make it
clear, then concise. Don't write captions when exhausted at the end;
standardize formats across similar figures; cross-check caption ↔ figure ↔
text.

## Discussing figures in the text

- A well-constructed figure does NOT speak for itself — walk readers through
  it. State the obvious feature first (indulge the reader), then the fine
  points and anomalies.
- Match text depth to figure complexity (complex flowchart: paragraphs;
  simple line graph: one sentence). Don't waste text explaining how to read
  the figure — that's the caption's job.
- **Never oversimplify comparisons.** "Modeled and observed precipitation
  show remarkable similarity" is naive or dishonest; describe agreements AND
  disagreements, then argue why the simulation still serves the purpose.
- Direct citation ("Figure 2 shows…") for complex figures needing a
  paragraph; indirect "(Fig. 2)" at the end of a science-first sentence for
  the rest — most authors favor indirect. Citation placement implies what
  the figure contains, so move it mid-sentence when needed for accuracy.
  Tables are inanimate: not "Table 6 demonstrates".
- Number figures in order of first mention; cite every panel (else delete
  it); cite figures liberally when discussing results (readers never
  complain about too many pointers); verify every figure number before
  submission.

## Equations

- A paper cannot stand on equations; avoid "it can be shown that" with
  missing steps. Accompany each equation with physical interpretation
  (term-by-term notes, typical values, scale analysis) and explicit
  assumptions.
- Typeset as part of the sentence (punctuation after); don't open a sentence
  with a symbol; scalars italic, vectors bold, operators roman.
- Define every variable at first use — "c represents phase speed" (never
  "c = phase speed"); use standard symbols; a symbol table if many.
- Number sequentially; refer with names: "the continuity equation (3.1)".
