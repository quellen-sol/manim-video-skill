# Notes: 03-git-workflows (end-to-end test of the manim-video skill)

## Outcome

- Silent (default: the user could not be asked), 1920x1080 at 60 fps, about 139 s, 6 chapters
  plus title card and recap: commits, branches (with HEAD), merge (two-parent commit), rebase
  (copies with new ids, fast-forward, golden rule), conflicts (markers, ours/theirs, edit by
  hand, ours/theirs swap in a rebase), team workflow (protected main, rejected push, PR with CI
  and review, merge commit vs squash vs rebase-and-merge), recap.
- **6 preview iterations** (the cap) + 1 final render. Rubric 17/20 after iteration 1, 20/20 from
  iteration 3 on. `qa_check.py` passed every render with no WARN; every bug below was found only
  by looking at frames.

## Bugs found and how they were fixed

| Iter | Bug | Fix |
|---|---|---|
| 1 | `frames.py --beats` sampled only 0-106 s of a 137 s video, with beat labels off by about 31 s (Manim had deleted 32 of 132 partial movies, `max_files_cached = 100`) | `config.max_files_cached = 1000` in the scene; tail sampled with `--at` meanwhile |
| 1 | Caption, command chip and chapter title swaps: old and new text superimposed mid-transition | `swap()` helper: `AnimationGroup(FadeOut(old), FadeIn(new), lag_ratio=1)` |
| 1 | Chapter 1 crammed into the left third | file card moved to the centre |
| 1 | HEAD and branch tags slid across other tags and commits when switching branches | `glide()`: `MoveAlongPath` on a `CubicBezier`; control offsets picked with a small box-collision search |
| 1 | New commit's parent arrow drawn through the feature/HEAD tags | tags move with the commit, then the arrow grows |
| 1 | Rebase copies swung **down** through the tags: `TransformFromCopy` runs the transform backwards, so `path_arc` bends the opposite way to `.animate(path_arc=...)` | sign flipped |
| 1 | Straightened history left-heavy | only the copies are lifted into the main lane |
| 1 | Strategy rows crowding the caption | tighter rows, top-aligned |
| 1 | `ReplacementTransform` of different text (`CONFLICT` to `resolved`, 5 lines to 1) scrambled glyphs mid-morph | crossfade |
| 1 | Check marks colliding with "CI tests"/"review" labels | label shifts left, check beside it |
| 2 | Second rebase copy's hop crossed the first copy's new parent arrow | both copies land, then both arrows are drawn |
| 2 | Resolved line cramped in a 5-line box; protected-main graph off-centre; policy row high; recap spacing uneven (descenders); two 8-9 word captions held about 2 s | resize box, recentre, lower, fixed top-to-top step, longer holds |
| 3 | **Only visible in the 1920x1080 still**: green frame 12 px above the caption, one label 0.02 units outside the safe area | conflict layout raised 0.5, rows pulled in |
| 4-5 | Resizing file box brushed the fading "ours/theirs" labels at mid-transition | labels fade within the first third (`lambda t: min(1, 3t)`; `rush_from` was not enough) |

Known and not fixed (cap reached): the 3-character id morphs from the old id to the new one
during each rebase copy's 1.3 s hop and is briefly scrambled mid-flight (seen in the
before/after stills). Fix would be to crossfade the id instead of morphing it. Also accepted:
HEAD crosses the long `c48 -> 7d2` arrow line (not a label) for a few frames on `git switch main`
in chapter 4.

## What was checked

- Every iteration: `render.sh` LAYOUT output (never any warning), `qa_check.py --expect-silent`,
  `frames.py --beats --mid` (260 stills, 17 contact sheets; all opened in iterations 1 and 2,
  the changed beats in iterations 3 to 6), full-size frames where something looked close.
- Full-resolution stills with `render.sh still -- -n 0,84` and `-n 0,126` (densest text frames).
- Final (760 s render on a loaded machine): `qa_check.py --expect-res 1920x1080 --expect-silent`
  all PASS (1920x1080 @ 60 fps, 139.00 s, no audio; blank 1.2 s; holds 45 % across 47; no cuts);
  `frames.py --count 8` contact sheet and one full 1080p frame opened.
- Git semantics checked against: parent pointers (child to parent arrows), branch = ref that moves
  with commits on the checked-out branch, HEAD, `git switch -c`, merge commit with two parents,
  rebase creating new commits (new ids) with originals unreferenced, fast-forward, golden rule,
  conflict markers (`<<<<<<< HEAD` / `=======` / `>>>>>>> feature`), ours = HEAD in a merge and the
  swap in a rebase, protected branch rejecting a direct push, PR + CI + review, merge commit /
  squash / rebase-and-merge.

## Skill feedback (most important first)

