# Review log: How a tiny network learns (gradient descent and backpropagation)

Scene: `scene.py`, class `Explainer` (`LayoutGuard`, `VoiceoverScene`). Narration: Kokoro
`af_heart` through manim-voiceover and the skill's `KokoroService` (38 sentences or
clauses, one `voiceover` block each, animations timed with `tracker.duration` / `get_remaining_duration()`).

## Iteration 1 (preview)

- Video: `media/videos/scene/480p15/Explainer.mp4` (159.0 s, 854x480 @ 15 fps, AAC audio).
  Render took 732 s (first-time TTS for 37 sentences on a CPU Kokoro, with 2 other renders
  running in parallel; load average about 10 on 4 cores).
- `qa_check.py --expect-audio`:
  - `WARN audio audio lasts 154.99s but video lasts 159.00s`: explained. Manim's audio track
    ends with the last clip; the 4 s after it are the silent outro (2 s hold on the recap,
    1 s fade, 1 s end).
  - `WARN holds nothing moves for 25.9s at 72.8-98.7s`: false positive. The frames at 78-98 s
    show the nudges, curved arrows and the product formula appearing one by one; those are
    small (a few hundred pixels at 480p), below `freezedetect`'s noise threshold.
  - PASS stream, audio level (mean -29.7 dB, peak -7.3 dB), blank, cuts.
- `LAYOUT` warnings: none printed. Suspicious for a scene this dense, so iteration 2 adds a
  one-line probe that prints whether `LayoutGuard` is really mixed in (the template's
  `except ImportError` fallback would hide a failed import).
- **Tooling problem found:** `frames.py --beats` mislabelled every still. The scene has 109
  animations; Manim keeps at most 100 partial movie files (`max_files_cached`), so it
  deleted the first 9. `frames.py` skips missing partials without adding their duration, so
  each "beat N (end)" frame was taken about 10.7 s early, labelled 9 beats off, and the last
  10.7 s of the video were never sampled. Workaround: rebuilt the timeline myself
  (`media/qa/tools/timeline.py`: offset = video duration minus the surviving partials),
  extracted 144 stills with `frames.py --at`, and rendered later iterations with
  `-- --max_files_cached 1000`.
- Narration sync: from the log order of the `converted media/voiceovers/*.mp3` lines and the
  rebuilt timeline, every voiceover block start (e.g. 10.67, 14.93, 18.53, 41.07, 78.60,
  105.53 s) is followed by a speech onset 0.1-0.2 s later in the audio (10.85, 15.05, 18.65,
  41.18, 78.72, 105.65 s). The still at each block start shows the visual the sentence
  names (nudges appear on "nudge w one", the tangent on "the slope here", and so on).
- Stills looked at: all 9 contact sheets (144 tiles, every animation end plus the midpoint of
  every animation of 1.5 s or longer).

### Visual bugs (references/visual-qa-checklist.md)

| Beat / time | Bug | Fix |
|---|---|---|
| all network beats | Text too small for a phone: equations 36-40 (style guide says 44-56), node symbols 44; the diagram hugs the top half | sizes up (equations 44, labels 40, node symbols 48, nodes r = 0.55), number line unit 1.1 → 1.25 |
| 3 / 22 s | Yellow gap label "2" sits under the number line next to the tick "2": two "2"s stacked, ambiguous | gap label above the segment, where the square then grows over it |
| 13 / 139 s | The moved ŷ label overlaps the corner of the new 0.71 square | ŷ label placed to the left of its dot, raised above the line |
| 2, 4, 8, 12 / title changes | Old and new chapter titles overlap mid-crossfade (e.g. "Forward pass" over "How a tiny network learns") | `AnimationGroup(FadeOut(old), FadeIn(new), lag_ratio=0.8)` |
| 5 / 44 s | "downhill" arrow starts left of the dashed drop line and crosses it | arrow starts further along the tangent direction, right of the line |
| 14 / 150 s | Loss history small, reads oddly ("L : 4 → 0.71 → 0.0005") | word "loss" plus the numbers at size 48 |

### Intuitiveness (references/intuition-rubric.md)

Newcomer summary: a two-weight network turns 2 into 1 when it should give 3, and the squared
gap (a square of area 4) is the loss. Sliding one weight draws a valley; the slope says which
way is downhill, and gradient descent steps against it, by learning rate times slope. To get
every weight's slope at once, backprop multiplies local rates from the loss backwards (the
chain rule, seen first as a nudge travelling down the chain); one step on both weights cuts
the loss from 4 to 0.71. This matches the learning goal.

