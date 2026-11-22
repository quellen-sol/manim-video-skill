# Examples: the five test prompts

Each prompt was given to a fresh agent (Claude Opus 5.5) that had only the skill to go on. It ran
the full loop: storyboard, scene, 480p previews, frame inspection, rubric, fixes, then the
1080p60 final. The folders hold what it produced: `prompt.md`, `storyboard.md`, the final
`scene.py`, `review.md` (iteration log and final report), `notes.md` (bugs found and fixed, plus
feedback on the skill) and `stills/` (before/after pairs and the final contact sheet).

Videos are not in git. Each folder is also a job directory for the render container (it has a
`job.json`): `skills/manim-video/scripts/render-in-container.sh examples/<folder> --quality final`
writes `examples/<folder>/out/Explainer-final.mp4`.

The folders now hold the **container re-run** (2026-11-22, below): `scene.py`, `job.json`,
`storyboard.md`, `review.md` and `stills/container-final-sheet.png` come from it. `notes.md`, the
other `stills/` and `prompt.md` are from the first run, which used the earlier render path (the
official Manim image driven by `render.sh`); its scenes are in git history at `9641aa2`.

## Container re-run (2026-11-22)

Five fresh agents ran the same prompts through `render-in-container.sh` only, starting from the
first run's scenes, with two extra bars: rubric at least 18/20 and the measured geometry check
(GeometryGuard) passing. That check was added after the owner spotted that the first unit-circle
video's axes were not symmetric about the circle and its figure sat 5% from the frame edge, a bug
the first run's visual review (19/20) had missed.

| Folder | Previews | Finals used (cap 3) | Final | Rubric | Geometry (final) | Main fixes |
|---|---|---|---|---|---|---|
| `01-unit-circle` | 6 | 2 | 138.9 s | 20/20 | PASS, 9 rules | symmetric axes, figure centred with margins, the doubled labels at 25 s (real for about 0.7 s), caption crossfades, stretched `Indicate` |
| `02-llm-weights` | 5 | 1 | 150.0 s | 19/20 | PASS, 23 rules | title/caption crossfade overlap, figures re-centred, a caption outside the safe area |
| `03-git-workflows` | 6 (4 on this scene) | 1 | 138.5 s | 19/20 | PASS, 25 rules (1 unchecked*) | rebase id scramble, HEAD crossing an arrow, chapter layouts off-centre or at 5% margins |
| `04-fourier-epicycles` | 4 | 1 (+1 stopped) | 129.5 s | 20/20 | PASS, 13 rules | caption swaps, thumbnails crossing, beat-3 rig 0.33 units low, panel off-centre |
| `05-gradient-descent-narrated` | 4 | 2 | 161.2 s, AAC 161.24 s | 20/20 | PASS, 18 rules | number-line markers 25 px below the axis, panels inside the margin, network off-centre, audio 4 s short (now padded) |

All five finals are 1920x1080 at 60 fps, rendered in the container on the CPU (Cairo, GPU off),
and pass `out/report.md` with no FAIL and no WARN. *In `03`, `symmetric(forked)` was measured
and held six times during the final render; the final checker version defers it (UNCHECKED)
because the tracked graph still references faded-out commit ids, not because it fails.
Re-measured with `render-in-container.sh <folder> --geometry`: 0 violations in all five.

| Folder | Prompt | Narration | Previews | Final | Rubric |
|---|---|---|---|---|---|
| `01-unit-circle` | unit circle and sin, cos, tan, sec, csc, cot | silent (no answer, default) | 3 | 138.9 s | 20/20 |
| `02-llm-weights` | diagram of a modern LLM's weights and neurons | silent (no answer, default) | 5, plus a second final after a 1080p-only bug | 150.0 s | 19/20 |
| `03-git-workflows` | git: commit, branch, merge, rebase, conflicts, team workflow | silent (no answer, default) | 6 (cap) | 139.0 s | 20/20 |
| `04-fourier-epicycles` | Fourier series as rotating circles drawing a shape | silent (answered) | 2 | 129.5 s | 20/20 |
| `05-gradient-descent-narrated` | gradient descent and backpropagation on a tiny network | Kokoro `af_heart` via manim-voiceover | 6 (cap), plus one still-verified fix | 158.2 s | 20/20 |

All five finals are 1920x1080 at 60 fps and pass `qa_check.py` (the narrated one with
`--expect-audio`).

## Known limitations left in the finals (container re-run)

- `01-unit-circle`: the recap boxes read as an overline for about half a second while they draw;
  a half-turn briefly sweeps over the "csc θ" label; the right panel holds only a caption for
  the first 25 s.
- `02-llm-weights`: toy values for weights and scores; a 1 s diagonal "staircase" when a row
  turns into a column; the query/key and neuron beats carry two or three ideas each.
- `03-git-workflows`: "in a rebase, ours and theirs swap" is a caption without a picture; "pull
  request" sits 0.14 units from its box edge; two code cards overlap for half a second while
  merging.
- `04-fourier-epicycles`: captions name each result while it is still being drawn; the smallest
  of the 50 arrows tangle near the pen.
- `05-gradient-descent-narrated`: in beats 1-2 and 8 the lower half of the frame is empty for
  about 15 s (the network lives in the upper band by design); the network is linear (no
  activation function).

## What the runs taught the skill

These were folded back into `SKILL.md`, the references and the scripts:

- `frames.py` per-animation stills were silently mistimed once a scene had more than 100
  animations (Manim deletes older partial movies). `render.sh` now raises the limit and
  `frames.py` refuses untrustworthy timings and falls back to even spacing.
- Narrated re-renders that reused Manim's animation cache drifted from the audio:
  `render.sh` now disables that cache for narrated scenes, and `frames.py --cues` checks sync
  against the subtitle file manim-voiceover writes.
- The layout checker now also reports text outside the safe area, text crossed by lines or
  arrows, and text overlapping braces; it no longer reports invisible `ValueTracker` groups, and
  it announces that it is active.
- Text swaps (crossfades, `Transform` between different strings), highlighting (`Indicate` on
  lines, `Circumscribe` on formulas), bound-method updaters, `TransformFromCopy` arcs and
  `NumberLine` positioning are now documented, with a swap helper in the template.
- The 480p preview hides collisions of a few pixels: the loop now renders the busiest frames at
  full resolution every iteration, and says what to do when the final reveals a bug.
- `qa_check.py` stall detection was too coarse (false stalls during small text reveals) and its
  audio-length warning fired on silent outros; both were tuned against these videos.