1. **`frames.py --beats` silently breaks on videos with more than 100 animations.** Manim's
   default `max_files_cached = 100` deletes the oldest partial movies; `beat_times()` skips
   missing files (`if not f.exists(): continue`), so every timestamp shifts earlier, beats are
   mislabelled ("beat 33" at 0.5 s) and the end of the video is never sampled. No warning is
   printed. A 2-3 minute explainer easily has 130+ `play`/`wait` calls. Suggested fix: have
   `render.sh` pass `--max_files_cached -1` (or set it), and make `frames.py` fail loudly (or
   fall back to `--count`) when listed partials are missing. Until then, the scene template could
   set `config.max_files_cached = 1000`.
2. **`TransformFromCopy` flips the direction of `path_arc`** (it plays target-to-source
   backwards). Not in `api-cheatsheet.md`; it cost one bug. Worth a line in the Gotchas.
3. **No pattern for swapping text in place.** `FadeOut(old)` + `FadeIn(new)` in one `play` at the
   same position superimposes both (every caption change in iteration 1), and `Transform` /
   `ReplacementTransform` between different strings scrambles glyphs mid-morph. A `swap()`
   helper (sequential crossfade) in `templates/scene_silent.py` and a cheatsheet line
   ("text whose content changes: crossfade, not Transform") would prevent both. Pattern 6
   (commit graph) itself uses `TransformFromCopy(f1, r1)` between "b1" and "b1'", which has the
   same mid-morph scramble.
4. **Moving labels across a diagram.** Pattern 6 moves tags with `.animate.next_to(...)`
   (straight lines), and has no HEAD. On a two-lane graph, switching branches moves a tag from
   above one lane to below the other, and a straight path or `path_arc` crosses tags and commits.
   A routing tip (`MoveAlongPath` + `CubicBezier` with control offsets; move labels before
   drawing edges that would cross them) would help any graph-style video.
5. **`render.sh still -- -n 0,K`: K is not the number in `index.txt`.** frames.py numbers beats
   from 1 (partial-movie order); `-n 0,K` stops after 0-based animation K. Beat N (end) was
   `-n 0,N-1` here. SKILL.md and the checklist say "K = animation number from `index.txt`".
   Also, `still` always writes the same file name (`Explainer_ManimCE_v0.22.1.png`), so each
   still overwrites the previous one (lost my iteration-3 still for the before/after pair).
6. **The 480p preview and its 480 px contact-sheet tiles hide near-collisions.** A 0.09-unit gap
   (12 px at 1080p, 5 px at 480p) looked fine in the sheets and was only obvious in the 1080p
   still. `LayoutGuard` does not check the safe area (±6.4, ±3.4) defined in the style guide, nor
   text-to-shape proximity (a caption vs a frame around other text), and it only sees resting
   states, never mid-animation collisions. It reported nothing in any iteration while real layout
   bugs existed. Suggest: a safe-area check, a text vs filled/stroked shape check with a margin,
   and a sentence in SKILL.md that it cannot see moving collisions (the `--mid` frames can).
7. **Fonts and text metrics.** The style guide says to check fonts with `fc-list : family` "in
   your renderer", but with Docker-only rendering there is no script for it (`check_env.sh` does
   not list fonts). I wrote a probe scene printing `manimpango.list_fonts()` and `Text` widths.
   Useful facts to put in the style guide: `Noto Mono` and `Noto Sans Mono` exist in the image; a
   mono character is about 0.213 units wide at size 26 (code panels can be planned without a render).
8. **Default `frames.py` output dir is wiped on each run** (`frames_<stem>`), so the previous
   iteration's frames are lost unless `--out` is used. Before/after comparisons (which the
   review log asks for) need the old frames; per-iteration folders by default would help.
9. **Volume of stills.** `--beats --mid` gave 260 stills on 17 sheets per iteration. Opening all of
   them is right for the first two passes but slow afterwards; SKILL.md's "re-watch the changed
   beats and the full contact sheet" is ambiguous with 17 sheets. A `--range T0,T1` option (or
   beats by chapter) would make re-checks of changed beats cheaper.
10. **Duration estimate.** The checklist wants the length within about 20 % of the storyboard; my
    planning estimate (175 s) was 22 % over the built 137-139 s because silent caption beats run
    shorter than guessed. Suggest: "after the first preview, update the storyboard times from
    the measured beats", or a rule of thumb (sum of `run_time` + `wait`).
11. What worked well: the Scope paragraph (with exactly this git example) led straight to a
    chapter structure; pattern 6 was a good starting point; the style guide's zones and sizes held
    up at 1080p; `qa_check.py` was fast and its PASS lines made the "explain every WARN" rule easy;
    `--mid` frames caught nearly every bug; `render.sh` error-free throughout.
