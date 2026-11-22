# Scene patterns

Reusable building blocks for common explainer subjects. Each pattern is a complete scene that
renders as-is under Manim Community v0.22.1 when placed after this header (the same header as
`templates/scene_silent.py`):

```python
from manim import *
try:
    from manim_qa import LayoutGuard
except ImportError:
    class LayoutGuard:
        pass
config.background_color = "#0F1117"
Text.set_default(font="Noto Sans")
```

Take the structure, not the content: your storyboard decides what each beat shows.

## 1. Live geometry: a point on the unit circle drives labelled segments

`ValueTracker` holds the angle; `always_redraw` rebuilds everything that depends on it, so the
segments, the arc and the readout never fall out of step.

```python
class UnitCircleLive(LayoutGuard, Scene):
    def construct(self):
        axes = Axes(x_range=[-1.5, 1.5, 1], y_range=[-1.5, 1.5, 1], x_length=6, y_length=6,
                    tips=False, axis_config={"color": GREY_B}).shift(2.8 * LEFT)
        O = axes.c2p(0, 0)
        unit = axes.c2p(1, 0)[0] - O[0]
        circle = Circle(radius=unit, color=GREY_B).move_to(O)
        theta = ValueTracker(35 * DEGREES)

        def P():
            t = theta.get_value()
            return axes.c2p(np.cos(t), np.sin(t))

        radius = always_redraw(lambda: Line(O, P(), color=WHITE))
        sin_seg = always_redraw(lambda: Line(axes.c2p(np.cos(theta.get_value()), 0), P(),
                                             color=BLUE, stroke_width=6))
        cos_seg = always_redraw(lambda: Line(O, axes.c2p(np.cos(theta.get_value()), 0),
                                             color=RED, stroke_width=6))
        arc = always_redraw(lambda: Arc(radius=0.45, angle=theta.get_value(), arc_center=O, color=YELLOW))
        dot = always_redraw(lambda: Dot(P(), color=YELLOW))

        sin_val = DecimalNumber(0, num_decimal_places=2, color=BLUE)
        cos_val = DecimalNumber(0, num_decimal_places=2, color=RED)
        sin_val.add_updater(lambda m: m.set_value(np.sin(theta.get_value())))
        cos_val.add_updater(lambda m: m.set_value(np.cos(theta.get_value())))
        readout = VGroup(
            VGroup(MathTex(r"\sin\theta =", color=BLUE), sin_val).arrange(RIGHT, buff=0.2),
            VGroup(MathTex(r"\cos\theta =", color=RED), cos_val).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).to_edge(RIGHT, buff=1.0)

        self.play(Create(axes), Create(circle))
        self.play(Create(radius), FadeIn(dot), Create(arc))
        self.play(Create(cos_seg), Create(sin_seg))
        self.play(FadeIn(readout))
        self.wait(1)
        self.play(theta.animate.set_value(145 * DEGREES), run_time=4)
        self.wait(1)
        for m in (sin_val, cos_val):
            m.clear_updaters()
        self.play(FadeOut(VGroup(axes, circle, radius, sin_seg, cos_seg, arc, dot, readout)))
```

Notes: build the picture first (circle, radius, angle), then the segments, then the numbers.
Put the readout well away from the diagram so labels never collide as the point moves.

## 2. Equation steps with colour-matched parts

Colour each symbol the same as its picture, then step the algebra with `TransformMatchingTex`.
`{{ }}` marks the parts that should travel between steps.

```python
class EquationSteps(LayoutGuard, Scene):
    def construct(self):
        colours = {r"\sin\theta": BLUE, r"\cos\theta": RED}
        eq1 = MathTex(r"{{\sin\theta}}^2 + {{\cos\theta}}^2 = 1", font_size=56)
        eq2 = MathTex(r"{{\sin\theta}}^2 = 1 - {{\cos\theta}}^2", font_size=56)
        for eq in (eq1, eq2):
            for tex, col in colours.items():
                eq.set_color_by_tex(tex, col)
        why = Text("Pythagoras on the right triangle", font_size=30, color=GREY_B)
        why.next_to(eq1, DOWN, buff=0.6)
        self.play(Write(eq1))
        self.play(FadeIn(why, shift=0.2 * UP))
        self.wait(1.5)
        self.play(TransformMatchingTex(eq1, eq2), FadeOut(why))
        self.wait(1.5)
        self.play(FadeOut(eq2))
```

## 3. A graph drawn by a moving point (circle to wave)

