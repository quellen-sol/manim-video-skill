# Intuitiveness rubric (Step 5)

Judge the preview as a first-time viewer would: someone who knows the prerequisites in the
storyboard (by default, high-school maths) and nothing about the topic itself.

## First, the newcomer test

Watch the contact sheets in order and write, in 2 or 3 sentences, what a newcomer would take
away. Compare it with the storyboard's learning goal.

- If the takeaway matches the goal, continue.
- If it is vaguer, different, or needs knowledge the video never gave, there is a leap: find
  the beat where the viewer gets lost and fix that beat first.

## Score each criterion 0, 1 or 2

| # | Criterion | 2 (good) | 1 (partial) | 0 (bug) |
|---|---|---|---|---|
| 1 | Concrete anchor first | Opens with a familiar picture or situation | Opens with a picture, but abstract | Opens with a definition or formula |
| 2 | One idea per beat | Every beat has a single point | One or two beats carry two ideas | Beats are crowded; several ideas at once |
| 3 | Every step motivated | Each beat answers a question the last one raised | One step arrives unexplained | Steps appear without reason; a "leap" |
| 4 | Picture before formula | Each symbol labels something already seen | A formula comes slightly early | Formulas carry the explanation alone |
| 5 | Progressive reveal | The diagram is built piece by piece | Some pieces appear in bulk | The finished diagram appears at once |
| 6 | Consistent colour coding | Legend followed everywhere, including equations | One or two lapses | Colours change meaning or are decorative |
| 7 | Minimal, legible text | Short labels; motion carries meaning | Some sentences on screen | Text walls, or text too small |
| 8 | Pacing | Holds after reveals; nothing rushed or dragging | One rushed or slow stretch | Hard to follow, or long stalls |
| 9 | Payoff and recap | Ends by tying the pieces together | A recap, but it adds nothing | Ends abruptly |
| 10 | Right depth | Matches the request (intuitive by default; rigorous if asked) | Slightly too shallow or too deep | Wrong level for the audience |

**Pass:** no criterion at 0 and a total of at least 15 of 20. Fix anything at 0 before anything
else. A 1 that a small change could raise to 2 is worth fixing too.

**Geometry cap (mandatory):** if `out/report.md` shows a geometry FAIL (any GeometryGuard rule
violated, or the frame-edge rule), or the main figure has no geometry rules at all, the total is
capped at **15 of 20**, whatever the criteria above add up to. A figure that is off-centre on its
own axes or crammed against the frame edge reads as sloppy, and eyeballing contact sheets does
not catch it reliably (an earlier unit-circle video scored 19/20 with exactly that bug). Fix
the geometry and re-render before scoring above 15.

## Questions that find leaps

- Where would a newcomer ask "why?" and not get an answer within the next beat?
- Is any term used before it is shown (for example "weight", "rebase", "tangent")?
- Does any beat rely on remembering something that left the screen long ago? Bring it back.
- Would the video still make sense with the sound off (silent) or with eyes closed (narration
  carries too much)?
- Is there a single moment where the key insight lands, and is it given a pause?

## Going deeper on request

When the user asked for rigour, also check: the derivation steps are all shown (no "it can be
shown that"), assumptions and edge cases are stated, and notation is introduced once and used
consistently. The intuitive spine (criteria 1, 3, 4) still applies.
