# Storyboard: Drawing with spinning arrows (Fourier epicycles)

- **Request:** "Show the Fourier series as rotating circles (epicycles) drawing a shape."
- **Learning goal:** a drawing can be made by chaining spinning arrows tip to tail, each with
  its own length and whole-number speed; big slow arrows give the rough shape, small fast ones
  add detail, so more arrows give a sharper drawing, and that sum is a Fourier series.
- **Audience and depth:** newcomer with high-school maths, intuitive (default). No complex
  numbers needed to follow; the formula only arrives at the end as a label for what was seen.
- **Narration:** silent (the user's answer).
- **Target length:** about 120 s.
- **Left out on purpose:** how the arrow lengths and start angles are computed from the shape
  (the averaging integral / DFT), complex-number algebra, convergence and the Gibbs overshoot at
  corners, the k = 0 (fixed centre) term beyond "the chain starts at the shape's centre".

## Colour legend

| Concept | Colour | Used for |
|---|---|---|
| Arrow (one term), already in the chain | BLUE | arrow, its circle (faint), `c_k` and "arrow" in equations |
| Arrow just added in this step | ORANGE | new arrows and their circles; they turn BLUE at the next step |
| The pen and its drawing | YELLOW | pen dot at the chain's tip, the traced curve (legend meaning, not just "look here") |
| The target shape | GREY_B (dim) | the lightning bolt we try to draw, and its copy in the thumbnails |
| Pivot, scaffolding | GREY_B | centre dot, thumbnail frames |
| Captions and labels | WHITE (or the concept colour when naming that concept) | |

## Beats

One idea per beat. Each beat answers a question raised by the one before.

| # | Time (s) | The one idea | Visual metaphor and what appears / leaves | On-screen text (short) |
|---|---|---|---|---|
| 1 | 0-4 | Hook: we will draw with circles | Title, subtitle; fade out | "Drawing with spinning arrows" / "the Fourier series" |
| 2 | 4-16 | One spinning arrow draws a circle | Pivot dot, BLUE arrow grows, yellow pen at its tip; one turn (4 s) traces a circle; the trace becomes the arrow's faint circle | "One spinning arrow" -> "Its tip draws a circle" |
| 3 | 16-28 | Each arrow has a length and a speed | Blue rig slides left; a short ORANGE arrow appears on the right; both spin for one loop: blue 1 turn, orange 2 turns backwards | "Each arrow: a length and a speed"; labels "1 turn", "2 turns, backwards" |
| 4 | 28-42 | Add arrows tip to tail | Orange arrow's tail slides onto the blue tip; its circle rides on the blue circle; pen at the orange tip traces a rounded triangle over one loop | "Add them: tip to tail" -> "Circle on circle: a new shape" |
| 5 | 42-54 | Many arrows chain the same way | Orange turns blue; three smaller faster ORANGE arrows grow at the end; one loop draws a fancier closed curve | "Chain more arrows" |
| 6 | 54-60 | Question: can we aim for a shape? | Stage clears; dim lightning bolt appears at stage left | "Which arrows draw this?" |
| 7 | 60-70 | 1 arrow: just a circle | Fourier's biggest arrow (blue) spins once; pen draws a circle around the bolt; result shrinks into thumbnail 1 (right panel) | "1 arrow: a circle" |
| 8 | 70-81 | 3 arrows: a rough blob | 2 new ORANGE arrows grow; one loop; thumbnail 2 | "3 arrows: a rough blob" |
| 9 | 81-94 | 10 arrows: smaller, faster arrows add detail | 7 new ORANGE (small, fast) arrows; one loop (8 s); thumbnail 3 | "10 arrows: detail appears" |
| 10 | 94-110 | 50 arrows: sharp corners | 40 more tiny fast arrows; slow loop (10 s); thumbnail 4 | "50 arrows: sharp corners" |
| 11 | 110-118 | Recap: more arrows, sharper drawing | Rig and bolt leave; thumbnails grow into one row with counts | "More arrows, sharper drawing" |
| 12 | 118-130 | Name it: this sum is a Fourier series | Row moves up; "pen = arrow + arrow + arrow + ..." becomes "pen(t) = sum c_k e^{ikt}", braces: c_k "an arrow", e^{ikt} "spins k turns per loop"; hold, fade out | "This sum is a Fourier series" |

## Layout sketch

- Title band (y 2.7 to 3.4): one caption per beat, font 40, centred.
- Beats 2-5: chain centred at (0, -0.4); longest arrow 1.9, so the rig stays inside y -3.0 to 2.2.
- Beats 6-10: bolt (4.6 tall) at stage left, centre (-2.8, -0.45); its rig stays inside x -4.7
  to -0.9. Right panel x 1.0 to 6.4: a 2 x 2 grid of thumbnails with count labels.
- Beat 11-12: thumbnails as a row across the frame (y about 0.9 in beat 12), formula below.

## Open questions for the user (if any)

- None (unattended test run; silent was answered).

## Changes made in this run (container route)

- Beat 3: the two arrows and their labels sit at y -0.075 (not -0.4), so the pair with its labels
  is centred on the stage; the chain slides back to (0, -0.4) for tip to tail.
- Beats 7-10: the result's thumbnail appears in its panel slot (no flight across the panel); slots
  at y 1.25 and -1.65, so the complete panel is centred in its zone (x 1.0 to 6.4).
- Captions swap in two steps (old out, then new in), never overlapping.
- Geometry rules (geometry_qa): see review.md, iteration 3.
