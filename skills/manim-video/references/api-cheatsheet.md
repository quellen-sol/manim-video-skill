# Manim Community v0.22.1 cheatsheet

Everything here was checked against Manim Community v0.22.1 (the Docker image
`manimcommunity/manim:v0.22.1`). Import everything with `from manim import *`.

Coordinates: the frame is 14.22 wide and 8 tall, centred on the origin. `UP`, `DOWN`, `LEFT`,
`RIGHT`, `ORIGIN`, `UL`, `UR`, `DL`, `DR`, `IN`, `OUT` are unit vectors (numpy arrays): write
`2 * RIGHT + UP`. `PI`, `TAU`, `DEGREES` (`30 * DEGREES`) are constants.

## Do not use ManimGL idioms

| ManimGL / old code (wrong here) | Manim Community |
|---|---|
| `from manimlib import *`, `from manimgl import *` | `from manim import *` |
| `ShowCreation(m)` | `Create(m)` |
| `ShowCreationThenDestruction(m)` | `ShowPassingFlash(m)` |
| `CONFIG = {"x": 1}` class dicts | `__init__` arguments, or module constants |
| `self.embed()`, `InteractiveScene` | not available headless; just `Scene` |
| `TexText("words")` | `Tex("words")` |
| `Tex("x^2")` (math mode in GL) | `MathTex("x^2")` (`Tex` is text mode here) |
| `TexMobject`, `TextMobject` | `MathTex`, `Tex` |
| `GraphScene`, `self.get_graph(f)` | `Axes(...)`, `axes.plot(f)` |
| `self.frame` (camera frame) | `MovingCameraScene` and `self.camera.frame` |
| `m.fix_in_frame()` | `self.add_fixed_in_frame_mobjects(m)` in `ThreeDScene` |
| `FadeInFrom(m, LEFT)`, `FadeOutAndShift(m, DOWN)` | `FadeIn(m, shift=RIGHT)`, `FadeOut(m, shift=DOWN)` |
| `ApplyMethod(m.shift, UP)` | `m.animate.shift(UP)` |
| `always(m.next_to, other)`, `f_always(...)` | `m.add_updater(lambda x: x.next_to(other))` |
| `self.play(m.shift, UP)` (method + args) | `self.play(m.animate.shift(UP))` |

## Scene types and config

```python
class Explainer(Scene): ...                 # 2D
class Zoom(MovingCameraScene): ...          # animate self.camera.frame
class Space(ThreeDScene): ...               # 3D camera
config.background_color = "#0F1117"         # module level, before the class
Text.set_default(font="Noto Sans")          # default font for all Text
self.next_section("chapter-2")              # names a section (optional)
self.add_sound("click.wav", time_offset=0)  # play a sound file (inside construct)
```

## Text and maths

```python
Text("Hello", font_size=36, color=BLUE)                 # Pango text, no LaTeX needed
Text("tan θ", t2c={"tan": YELLOW})                     # colour a substring
MarkupText('<span fgcolor="#58C4DD">sin</span> wave')   # Pango markup
Paragraph("line one", "line two", alignment="left", font_size=28)
MathTex(r"\sin^2\theta + \cos^2\theta = 1")             # needs LaTeX
MathTex(r"\tan\theta", "=", r"\frac{\sin\theta}{\cos\theta}")   # 3 parts: eq[0], eq[1], eq[2]
MathTex(r"{{a}}^2 + {{b}}^2 = {{c}}^2")                 # {{ }} makes isolatable parts
eq = MathTex(r"\sin\theta", "+", r"\cos\theta"); eq[0].set_color(BLUE)  # index parts
MathTex(r"y = mx + b", substrings_to_isolate=["m", "b"]).set_color_by_tex("m", YELLOW)
Tex(r"A \textbf{bold} claim")                           # LaTeX text mode
DecimalNumber(0.5, num_decimal_places=2, font_size=36)  # number that can change
Integer(3)
Title("Section title")                                  # Tex title with underline
BulletedList("first", "second", font_size=32)           # Tex bullets
Code(code_string="git commit -m 'msg'", language="bash",
     background="window", paragraph_config={"font": "Noto Mono"})
```

## Shapes, lines, arrows

