# Storyboard: Six trig functions on one unit circle

- **Request:** "show a unit circle animation, with its relations to sin, cos, tan, sec, csc, and cot."
- **Learning goal:** "All six trig functions are lengths in one picture: the point on the unit
  circle is (cos θ, sin θ); the tangent line at that point is cut by the axes into tan θ and cot θ,
  and the distances from the centre to those crossings are sec θ and csc θ. Similar triangles give
  tan = sin/cos, sec = 1/cos, cot = cos/sin, csc = 1/sin, and tan and sec blow up near 90°."
- **Audience and depth:** newcomer with high-school maths (right triangles, Pythagoras), intuitive (default).
- **Narration:** silent (default; the user could not be asked).
- **Target length:** about 120 s (final: 140 s, see review.md).
- **Left out on purpose:** signs of the functions in the other three quadrants (the six-length
  picture is drawn in the first quadrant only), radians, the graphs of the functions,
  1 + tan² = sec² and 1 + cot² = csc², the etymology of the names, inverse functions.

## Colour legend

| Concept | Colour | Used for |
|---|---|---|
| sine | BLUE `#58C4DD` | vertical leg Q to P, sin label, sin in every formula and readout |
| cosine | RED `#FC6255` | horizontal leg O to Q, cos label, cos in formulas |
| tangent | YELLOW `#F7D96F` | tangent-line piece P to the x-axis, tan label, tan in formulas (so yellow is NOT used as the emphasis colour in this video) |
| secant | GREEN `#83C167` | dimension line O to E under the x-axis, sec label, sec in formulas |
| cotangent | PURPLE_A `#CAA3E8` | tangent-line piece P to the y-axis, cot label, cot in formulas |
| cosecant | ORANGE `#FF862F` | segment O to F on the y-axis, csc label, csc in formulas |
| radius 1, angle θ, point | WHITE | radius, its "1", the angle arc and θ, the moving dot |
| scaffolding | GREY_B | axes, circle, tangent line, dashed helpers |

Six concept colours is one more than the style guide's "4 or 5 on screen at once"; the request
itself asks for six functions in one picture, so this is deliberate. Labels always name each
colour, so no difference is carried by colour alone.

## Beats

One idea per beat. Each beat answers a question raised by the one before. θ rests at 55°.

| # | Time (s) | The one idea | Visual metaphor and what appears / leaves | On-screen text (short) |
|---|---|---|---|---|
| 1 | 0-9 | A circle of radius 1 | axes and circle draw; radius with "1"; the dot runs once around | "A circle of radius 1" |
| 2 | 9-14 | The point is set by an angle | radius turns from 0° to 55°; arc and θ appear | "Turn by an angle" |
| 3 | 14-19 | cos θ is how far across | dashed drop from the point; red leg grows O to Q; label | "How far across?" |
| 4 | 19-26 | sin θ is how far up; point = (cos θ, sin θ) | blue leg grows Q to P; label; coordinates beside the point | "How far up?" |
| 5 | 26-39 | They change with the angle | labels fade; live readouts in the panel; θ sweeps 55° to 80° to 20° to 55°; labels return | "Move the point" |
| 6 | 39-45 | Pythagoras: sin² + cos² = 1 | the triangle fills; identity written in the panel | "A right triangle, long side 1" |
| 7 | 45-51 | The tangent line at the point | coordinates leave; axes extend; line touching the circle; right-angle mark | "Four more, on one line" |
| 8 | 51-55 | tan θ is the piece down to the x-axis | yellow piece P to E; label | "Along it, to the x-axis" |
| 9 | 55-59 | sec θ is centre to that crossing | green dimension line O to E with a dashed tie at E; label | "Centre to that crossing" |
| 10 | 59-63 | cot θ is the piece up to the y-axis | purple piece P to F; label | "Same line, other axis" |
| 11 | 63-68 | csc θ is centre to that crossing | orange segment O to F; label | "Centre to that crossing" |
| 12 | 68-80 | tan = sin/cos, sec = 1/cos | copy of the small triangle flips onto the big one and scales by 1/cos θ: sin side lands on tan, 1 lands on sec; two formulas written | "Same shape, just bigger" / "Stretch until cos θ is 1" |
| 13 | 80-93 | cot = cos/sin, csc = 1/sin | copy turns 180° (sin now on the y-axis), flips, scales by 1/sin θ onto the upper triangle; two formulas | "Same trick, other axis" / "Stretch until sin θ is 1" |
| 14 | 93-113 | Near 90° tan, sec blow up; near 0° cot, csc do | panel and labels leave; picture zooms out; live readouts of all six; θ sweeps to 80°, then 20°, back to 55°; zoom back | "Toward 90°" then "θ → 90°: tan θ, sec θ → ∞"; "Toward 0°" then "θ → 0°: cot θ, csc θ → ∞" |
| 15 | 113-124 | Recap: six lengths, one picture | all labels and formulas back; pairs light up in turn (segments flash, labels pulse, their formulas boxed); hold; fade out | "Six lengths, one circle" |

## Layout sketch

- Diagram on the left: origin O at (-3.8, -0.8), radius 2.5 scene units; the circle spans x -6.3 to -1.3,
  y -3.3 to 1.7. At 55°: E (x-axis crossing) at x ≈ 0.56, F (y-axis crossing) at y ≈ 2.25.
- Side panel from x = 1.7 to 6.4: caption at the top (y ≈ 3.0), formulas or live readouts below.
- Labels: cos below its leg; sin right of its leg near the bottom; tan and cot on the outer side
  of the tangent line; sec at the right end of a dimension line 0.7 below the x-axis (cos and sec
  would otherwise overlap on the axis); csc left of the y-axis.
- Final sweep: diagram shrinks to radius 1.4 at (-4.6, -1.6) so the long segments fit; readouts
  top-right, out of the line's path.

## Open questions for the user (if any)

- Narration (could not be asked; silent default used).
