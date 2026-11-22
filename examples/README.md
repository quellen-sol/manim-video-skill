# Examples: the five test prompts

Each prompt was given to a fresh agent (Claude Opus 5.5) that had only the skill to go on. It ran
the full loop: storyboard, scene, 480p previews, frame inspection, rubric, fixes, then the
1080p60 final. The folders hold what it produced: `prompt.md`, `storyboard.md`, the final
`scene.py`, `review.md` (iteration log and final report), `notes.md` (bugs found and fixed, plus
feedback on the skill) and `stills/` (before/after pairs and the final contact sheet).

Videos are not in git. Rebuild one with
`skills/manim-video/scripts/render.sh final examples/<folder>/scene.py <Scene>`
(the scene class is `Explainer` unless `scene.py` says otherwise).

| Folder | Prompt | Narration | Previews | Final | Rubric |
|---|---|---|---|---|---|
| `01-unit-circle` | unit circle and sin, cos, tan, sec, csc, cot | silent (no answer, default) | 3 | 138.9 s | 20/20 |
| `02-llm-weights` | diagram of a modern LLM's weights and neurons | silent (no answer, default) | 5, plus a second final after a 1080p-only bug | 150.0 s | 19/20 |
| `03-git-workflows` | git: commit, branch, merge, rebase, conflicts, team workflow | silent (no answer, default) | 6 (cap) | 139.0 s | 20/20 |
| `04-fourier-epicycles` | Fourier series as rotating circles drawing a shape | silent (answered) | 2 | 129.5 s | 20/20 |
| `05-gradient-descent-narrated` | gradient descent and backpropagation on a tiny network | Kokoro `af_heart` via manim-voiceover | 6 (cap), plus one still-verified fix | 158.2 s | 20/20 |

All five finals are 1920x1080 at 60 fps and pass `qa_check.py` (the narrated one with
`--expect-audio`).

## Known limitations left in the finals

- `03-git-workflows`: during each rebase hop the 3-character commit id morphs from old to new and
  is scrambled for about half a second (found after the iteration cap); HEAD crosses a thin arrow
  for a few frames in chapter 4.
- `05-gradient-descent-narrated`: on the number line (beats 3 and 13) the dots, gap segment and
  square bases sit about 25 px below the axis line (found in the final's full-size frames).
- `02-llm-weights`: titles and captions crossfade, so for a few frames old and new text overlap.

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