```python
Dot(point, radius=0.08, color=WHITE);  LabeledDot("A")
Circle(radius=1, color=BLUE);  Ellipse(width=3, height=1.5)
Square(side_length=2);  Rectangle(width=4, height=2);  RoundedRectangle(corner_radius=0.2, width=3, height=1)
Polygon(p1, p2, p3);  RegularPolygon(n=6);  Triangle();  Star()
Arc(radius=1, start_angle=0, angle=PI / 3);  Sector(radius=1, angle=PI / 4);  Annulus(inner_radius=1, outer_radius=1.5)
Line(start, end);  DashedLine(start, end);  Arrow(start, end, buff=0);  DoubleArrow(start, end)
Vector([2, 1]);  CurvedArrow(start, end, angle=-PI / 4);  ArcBetweenPoints(start, end, angle=PI / 3)
Angle(line1, line2, radius=0.5, other_angle=False);  RightAngle(line1, line2, length=0.3)
Brace(mobject, direction=DOWN);  brace.get_text("width");  BraceLabel(mobject, r"\Delta x")
SurroundingRectangle(mobject, color=YELLOW, buff=0.1, corner_radius=0.1);  BackgroundRectangle(mobject)
Cross(mobject);  Underline(mobject)
```

Styling: `set_color`, `set_fill(color, opacity=0.5)`, `set_stroke(color, width=4, opacity=1)`,
`set_opacity`, `set_z_index(2)` (higher draws on top). Most constructors take `color`,
`fill_opacity`, `stroke_width`.

## Positioning and groups

```python
m.move_to(ORIGIN); m.shift(2 * LEFT); m.to_edge(UP, buff=0.5); m.to_corner(UL, buff=0.5)
m.next_to(other, RIGHT, buff=0.25); m.align_to(other, LEFT); m.scale(0.8); m.rotate(PI / 6)
m.get_center(); m.get_top(); m.get_left(); m.get_corner(UR); m.width; m.height
g = VGroup(a, b, c).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
VGroup(*items).arrange_in_grid(rows=2, cols=3, buff=0.5)
Group(image, text)   # use Group (not VGroup) when it holds an ImageMobject
m.copy(); m.become(other); m.match_width(other); m.scale_to_fit_width(6)
```

## Graphs, axes, planes

```python
axes = Axes(x_range=[-1, 7, 1], y_range=[-1.5, 1.5, 0.5], x_length=9, y_length=4,
            axis_config={"include_numbers": False, "color": GREY_B}, tips=False)
labels = axes.get_axis_labels(x_label="x", y_label="y")      # MathTex labels
sine = axes.plot(lambda x: np.sin(x), x_range=[0, TAU], color=BLUE)
axes.c2p(1, 0.5)                    # coords -> scene point;  axes.p2c(point)
axes.get_graph_label(sine, label=r"\sin x", x_val=2, direction=UP)
axes.get_vertical_line(axes.c2p(2, np.sin(2)))
axes.get_area(sine, x_range=[0, PI], color=BLUE, opacity=0.3)
axes.get_riemann_rectangles(sine, x_range=[0, PI], dx=0.25)
NumberPlane(background_line_style={"stroke_opacity": 0.4})
NumberLine(x_range=[0, 10, 1], length=10, include_numbers=True)
ParametricFunction(lambda t: np.array([np.cos(t), np.sin(t), 0]), t_range=[0, TAU])
FunctionGraph(lambda x: x ** 2, x_range=[-2, 2])
Graph(vertices, edges, layout="circular", labels=True)   # network diagrams (uses networkx)
Table([["1", "2"], ["3", "4"]], col_labels=[Text("a"), Text("b")])
Matrix([[1, 0], [0, 1]])
```

`np` is available after `from manim import *` (numpy).

## Animations

```python
self.play(Create(m))                 # draw strokes;  Uncreate(m)
self.play(Write(text))               # handwriting for text/maths;  Unwrite(text)
self.play(FadeIn(m, shift=UP, scale=0.8));  self.play(FadeOut(m, shift=DOWN))
self.play(DrawBorderThenFill(shape));  self.play(GrowFromCenter(m));  self.play(GrowArrow(arrow))
self.play(SpinInFromNothing(m));  self.play(GrowFromPoint(m, point))
self.play(Transform(a, b))           # a morphs into b's shape; keep using a
self.play(ReplacementTransform(a, b))  # a is replaced by b; keep using b
self.play(TransformMatchingTex(eq1, eq2))      # equation steps; matches equal parts
self.play(TransformMatchingShapes(t1, t2))     # rearrange letters/shapes
self.play(FadeTransform(a, b))       # crossfade between different-looking objects
self.play(m.animate.shift(RIGHT).set_color(RED))   # animate any method chain
self.play(m.animate(run_time=2, rate_func=smooth).scale(2))
self.play(Rotate(m, angle=PI / 2, about_point=ORIGIN))
self.play(MoveAlongPath(dot, path));  self.play(Indicate(m));  self.play(Circumscribe(m))
self.play(Flash(point));  self.play(Wiggle(m));  self.play(FocusOn(point));  self.play(ShowPassingFlash(m.copy()))
self.play(ApplyWave(m));  self.play(Broadcast(Circle()))
self.play(LaggedStart(*[FadeIn(x) for x in items], lag_ratio=0.2))
self.play(AnimationGroup(a1, a2, lag_ratio=0.5));  self.play(Succession(a1, a2))
self.play(AddTextLetterByLetter(Text("typing")))
self.play(ChangeDecimalToValue(number, 3.14))
self.wait(1.5)
```

