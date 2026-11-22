# Review log: Git, visually

Scene: `scene.py`, class `Explainer`. Narration: silent (default; the user could not be asked).

## Iteration 1 (preview)

- Video: `media/videos/scene/480p15/Explainer.mp4` (137.1 s, 854x480 @ 15 fps), render 126 s.
- `qa_check.py --expect-silent`: PASS stream, PASS blank (1.1 s total), PASS holds (47 % still
  across 58 holds), PASS cuts. Overall PASS.
- `LAYOUT` warnings: none.
- Stills looked at: `frames.py --beats --mid` sheets 01 to 12 (181 stills), all opened; full-size
  frame 156 (conflict strategies). **The beat stills stopped at 106 s of 137 s**: Manim keeps at
  most 100 partial movie files (`max_files_cached`), so the first 32 of 132 partials had been
  deleted and `frames.py` silently skipped them, shifting every beat time by about 31 s and never
  sampling the last 31 s. Extracted the tail separately (`frames.py --at 105.5,...,136.3`, 2 sheets,
  both opened). Workaround for later iterations: `config.max_files_cached = 1000` in the scene.

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| all chapters (every caption, command and title change) | Crossfades overlap: old and new caption (or command chip, or chapter title) are both half-visible at the same spot mid-transition, reading as garbled text | Sequential crossfade: `AnimationGroup(FadeOut(old), FadeIn(new), lag_ratio=1)` in `caption_to`, `cmd_to`, `title_to` |
| 2-3 / 5-22 s | Composition left-heavy in chapter 1: file card and commits all in the left third, right two thirds empty | Move the file card to the centre (x = 0) so snapshots fly left into the history |
| 4 / ~31 s | `HEAD` (moving with `path_arc`) slides across the `feature` tag on its way down | Move HEAD along a `CubicBezier` path that swings right and arrives from below-right (`glide` helper) |
| 5 / ~34 s | The new commit's parent arrow (e5b to 7d2) is drawn through the `feature` and `HEAD` tags for about 1 s | Move the tags (along a path below the lane) together with the new commit, then grow the arrow |
| 8 / ~62-65 s | Rebase copies swing **down** through the `feature`/`HEAD` tags: `TransformFromCopy` plays the transform backwards, so `path_arc=-0.5*PI` bends the other way | `path_arc=+0.5*PI` for `TransformFromCopy` (hops up over the lane) |
| 8-9 / ~68, 71 s | HEAD crossing `6d7` and the `feature` tag on `git switch main`; main tag grazing `c48` on the fast-forward | `glide` paths routed around the nodes and tags |
| 9 / ~74 s | After "straighten", the whole line sits in the left 60 % of the frame | Keep `c48` in place and only lift the copies into the main lane (line spans the frame) |
| 13 / ~88 s | Strategy rows run low: the green frame around "edit by hand" touches the caption | Tighter row spacing (0.3), top-align the rows with the file header |
| 13 / ~92 s | `ReplacementTransform` of the 5-line conflict into the resolved line, and of `CONFLICT` into `resolved`, shows scrambled glyphs mid-morph | Crossfade (`FadeOut` old, then `FadeIn` new) |
| 16 / ~110 s | Green check marks collide with the "CI tests" and "review" box labels | Shift the label left and place the check to its right |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: each commit is a saved snapshot of the files that points back to the previous
one, and branches (main, feature) are labels that move as you commit; HEAD shows where you are.
Diverged work is combined either by a merge commit with two parents or by a rebase that copies
your commits onto the tip of main so main just slides forward, but you must not rebase shared
commits. When both sides edit the same line Git stops and a person picks ours, theirs or a
hand-made combination; in a team main is locked and changes arrive as pull requests that pass
tests and review, landed by a team merge policy. Matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | opens on a file card being saved as snapshots |
| One idea per beat | 2 | each caption carries one idea |
| Every step motivated (no leaps) | 1 | why rebase at all is never said: "back to before the merge: the other option" gives no reason |
| Picture before formula | 2 | the git command appears with the action it names |
| Progressive reveal | 2 | graph grows commit by commit |
| Colour coding consistent | 2 | blue main, orange feature (copies and squash stay orange), white HEAD, yellow focus only |
| Minimal, legible on-screen text | 1 | recap is 5 lines and about 30 words (guide: about 12 on screen) |
| Pacing (holds after reveals, not dragging) | 1 | rebase stretch is rushed: `git switch feature` shows for 1.4 s before the next command |
| Payoff and recap | 2 | straight line of history, resolved file, recap |
| Matches the learning goal and requested depth | 2 | intuitive, covers the enterprise layer (protected main, PR, CI, review, merge policy) |
| **Total** | 17/20 | passes, but visual bugs above must be fixed |

## Iteration 2 (preview)

- Video: 138.3 s, render 158 s. `qa_check.py --expect-silent`: PASS stream, blank (1.1 s), holds
  (46 % across 56 holds), cuts. Overall PASS. `LAYOUT` warnings: none.