```python
class CircleToWave(LayoutGuard, Scene):
    def construct(self):
        centre = 4.5 * LEFT
        circle = Circle(radius=1.2, color=GREY_B).move_to(centre)
        axes = Axes(x_range=[0, TAU, PI / 2], y_range=[-1.2, 1.2, 1], x_length=7, y_length=2.4 * 1.2,
                    tips=False, axis_config={"color": GREY_B}).shift(1.8 * RIGHT)
        t = ValueTracker(0)
        dot = always_redraw(lambda: Dot(circle.point_at_angle(t.get_value()), color=YELLOW))
        pen = always_redraw(lambda: Dot(axes.c2p(t.get_value(), np.sin(t.get_value())), color=BLUE))
        link = always_redraw(lambda: DashedLine(dot.get_center(), pen.get_center(), color=GREY_B,
                                                stroke_width=2))
        wave = always_redraw(lambda: axes.plot(np.sin, x_range=[0, max(t.get_value(), 1e-3)], color=BLUE))
        self.play(Create(circle), Create(axes))
        self.add(wave, link, dot, pen)
        self.play(t.animate.set_value(TAU), run_time=6, rate_func=linear)
        self.wait(1)
        live = VGroup(wave, link, dot, pen)
        for m in live:
            m.clear_updaters()       # freeze always_redraw objects before animating them
        self.play(FadeOut(VGroup(circle, axes, live)))
```

Always call `clear_updaters()` on `always_redraw` objects before you `FadeOut`, `Transform` or
`.animate` them; otherwise the redraw fights the animation (crashes such as
`ValueError: zip() argument 2 is shorter than argument 1`, or objects that snap back).

## 4. Boxes and arrows: a pipeline with a travelling highlight

```python
def box(label, color=BLUE, width=2.6, height=1.0):
    rect = RoundedRectangle(corner_radius=0.15, width=width, height=height, color=color,
                            fill_color=color, fill_opacity=0.15)
    return VGroup(rect, Text(label, font_size=28).move_to(rect))


class Pipeline(LayoutGuard, Scene):
    def construct(self):
        steps = VGroup(box("tokens"), box("embeddings", TEAL), box("attention", PURPLE),
                       box("next token", GREEN)).arrange(RIGHT, buff=0.7)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.08, color=GREY_B)
                          for a, b in zip(steps, steps[1:])])
        for i, s in enumerate(steps):
            self.play(FadeIn(s, shift=0.2 * RIGHT), *([GrowArrow(arrows[i - 1])] if i else []), run_time=0.8)
        self.wait(1)
        token = Dot(steps[0].get_center(), color=YELLOW, radius=0.12)
        self.play(FadeIn(token, scale=0.5))
        for s in steps[1:]:
            self.play(token.animate.move_to(s.get_center()), Indicate(s[0], color=YELLOW), run_time=0.9)
        self.wait(1)
        self.play(FadeOut(VGroup(steps, arrows, token)))
```

Width budget: n boxes of width w and n-1 gaps of b must fit in about 12.8 units
(`4 * 2.6 + 3 * 0.7 = 12.5`). Shrink the boxes or use two rows rather than letting the row clip.

## 5. Layered network: neurons, weighted edges, a forward pass

Edge width and opacity encode weight magnitude; colour encodes sign. A seeded generator keeps
renders identical between iterations.

```python
class TinyNetwork(LayoutGuard, Scene):
    def construct(self):
        sizes, xs = [3, 5, 4, 2], [-4.5, -1.5, 1.5, 4.5]
        layers = VGroup(*[
            VGroup(*[Circle(radius=0.25, color=WHITE, stroke_width=2, fill_color=BLUE_E, fill_opacity=1)
                     for _ in range(n)]).arrange(DOWN, buff=0.35).move_to(x * RIGHT)
            for n, x in zip(sizes, xs)])
        rng = np.random.default_rng(7)
        edge_layers = VGroup()
        for a, b in zip(layers, layers[1:]):
            group = VGroup()
            for u in a:
                for v in b:
                    w = rng.normal()
                    group.add(Line(u.get_center(), v.get_center(), buff=0.25,
                                   color=BLUE if w > 0 else ORANGE,
                                   stroke_width=0.5 + 2.5 * min(abs(w), 1.5),
                                   stroke_opacity=0.3 + 0.4 * min(abs(w), 1)))
            edge_layers.add(group)
        edge_layers.set_z_index(-1)
        base_y = layers.get_bottom()[1] - 0.45          # one baseline for all layer names
        names = VGroup(*[Text(t, font_size=26, color=GREY_B).move_to([l.get_x(), base_y, 0])
                         for t, l in zip(["input", "hidden", "hidden", "output"], layers)])
        self.play(LaggedStart(*[FadeIn(l, shift=0.2 * UP) for l in layers], lag_ratio=0.2))
        self.play(LaggedStart(*[Create(g) for g in edge_layers], lag_ratio=0.3), FadeIn(names))
        self.wait(1)
        for g, nxt in zip(edge_layers, layers[1:]):
            pulses = [ShowPassingFlash(e.copy().set_stroke(YELLOW, width=4, opacity=1), time_width=0.6)
                      for e in g]
            self.play(LaggedStart(*pulses, lag_ratio=0.01), run_time=1.0)
            self.play(*[n.animate.set_fill(YELLOW, opacity=float(rng.uniform(0.3, 1))) for n in nxt],
                      run_time=0.5)
        self.wait(1)
        self.play(FadeOut(VGroup(layers, edge_layers, names)))
```

