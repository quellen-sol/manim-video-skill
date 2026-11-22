# Review log: Git, visually (container-route test, job 03-git-workflows)

Scene: `scene.py`, class `Explainer`. Narration: silent (skill default; unattended run, nobody
to ask). Audience: newcomer (knows files and saving), intuitive depth, 16:9 1920x1080 at 60 fps.

## Change of plan (owner, mid-run)

Previews 1 and 2 rendered my own 121 s scene (kept in `_discarded/`). The owner then asked to
start from `examples/03-git-workflows/` (scene.py and storyboard.md copied in), keep its content
and length (earlier final 139.0 s), fix its two known limitations (the commit id scrambled
during each rebase hop; HEAD crossing the `c48 -> 7d2` arrow in chapter 4), and reach a rubric of
at least 18/20 with at most 3 final renders. Preview numbering below continues from 3.

Findings on my own scene before the switch (preview 1; for the record): file-to-commit morph
went through a garbled blob; chapter 1 left-heavy; file-panel words misaligned; chapter 6 box
labels tight at 1080p. Its preview 2 was never reviewed (superseded).

## Preview 3 (adopted scene, first container render)

Fixes applied before rendering (from the known limitations and from reading the scene against
the current SKILL.md):

- Rebase: `TransformFromCopy(f1, f1r)` morphed "e5b" into "2be" mid-flight (scrambled glyphs).
  Now copies carrying the old ids hop together along the same arc (same offset, so they never
  cross); the ids swap with a sequential fade when the caption says "new ids".