- Partial movies: 132 listed, 0 missing (the `max_files_cached` workaround works), so
  `frames.py --beats --mid` covered the whole video: 260 stills, sheets 01 to 17, all opened.
- Re-checked every iteration-1 bug in the new frames: crossfades clean (no double captions,
  commands or titles in any mid frame); chapter 1 balanced; HEAD and tag glides clear of tags in
  all mid frames (switch -c, commit on feature, switch main x2, switch feature, fast-forward);
  rebase copies hop up over the lane; straight line spans the frame; strategy rows clear the
  caption; resolved file and tag crossfade without glyph scrambling; PR checks sit beside the labels.
  All iteration-1 bugs: fixed.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 8 / ~62 s | The second rebase copy's hop crosses the first copy's freshly drawn parent arrow (2be to c48) | Draw both parent arrows after both copies have landed |
| 8 / ~68 s | HEAD's `git switch main` glide brushes the long c48-to-7d2 arrow (a thin line, not a label) | Accepted: a moving tag crossing a line for a few frames; it never covers text |
| 13 / ~93 s | Resolved line `fetchUser(id, cache)` nearly touches the left and right edges of the (5-line) file box | Resize the box to the single resolved line (top-left anchored) |
| 15 / ~100 s | Protected-main mini graph sits left of centre, right half empty | Shift the mini graph 1 unit right |
| 17 / ~120 s | Policy columns sit high; empty band above the caption | Move the columns 0.3 down |
| 18 / ~131 s | Recap line spacing uneven ("branch" and "merge" lines closer than the others: bounding boxes differ by descenders) | Place lines on a fixed top-to-top step |
| 7, 8 / ~52, 64 s | Two 8 to 9 word captions held only about 2 to 2.5 s ("go to main, the branch...", "new copies, new ids...") | Longer holds (+0.4 s, +0.5 s) |

### Intuitiveness

Newcomer summary: unchanged from iteration 1, plus a reason for rebase ("for a straight history")
and its payoff ("one straight line of history").

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | file card saved as snapshots |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | rebase now motivated by a straight history; team chapter motivated by "main is protected" |
| Picture before formula | 2 | |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | |
| Minimal, legible on-screen text | 2 | recap cut to about 20 words, built line by line |
| Pacing (holds after reveals, not dragging) | 1 | two long captions read in about 2 s (fixed for iteration 3) |
| Payoff and recap | 2 | |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 19/20 | |

## Iteration 3 (preview)

- Video: 139.3 s, render 157 s. `qa_check.py --expect-silent`: PASS stream, blank (1.1 s), holds
  (47 % across 56 holds), cuts. Overall PASS. `LAYOUT` warnings: none.
- Stills: `frames.py --beats --mid`, 260 stills, 17 sheets; opened the changed beats in full
  (sheets 07, 08, 09, 12, 13, 16, 17). Full-resolution check of the densest frame:
  `render.sh still scene.py Explainer -- -n 0,84` (frames.py beat 85 = animation index 84).
- Iteration-2 fixes confirmed in the frames: both rebase copies land before the parent arrows
  are drawn (the hop of the second copy no longer crosses an arrow); resolved file box hugs the
  line; protected-main graph centred; policy columns lowered; recap spacing even; longer holds.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 13 / ~90 s, seen only in the **1920x1080 still** | The green frame around "edit by hand" ends about 12 px above the caption (they look separate in the 480p preview); "loses the rename" ends 0.02 units past the safe area | Conflict layout raised by 0.5 (there was an empty band above it); rows moved in from the right edge (`buff=0.9`) |
| 18 / ~133 s | Recap is small (size 32) and leaves much of the frame empty | Size 36, 0.85 step |

### Intuitiveness

Unchanged: 20/20 after the pacing fix (all criteria 2). Two long captions now hold 2.4 to 3 s.

## Iteration 4 (preview)

- Video: 139.3 s, render 177 s. `qa_check.py --expect-silent`: overall PASS (all four checks).
  `LAYOUT` warnings: none.
- Stills: sheets 10, 11 and 17 (changed beats) opened; full-resolution stills
  `-n 0,84` (strategies) and `-n 0,126` (merge policies, the smallest text in the video) opened.
- Confirmed at 1920x1080: the green frame now clears the caption by about 80 px; every element is
  inside x within ±6.4; the policy minis, `main` tags (size 24) and traits read clearly; recap
  evenly spaced at size 36. Conflict file no longer leaves an empty band under the title.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 13 / ~92 s (mid frame) | While the file box shrinks to the resolved line it grows 0.4 wider and brushes the still-fading "ours (main)" label | Labels fade with `rush_from` |

## Iteration 5 (preview)

- Video: 139.3 s, render 139 s. `qa_check.py --expect-silent`: overall PASS. No `LAYOUT` warnings.
- Stills: sheet 11 and full-size mid frame 172 (t = 91.9 s) opened.

### Visual bugs