To show that a layer is a matrix multiply, follow with `Matrix(...)` beside the edges and
`Indicate` one row while highlighting the matching fan-in edges of one neuron.

## 6. Commit graph: commits, branches, merge, rebase

Commits are dots on horizontal lanes; branch names are tags that move; a merge commit has two
parent edges; a rebase copies commits onto a new base (primes) while the originals fade.

```python
def commit(label, pos, color=BLUE):
    dot = Circle(radius=0.28, color=color, fill_color=color, fill_opacity=1).move_to(pos)
    text = Text(label, font_size=22, color=GREY_B).next_to(dot, DOWN, buff=0.15)
    return VGroup(dot, text)


def tag(name, target, color, direction=UP):
    label = Text(name, font_size=24, color=BLACK)
    plate = RoundedRectangle(corner_radius=0.1, width=label.width + 0.3, height=0.45,
                             fill_color=color, fill_opacity=1, stroke_width=0)
    return VGroup(plate, label).next_to(target, direction, buff=0.25)


def edge(a, b):
    return Line(a[0].get_center(), b[0].get_center(), buff=0.28, color=GREY_B, stroke_width=4)


class CommitGraph(LayoutGuard, Scene):
    def construct(self):
        main_y, feat_y = 1.0, -1.3
        c1, c2 = commit("a1", [-5, main_y, 0]), commit("a2", [-3, main_y, 0])
        main = tag("main", c2, BLUE)
        self.play(FadeIn(c1), FadeIn(c2), Create(edge(c1, c2)), FadeIn(main))
        f1 = commit("b1", [-1, feat_y, 0], GREEN)
        f2 = commit("b2", [1, feat_y, 0], GREEN)
        feat = tag("feature", f2, GREEN, DOWN).shift(0.45 * DOWN)
        self.play(Create(edge(c2, f1)), FadeIn(f1))
        self.play(Create(edge(f1, f2)), FadeIn(f2), FadeIn(feat))
        c3 = commit("a3", [1, main_y, 0])
        self.play(Create(edge(c2, c3)), FadeIn(c3), main.animate.next_to(c3, UP, buff=0.25))
        self.wait(1)
        # rebase: replay b1, b2 on top of a3 as new commits b1', b2'
        r1, r2 = commit("b1'", [3, main_y - 1.3, 0], GREEN), commit("b2'", [5, main_y - 1.3, 0], GREEN)
        e1, e2 = edge(c3, r1), edge(r1, r2)
        ghosts = VGroup(f1, f2)
        self.play(ghosts.animate.set_opacity(0.25), Create(e1), TransformFromCopy(f1, r1))
        self.play(Create(e2), TransformFromCopy(f2, r2), feat.animate.next_to(r2, DOWN, buff=0.7))
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects))
```

For merges, add a commit with two `edge` lines (one from each parent) and move the branch tag.
For conflicts, show the two versions of the same lines side by side (`Code` or `Text` panels)
with the conflicting line highlighted by a `SurroundingRectangle`, then the resolved file.

## 7. Rotating vectors (epicycles) drawing a closed shape

Sample the shape, take its discrete Fourier transform, and chain the terms from largest to
smallest. `TracedPath` draws what the tip visits.