- `git switch main` in chapter 4: the old glide crossed the long `c48 -> 7d2` arrow. After the
  rebase the graph is one connected barrier (main lane + `c48 <- 2be <- 6d7`), so no route
  between commits avoids an arrow; HEAD now goes around the right end of the graph
  (`route_around_right`, built from the tags' real sizes), and the copies land 0.3 units further
  left so that detour stays inside the frame. `check_route` prints a `ROUTE-CHECK` line to
  render.log.
- `Indicate` on the parent arrow (chapter 1) and `Circumscribe` on the `main` tag (chapter 2)
  are on the style guide's avoid list: replaced by a yellow `ShowPassingFlash` along the arrow
  and a `SurroundingRectangle` that is created and faded.

Result: `out/Explainer-preview.mp4`, 139.00 s, 854x480 @ 15 fps. report.md: PASS (stream PASS,
blank PASS 1.1 s, holds PASS 38 % across 46 holds, cuts PASS). LayoutGuard active, no LAYOUT
lines. Timings: render 120.3 s, checks 11.4 s, stills 101.3 s. Stills looked at: all 17 sheets;
`--frames --at 58.1..59.2` (8 frames of the HEAD route); full-size `--still 86` (conflict
strategies) and `--still 113` (pull-request pipeline).

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 2-3 / 6.1 s, 10.5 s, 16.9 s (mid frames) | `FadeTransform(card, commit)` stretches the id ("a1f", "3c9", "7d2") to card size on top of "app.py": two texts superimposed mid-transition (not in the earlier run's notes) | a text-free copy of the card (box + lines) shrinks into the commit slot, then the commit fades in |
| 9 / 58.6 s (mid route) | HEAD passes 0.18 units from the `feature` tag's right edge (ROUTE-CHECK: hit at the 0.05 margin) | route margin 0.15 to 0.25 and a flatter start; copies 0.15 further left (3.15, 4.65) so the wider swing stays well inside the frame; hop arc -0.55 pi (keeps 0.12+ clear of `9a0` and `c48` with the new chord) |
| 13 / 92 s (1080p still) | the check mark after "keeps both" touches the green frame's right edge | the frame surrounds the row and the check |
| 12 / 79 s (mid frame) | the two code cards slide over each other while merging into the conflict file | kept: it is the merge metaphor (texts stay on different rows); noted |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: a commit is a saved snapshot that points back to the one before; a branch
(and HEAD, "where I am") is just a label, so work can split off and main can move on meanwhile.
Merging joins the lines with a commit that has two parents; rebasing copies my commits on top
of main (new ids), so main can simply slide forward and history is one line, but shared commits
must not be rebased. When both sides change the same line Git stops and a person keeps one side
or combines them; at work main is locked and changes arrive through a pull request that passes
tests and review, landing as a merge commit, a squash or a rebase.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | a file card that is saved as snapshots |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 1 | "careful: in a rebase, ours and theirs swap" is a caption-only claim with no picture; everything else is shown |
| Picture before formula | 2 | each command chip appears with the picture it causes |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | blue main / orange feature / white HEAD / yellow focus / red conflict / green resolved |
| Minimal, legible on-screen text | 2 | one caption at a time; chip + caption; 1080p stills legible |
| Pacing (holds after reveals, not dragging) | 2 | 139 s, holds 1-2.5 s |
| Payoff and recap | 2 | five-line recap |
| Matches the learning goal and requested depth | 2 | includes the enterprise part (protected main, PR, CI, review, merge policy) |
| **Total** | 19/20 | above the owner's bar of 18 |

## Preview 4

139.00 s; report PASS (stream, blank 1.1 s, holds 38 %/46, cuts); no LAYOUT lines; ROUTE-CHECK
clear. Timings: render 145.7 s, checks 14.0 s, stills 102.5 s. Looked at: sheets 1 (snapshot) and
8 (rebase + HEAD route), and the changed beats in the others.

| Beat / time | Bug | Fix |
|---|---|---|
| 2 / 6.9 s (mid) | snapshot: the shrunken page's lines show through the id while it fades in | crossfade made sequential (page out, then commit in) |
| 9 / 59 s (mid) | HEAD's detour around the graph reaches x = 6.64 (3 % from the frame edge): inside the new 6-8 % margin required by the owner's geometry gate | `git switch main` becomes a hop (fade out downwards, fade in from above main); with the graph one connected barrier, no glide can avoid both arrows and margins |

Owner's message mid-iteration: geometry joins the acceptance gate (margins of 6-8 %, centred
figures, symmetric layouts, nothing touching the edge). Audit by reading the layout code:
title/command chip at 4.9 % side margin (`to_corner(buff=0.7)`); chapter 5 options layout
about 5 %; chapter 6 pipeline 7.1 %; merge-policy graphs 0.15-0.5 off their column titles;
protected-main picture 0.3 off-centre; graph slots 0.15 left of centre.

## Preview 5 (first with GeometryGuard)

Rules declared (25): title/chip/caption/card/graph within 7 %; titlecard centred in the frame;
the two-lane graph after the rebase (`forked`) and the straightened line (`history`)
symmetric about x = 0; main and HEAD tags centred over the merge commit; merge id concentric with
its ring; conflict-cause cards, conflict + options pair, protected-main picture, pipeline,
policy row and recap symmetric about x = 0 (and within 7 %); each policy graph centred under its
title. Rules are scoped by re-binding names (an empty group is never measured).

Layout changes before it: EDGE buff (1.15, 0.65) for title and chip (8.1 %); graph slots +0.15
(final line -5.25..5.25); copies at 3.3 / 4.8; main's and feature's code cards share one width;
ours/theirs labels stacked (narrower) and the file + options pair centred from measured widths;
pipeline boxes 2.45 wide; protected-main x positions computed from the feature tag's width;
policy graphs centred under titles.

Result: 138.86 s; report **FAIL** (exit 1) on geometry only, 4 violations:

| Rule | Measured | Cause | Fix |
|---|---|---|---|
| centered_in(titlecard, frame) | 0.38 up (anim 0) | measured while only the title line was up | track it once both lines are up |
| symmetric(options) | 5.93 left, 0.21 right | `.animate` on the conflict group added it to the scene as a whole, so the checker took that member and skipped the nested `rows` group | track a flat group (file, each row, check, frame) |
| symmetric(policies) | 6.13 left, 5.90 right | outer columns differ in width (merge graph + "keeps the real history") | outer columns placed at the same reach (8 % margins), middle on the centre; per-column rules declared with the computed centres |
| within_margin(policies, 7 %) | left 6.9 % | same | same |

Measured and passing: graph margins (right 7.3 %), forked -5.63..5.62, history ±5.63, cards
±5.615, protected ±2.90, pipeline ±5.80, recap ±4.84, merge tags centred on the merge commit.
Stills looked at: sheets 8 (HEAD hop: clean), 9 (straight line centred), 12 (centred options
pair), 13 (protected main).

Wrapper note: with exit 1 the wrapper printed no VIDEO/SHEET/REPORT/LOG lines (see FEEDBACK).

## Preview 6 (last allowed by the cap: 2 on the discarded scene + 4 on the adopted one)

138.86 s; report **PASS**: stream, blank 1.1 s, holds 38 %/46, cuts, and **geometry PASS: all 25
rules and the frame-edge rule hold over 136 animations, none UNCHECKED**. No LAYOUT lines.
Timings: render 122.6 s, checks 10.8 s, stills 76.2 s. Measured: options -5.93..5.93,
policies -5.96..5.96 (8.2 % margins), forked -5.63..5.62, history ±5.63, protected ±2.90,
pipeline ±5.80, cards ±5.62, graph right margin 7.3 %, title/chip 8.1 %, caption 7.5 %.

Looked at: sheet 16 (policy row), `--frames --count 16` overview of the whole video, full-size
1080p `--still 60` (rebase state with ghosts), `--still 89` (conflict + options pair),
`--still 130` (policy row). No new bugs.

Accepted and noted (not bugs): the two code cards slide over each other for about half a second
while merging into the conflicted file (the merge metaphor; their texts stay on separate rows);
`git switch main` in chapter 4 is a fade hop rather than a glide (the only way to cross nothing
and keep the margins).

### Intuitiveness (final scoring)

Same newcomer summary as preview 3. Scores: concrete anchor 2, one idea per beat 2, every step
motivated **1** ("careful: in a rebase, ours and theirs swap" is stated in a caption without a
picture), picture before formula 2, progressive reveal 2, colour 2, text 2, pacing 2, recap 2,
depth 2. **Total 19/20** (owner's bar 18; geometry PASS, so no cap).

## Final (1 of at most 3 final renders)

- File: `/home/quellen/dev/manim-video-skill/out/container-runs/03-git-workflows/out/Explainer-final.mp4`
  (8.2 MB)
- Duration / resolution / audio: 138.50 s (earlier final: 139.0 s), 1920x1080 at 60 fps, h264, no
  audio (silent).
- report.md: **PASS**, no WARN: stream PASS, blank PASS (1.2 s incl. start/end), holds PASS (39 %
  across 43), cuts PASS, geometry PASS (25 rules + frame-edge rule over 136 animations, none
  unchecked). LayoutGuard active, no LAYOUT lines.
- Timings (summary.json): render 974.5 s, checks 220.8 s, stills 9.0 s, total 1204.3 s (shared
  machine, 5 runs on 4 cores).
- Looked at: the final contact sheet (8 even stills) and full-size frames at 43.3 s (merge
  commit), 60.6 s (fast-forward in motion), 112.5 s (pipeline): sharp strokes, ids and tags
  legible, nothing near the edges.
- Iterations: 6 previews (2 on my own scene before the owner's change of plan, 4 on the adopted
  scene) + 1 final.
- Bugs fixed on the adopted scene: rebase id scramble (copies hop with old ids, ids fade); HEAD
  crossing the c48 -> 7d2 arrow (hop instead of glide); FadeTransform card-to-commit text overlap;
  Indicate on an arrow and Circumscribe (style-guide violations); check mark against its frame;
  title/chip 4.9 % margins; options layout 5 % margins and off-centre; pipeline 7.1 % margins;
  policy graphs off their titles and the row asymmetric; protected-main picture off-centre;
  graph slots 0.15 left of centre; main/feature cards of unequal width.
- Rubric: 19/20 (criterion 3 at 1: the ours/theirs swap in a rebase is a caption-only claim).
- Assumptions: silent, newcomer, intuitive, 16:9 1080p60 (skill defaults; unattended run).
  Content and length kept from `examples/03-git-workflows` at the owner's request.
- Known limitations: "careful: in a rebase, ours and theirs swap" has no picture; the
  "pull request" label sits about 0.14 units from its box border (tight, not touching); the two
  code cards overlap for about half a second while merging into the conflicted file (the merge
  metaphor); short ids are 3 characters (real ones are 7+); recap is text only.