| Criterion | Score 0-2 | Note |
|---|---|---|
| Concrete anchor first | 2 | a number flows through a tiny network; "we wanted three" |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | valley → slope → step; "millions of weights" motivates backprop; nudge before chain rule |
| Picture before formula | 2 | square before L formula, valley before update rule, nudge before chain rule |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | signals blue, weights teal, target green, loss red, gradients orange |
| Minimal, legible on-screen text | 1 | labels only, but too small (see bugs) |
| Pacing (holds after reveals, not dragging) | 2 | narration sets the pace; 0.5-1.5 s holds between blocks |
| Payoff and recap | 2 | shrinking square, then the four-step loop with the loss history |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 19/20 | |

## Iteration 2 (preview)

Changes: all iteration-1 fixes, plus `config.max_files_cached = 1000` in the scene (Manim 0.22
has no `--max_files_cached` CLI flag: the first attempt with `render.sh ... -- --max_files_cached`
failed in 7 s with "No such option"), plus a one-line probe printing whether `LayoutGuard` is
mixed in.

- Video: 159.0 s. Render 146 s (all 37 voiceover clips came from `media/voiceovers/` cache).
- `qa_check.py`: same two WARNs as iteration 1 (silent 4 s outro; small-element false stall at
  72.7-98.7 s). No FAIL.
- `LAYOUT`: probe printed `QA-GUARD mixed in: True`; the guard was active and found nothing.
  A later `render.sh still` printed its `LAYOUT END` line, so it does report.
- `frames.py --beats --mid`: now maps correctly (109 partials, beat 1 at 0.7 s, last tile at
  157.96 s). Looked at all 14 sheets.
- Full-resolution check: `render.sh still scene.py Explainer -- -n 0,83` (end of the backward
  sweep, the densest frame). All labels readable at 1080p (equations about 50-60 px tall).

| Beat / time | Bug | Fix |
|---|---|---|
| 1, 3 titles | fixed: titles no longer overlap | - |
| 13 / 144 s | fixed: ŷ label clear of the new square, but its foot touches the tick at 2 (full-size 480p frame) | raise the label (0.32 → 0.45 above the line) |
| 10 / 88-95 s | Sync: the three ×rate arcs start at 15 % of the sentence "Each link scales the nudge by its own local rate: times two, times one half, times minus four", so "×2" appears about 1-1.5 s before "times two" is said | split into two voiceover blocks; arcs get a third of "Times two, times one half, times minus four." each |
| 1, 3 | Sync: smaller leads (0.5-0.8 s): edges before "two weights", square before "square it" | retimed fractions |

Rubric: criterion 7 (text) now 2; total 20/20.

## Iteration 3 (preview)

- Video: 159.6 s; render 199 s. qa_check: same explained WARNs (stall window now 73.5-89.7 s).
- Looked at all 14 sheets. Fixed and verified: ŷ label above the tick; beat 10 links glow on
  "Each link scales...", then each arc appears on its own phrase.
- **Sync check with the subtitle file.** manim-voiceover writes `Explainer.srt` next to the video
  with every sentence's exact start and end (renderer time). One still at each sentence end
  (49 cues, 3 sheets) showed every named visual on screen.
- **Bug found: audio/video drift caused by Manim's cache.** Block starts in the SRT preceded the
  matching animation starts by 0.07 s at 3 s, 0.21 s at 20 s and 0.43 s from 80 s on;
  frames at 91.60-92.53 s confirmed the "×2" arc starts at about 92.2 s while its sentence's
  audio starts at 91.70 s. Cause: 30 of 108 animations came from the partial-movie cache; a
  cached animation advances `renderer.time` (where audio is placed) by its exact `run_time`,
  but its cached file has `ceil(run_time × fps)` frames, so each one adds up to one frame of
  lag. The drift grew exactly over the cached ranges (animations 0-17, 48-63, 97-107) and was
  absent in iteration 1 (nothing cached). Fix: render with `-- --disable_caching` from now on,
  including the final.

## Iteration 4 (preview, same scene, `--disable_caching`)