| Beat / time | Bug | Fix |
|---|---|---|
| 13 / 91.9 s (mid frame) | "ours (main)" still about 20 % visible under the box edge at the midpoint (`rush_from` is not fast enough) | Labels fade with `rate_func=lambda t: min(1, 3t)` (gone by a third of the move) |

## Iteration 6 (preview, last allowed by the cap)

- Video: 139.3 s, render 146 s. `qa_check.py --expect-silent`: PASS stream, blank (1.1 s), holds
  (47 % across 56 holds), cuts. Overall PASS. No `LAYOUT` warnings.
- Stills: `frames.py --beats --mid` (260 stills); frames at 91.60, 91.75, 91.93 and 92.10 s
  across the resolve transition opened: the ours/theirs labels are gone before the box edge
  reaches them. No other beat changed since iteration 5.
- While picking stills for the report I noticed in frames from iterations 1 and 2 (rebase,
  ~51.5 s) that each copy's 3-character id morphs from the old id to the new one during the
  1.3 s hop and is scrambled mid-flight. Not fixed: the iteration cap was reached; listed under
  known limitations.

### Stop check (Step 6)

- Open visual bugs: none blocking. Accepted and explained: (1) HEAD crosses the long
  `c48 -> 7d2` arrow line for a few frames during `git switch main` in chapter 4 (a line, never
  text); (2) the id morph scramble during the rebase hop (above).
- `qa_check.py`: no FAIL, no WARN.
- Rubric: 20/20 (no criterion below 2).

## Final

- File: `/home/quellen/dev/manim-video-skill/out/03-git-workflows.mp4` (copy of
  `examples/03-git-workflows/media/videos/scene/1080p60/Explainer.mp4`, 8.1 MB).
- Duration / resolution / audio: 139.0 s, 1920x1080 at 60 fps, h264, no audio stream (silent).
  `render.sh final` took 760 s on a shared, heavily loaded 4-core machine (load average 12-15).
- Iterations: 6 previews (the cap) + 1 final.
- Bugs found and fixed: superimposed caption/command/title crossfades; left-heavy chapter 1;
  HEAD and branch tags sliding across other tags (Bezier glides); a parent arrow drawn through
  tags; rebase copies swinging through tags (`TransformFromCopy` reverses `path_arc`); the
  second copy's hop crossing a fresh arrow; left-heavy straightened history; strategy rows
  crowding the caption (twice, the second only visible at 1080p); glyph-scrambling text morphs
  (`CONFLICT` to `resolved`, 5 lines to 1); check marks on top of box labels; cramped resolved
  box; off-centre protected-main graph; high policy row; uneven recap spacing; short holds on two
  long captions; resizing box brushing fading labels. Also the `frames.py` coverage problem
  (`max_files_cached`), worked around in the scene.
- Checked on the final: `qa_check.py --expect-res 1920x1080 --expect-silent`: PASS stream
  (h264 1920x1080 @ 60 fps, 139.00 s, 0 audio streams), PASS blank (1.2 s incl. start/end),
  PASS holds (45 % still across 47 holds), PASS cuts; overall PASS. No `LAYOUT` warnings.
  `frames.py --count 8` contact sheet opened (all six chapters, correct colours and text) and the
  full 1080p frame at 43.4 s (merge commit: strokes, arrowheads, ids and tags sharp).
  Rubric 20/20.
- Assumptions: silent, because the narration question could not be asked (unattended run);
  newcomer audience, intuitive depth, 16:9 1080p60. Broad prompt, so 6 chapters in about 2.3
  minutes (SKILL.md "Scope").
- Storyboard in one paragraph: a file card is saved as snapshots that become commits pointing to
  their parents; `main` is a label that moves; HEAD marks where you are and `feature` is a second
  label; work diverges when a teammate's commit lands on main; a merge joins the two with a
  two-parent commit; rewinding, a rebase replays the feature commits as copies with new ids on
  top of main, main fast-forwards and history becomes one line (never rebase shared commits);
  when both branches edit the same line Git marks a conflict and a person keeps ours, theirs or
  (best here) combines both by hand, then commits (and ours/theirs swap in a rebase); in a team
  main is protected, a direct push is rejected, changes arrive by pull request through CI and
  review, and the team picks merge commit, squash or rebase-and-merge; recap.
- Left out: staging area, remotes and fetch/pull (a teammate's commit simply "lands on main"),
  cherry-pick, interactive rebase, reset/revert, tags, `-s ours` vs `-X ours`, CODEOWNERS and merge
  queues.
- Known limitations: (1) during each rebase copy's 1.3 s hop the 3-character id morphs from the
  old id to the new one and is briefly scrambled mid-flight (fix: crossfade the id); found after
  the iteration cap, so not fixed. (2) HEAD crosses the long `c48 -> 7d2` arrow line for a few
  frames on `git switch main` in chapter 4 (accepted). (3) Short ids are 3 characters (real
  short ids are 7). (4) Recap is text only.