```python
def fourier_terms(points, n_terms):
    z = points[:, 0] + 1j * points[:, 1]
    N = len(z)
    ks = np.arange(-(n_terms // 2), n_terms // 2 + 1)
    s = np.arange(N) / N
    coeffs = [(k, (z * np.exp(-2j * np.pi * k * s)).mean()) for k in ks]
    return sorted(coeffs, key=lambda kc: -abs(kc[1]))


class Epicycles(LayoutGuard, Scene):
    def construct(self):
        s = np.linspace(0, 1, 400, endpoint=False) * TAU
        heart = np.stack([16 * np.sin(s) ** 3,
                          13 * np.cos(s) - 5 * np.cos(2 * s) - 2 * np.cos(3 * s) - np.cos(4 * s)], axis=1) / 6
        terms = fourier_terms(heart, 21)
        t = ValueTracker(0)
        centre = 0.3 * UP

        def joints():
            p, pts = complex(*centre[:2]), []
            pts.append(p)
            for k, c in terms:
                p = p + c * np.exp(2j * np.pi * k * t.get_value())
                pts.append(p)
            return [np.array([q.real, q.imag, 0]) for q in pts]

        def arms():
            pts = joints()
            lines = VGroup(*[Line(a, b, color=BLUE, stroke_width=2) for a, b in zip(pts, pts[1:])])
            rings = VGroup(*[Circle(radius=np.linalg.norm(b - a), color=BLUE_E, stroke_width=1).move_to(a)
                             for a, b in zip(pts, pts[1:])])
            return VGroup(rings, lines)

        rig = always_redraw(arms)
        trail = TracedPath(lambda: joints()[-1], stroke_color=YELLOW, stroke_width=4)
        self.add(rig, trail)
        self.play(t.animate.set_value(1), run_time=8, rate_func=linear)
        self.wait(1)
        self.play(FadeOut(rig), trail.animate.set_stroke(width=6))
        self.wait(1)
```

Fewer terms make a rounder shape; show that progression (5, 11, 21 terms) to build intuition.

## 8. Gradient descent on a loss curve

The slope is drawn as a tangent; each step moves against the slope by learning rate times slope.

```python
class GradientSteps(LayoutGuard, Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3, 1], y_range=[0, 5, 1], x_length=8, y_length=5, tips=False,
                    axis_config={"color": GREY_B}).shift(0.3 * DOWN)
        loss = lambda w: 0.5 * w ** 2 + 0.3 * np.sin(2 * w) + 0.5
        dloss = lambda w: w + 0.6 * np.cos(2 * w)
        curve = axes.plot(loss, x_range=[-3, 3], color=BLUE)
        labels = axes.get_axis_labels(MathTex("w"), Text("loss", font_size=28))
        w = ValueTracker(-2.6)
        ball = always_redraw(lambda: Dot(axes.c2p(w.get_value(), loss(w.get_value())), color=YELLOW,
                                         radius=0.12))
        tangent = always_redraw(lambda: axes.plot(
            lambda x: loss(w.get_value()) + dloss(w.get_value()) * (x - w.get_value()),
            x_range=[w.get_value() - 0.8, w.get_value() + 0.8], color=ORANGE))
        self.play(Create(axes), Create(curve), FadeIn(labels))
        self.play(FadeIn(ball), Create(tangent))
        lr = 0.35
        for _ in range(6):
            self.play(w.animate.set_value(w.get_value() - lr * dloss(w.get_value())), run_time=0.8)
            self.wait(0.3)
        self.wait(1)
        self.play(FadeOut(VGroup(axes, curve, labels, ball, tangent)))
```

For backpropagation, draw the computation graph left to right with forward values in one
colour, then sweep right to left writing the local gradients in a second colour, multiplying
along each path (chain rule) before updating a weight.

## 9. Zooming in on a detail

```python
class ZoomDetail(LayoutGuard, MovingCameraScene):
    def construct(self):
        grid = VGroup(*[Square(0.6, color=BLUE, fill_opacity=0.2 + 0.05 * i) for i in range(12)])
        grid.arrange_in_grid(rows=3, cols=4, buff=0.2)
        target = grid[6]
        note = Text("one cell", font_size=14, color=YELLOW).next_to(target, DOWN, buff=0.08)
        self.play(FadeIn(grid))
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.35).move_to(target), run_time=2)
        self.play(FadeIn(note))
        self.wait(1)
        self.play(Restore(self.camera.frame), FadeOut(note), run_time=2)
        self.play(FadeOut(grid))
```

Text placed for a zoomed view (font 14 at 0.35 zoom reads like 40) becomes tiny when the camera
pulls back: fade it out before restoring.

## 10. Chapter cards and the recap

```python
class ChapterAndRecap(LayoutGuard, Scene):
    def construct(self):
        card = VGroup(Text("Chapter 2", font_size=28, color=GREY_B),
                      Text("Branching", font_size=48)).arrange(DOWN, buff=0.25)
        self.play(FadeIn(card, shift=0.3 * UP))
        self.wait(1)
        self.play(FadeOut(card, shift=0.3 * UP))
        recap = VGroup(*[Text(s, font_size=32) for s in [
            "1. A commit is a snapshot",
            "2. A branch is a movable label",
            "3. Merge joins histories; rebase replays them"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        self.play(LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in recap], lag_ratio=0.4))
        self.wait(2.5)
        self.play(FadeOut(recap))
```