- Video: 159.13 s (0.47 s shorter: the drift is gone); 0 cached animations.
- Every block start in the SRT now coincides with an animation start (offset 0.00 s); speech
  onsets in the audio are a constant 0.12 s after each block start (Kokoro's lead-in).
- Sentence-end stills (49 cues) looked at: all in step, except the recap: the four loop boxes
  were spread evenly over the sentence, so at "...a loss, a backward" the loss box was still
  fading in (about 0.6 s late). Fix: time each box to its phrase (fractions from the SRT).

## Iteration 5 (preview, `--disable_caching`)

- Video: 159.2 s; qa_check unchanged (explained WARNs only). Recap stills at 145.6-150.2 s:
  each box arrives as its phrase is spoken. Looked at sheets 13-14 (changed beat).
- While picking before/after stills for the report, a full-size frame at 23.5 s showed a
  **new defect from the iteration-2 fix**: the gap label "2", moved above the segment with
  `buff=0.15`, is crossed by the number line's tick at 2 and reads like "?". I had missed it on
  the contact sheets. A final render had already started; stopped it (and its orphaned
  container process, see notes.md), fixed with `buff=0.3`.

## Iteration 6 (preview, `--disable_caching`; the last one the cap allows)

- Video: 159.2 s; qa_check unchanged. Full-size frame at 24.0 s: "2" sits clear above the tick.
  Looked at sheet 3 (changed beat) and, because I had missed one defect, at a full-size frame
  of the other label next to a line, the "downhill" label (48.5 s): it is crossed by the
  dashed drop line and its right end touches the curve.
- Fix: arrow moved inside the valley, parallel to the tangent and 0.5 units off it, label to the
  right of its tip. With no preview iterations left, verified at full resolution with
  `render.sh still scene.py Explainer -- -n 0,36` (the skill's full-res check, not a preview):
  clean, no contact with curve or drop line. The final render was then checked again.

### Rubric (iterations 2-6)

| Criterion | Score | Note |
|---|---|---|
| Concrete anchor first | 2 | |
| One idea per beat | 2 | |
| Every step motivated (no leaps) | 2 | |
| Picture before formula | 2 | |
| Progressive reveal | 2 | |
| Colour coding consistent | 2 | |
| Minimal, legible on-screen text | 2 | sizes fixed; verified at 1080p |
| Pacing | 2 | narration-driven; each visual lands on its words |
| Payoff and recap | 2 | |
| Matches the learning goal and requested depth | 2 | |
| **Total** | 20/20 | |

## Final

- File: `/home/quellen/dev/manim-video-skill/out/05-gradient-descent-narrated.mp4`
  (copy of `media/videos/scene/1080p60/Explainer.mp4`; subtitles in `Explainer.srt` beside it).
- Duration / resolution / audio: 158.22 s, 1920x1080 @ 60 fps h264, AAC 48 kHz stereo, 8.3 MB.
  Rendered with `render.sh final scene.py Explainer -- --disable_caching` in 547 s (0 cached
  animations, 0 LAYOUT warnings).
- Iterations: 6 previews, 1 full-resolution `render.sh still` check, 1 final (a first final
  attempt was stopped when the tick/label defect was found).
- Bugs found and fixed: tiny text; ambiguous gap label (then crossed by a tick); ŷ label
  overlapping the 0.71 square (then touching a tick); title crossfade overlap; narration
  leads/lags in beats 1, 3, 10 and the recap; A/V drift of up to 0.43 s from Manim's cache;
  `frames.py --beats` mistiming from evicted partials (tooling); "downhill" label crossing the
  drop line and curve.
- Checked on the final:
  ```
  qa_check: .../media/videos/scene/1080p60/Explainer.mp4
    PASS stream h264 1920x1080 @ 60 fps, 158.22s, 1 audio stream(s)
    WARN audio  audio lasts 154.24s but video lasts 158.22s
    PASS audio  audio level mean -29.7 dB, peak -7.3 dB
    PASS blank  no long empty-screen stretches (total 1.2s, incl. start/end)
    WARN holds  nothing moves for 16.1s at 72.5-88.6s (stall? cut the wait or add motion)
    PASS holds  65% still time across 45 hold(s)
    PASS cuts   no abrupt full-frame changes
  qa_check: overall WARN
  ```
  Both WARNs are the explained ones (4 s silent outro; small nudge reveals below freezedetect's
  threshold). Sync: every voiceover block start in the final's SRT coincides with an animation
  start (offset 0.00 s on all block starts), and speech begins 0.0-0.2 s after each. Looked at
  the `frames.py --count 8` contact sheet and at full-size 1080p frames at 24.0 s (gap label),
  48.3 s (downhill arrow), 124.4 s (backward sweep) and 143.6 s (shrinking square).
- Rubric: 20/20 (no criterion below 2).
- Assumptions: narration on (the user asked for Kokoro); voice `af_heart`, server at the skill
  default; newcomer audience, intuitive depth; length about 160 s because the request covers
  two topics (under the skill's 3-minute cap for broad prompts). Left out: activation
  functions, biases, batches, several examples, optimisers, choosing the learning rate.
- Known limitations:
  - On the number line (beats 3 and 13) the ŷ and y dots, the gap segment and the squares' bases
    sit about 0.19 units (25 px at 1080p) below the axis line instead of on it. Cause:
    `NumberLine(include_numbers=True).move_to(...)` centres line plus numbers; the points use
    the unshifted origin instead of `line.n2p()`. Horizontal positions and the square sizes are
    correct. Found on the final's full-size frame, after the iteration cap; not fixed.
  - The network is linear (no activation), so the chain-rule rates are plain numbers; said in
    the storyboard, not in the video.