Options on any animation: `run_time=2`, `rate_func=linear | smooth | there_and_back | rush_into
| rush_from | double_smooth`, `lag_ratio`. `self.play(a, b)` runs animations together.
Do not animate the same mobject in two animations of one `play` call.

## Updaters, ValueTracker, always_redraw

```python
theta = ValueTracker(30 * DEGREES)
dot = always_redraw(lambda: Dot(circle.point_at_angle(theta.get_value()), color=YELLOW))
radius = always_redraw(lambda: Line(ORIGIN, dot.get_center(), color=BLUE))
value = always_redraw(lambda: DecimalNumber(np.sin(theta.get_value())).next_to(dot, UR, buff=0.1))
self.add(radius, dot, value)
self.play(theta.animate.set_value(150 * DEGREES), run_time=3)
label.add_updater(lambda m: m.next_to(dot, UP, buff=0.15))   # follow another object
label.clear_updaters()                                         # stop following
trail = TracedPath(dot.get_center, stroke_color=YELLOW, stroke_width=3)  # path drawn by a point
m.add_updater(lambda m, dt: m.rotate(dt * 0.5))                # time-based motion
```

Updaters run every frame, including during `self.wait()`. A redrawn object is rebuilt from
scratch each frame: give it its colour inside the lambda. Remove redrawn objects (or call
`clear_updaters()`) when the beat ends; otherwise they keep running and can reappear.

## Camera: MovingCameraScene and ZoomedScene

```python
class Zoom(MovingCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.5).move_to(target))   # zoom in on target
        self.play(Restore(self.camera.frame))                             # zoom back out
```

Text sizes scale with the zoom: a label that is readable at full frame is twice as large when
the frame is scaled by 0.5. `manim_qa.LayoutGuard` checks against the moving frame.

## ThreeDScene

```python
class Space(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
        axes = ThreeDAxes(x_range=[-3, 3], y_range=[-3, 3], z_range=[-2, 2])
        surface = Surface(lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
                          u_range=[-3, 3], v_range=[-3, 3], resolution=(24, 24))
        title = Text("A surface", font_size=36).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)     # 2D overlay that ignores the camera
        self.play(Create(axes), Create(surface))
        self.begin_ambient_camera_rotation(rate=0.2); self.wait(3); self.stop_ambient_camera_rotation()
        self.move_camera(phi=45 * DEGREES, theta=30 * DEGREES, run_time=2)
```

Also `Sphere`, `Cube`, `Prism`, `Cylinder`, `Cone`, `Arrow3D`, `Line3D`, `Dot3D`. 3D renders
are much slower with Cairo; keep `Surface` resolution modest.

## Colours

Named: `BLUE #58C4DD`, `TEAL #5CD0B3`, `GREEN #83C167`, `YELLOW #F7D96F`, `GOLD #F0AC5F`,
`ORANGE #FF862F`, `RED #FC6255`, `MAROON #C55F73`, `PURPLE #9A72AC`, `PINK #D147BD`,
`GREY #888888`, `GREY_B #BBBBBB`, `DARK_GREY #444444`, `WHITE`, `BLACK`. Shades: `BLUE_A`
(lightest) to `BLUE_E` (darkest), same for the others. Hex strings work anywhere a colour does.
`interpolate_color(BLUE, RED, 0.3)`, `ManimColor("#123456")`, `color_gradient([BLUE, GREEN], 5)`.

## Gotchas

- `Text` is Pango (no LaTeX); `Tex`/`MathTex` need LaTeX and use raw strings `r"..."`.
- `MathTex` splits only where you split the strings (or use `{{ }}`); `eq[1]` is the second part.
- `Write` on long text takes longer by default; pass `run_time`.
- `FadeOut(*self.mobjects)` clears the stage; updater-driven objects come back unless removed.
- `Uncreate(m)` leaves `m` collapsed to zero size: to show it again, create a new object
  (or keep a `copy()` made before). `FadeOut` restores the object, so it can be faded back in.
- `self.add(m)` shows instantly (a pop-in). Prefer an animation unless an instant cut is intended.
- `Group` for mixed raster and vector content; `VGroup` only for vector mobjects.
- `Arrow(buff=0.25)` by default leaves a gap at both ends; `buff=0` to touch the points.
- `next_to` places by bounding box; rotated or curved objects can still touch. Check the stills.
