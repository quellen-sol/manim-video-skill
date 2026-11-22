"""Drawing with spinning arrows: arrows chained tip to tail, each spinning a whole number of
turns per loop, draw a shape; more arrows give a sharper drawing; that sum is a Fourier series.

Render: "$SKILL_DIR/scripts/render.sh" preview scene.py Explainer
"""

from manim import *

try:  # layout checker; on PYTHONPATH when rendered with render.sh
    from manim_qa import LayoutGuard
except ImportError:  # keeps the file renderable without the skill
    class LayoutGuard:
        pass

# --- style (references/style-guide.md) -----------------------------------------------
config.background_color = "#0F1117"
Text.set_default(font="Noto Sans")
MarkupText.set_default(font="Noto Sans")

# --- colour legend (storyboard.md) ----------------------------------------------------
C_ARROW = BLUE      # an arrow (one term) that is part of the chain
C_NEW = ORANGE      # arrows added in this step (turn blue at the next step)
C_PEN = YELLOW      # the pen and the curve it draws
C_TARGET = GREY_B   # the shape we aim for (dim)
C_MUTED = GREY_B    # pivot, scaffolding

TITLE_SIZE = 44
CAPTION_SIZE = 40
LABEL_SIZE = 30
SMALL_SIZE = 28
FORMULA_SIZE = 52

SAMPLES = 1600          # pen-path points per loop: smooth at any frame rate
CENTRE = np.array([0.0, -0.4, 0.0])               # stage centre for beats 2-5
BOLT_ORIGIN = np.array([-2.8, -0.45, 0.0])        # where the target shape sits
BOLT = [(-0.2, 2.3), (1.2, 2.3), (0.3, 0.6), (1.3, 0.6),
        (-0.9, -2.3), (-0.1, -0.2), (-1.1, -0.2)][::-1]   # counter-clockwise
PASSES = [  # (arrows in total, caption, loop seconds)
    (1, "Biggest arrow alone: a circle", 5),
    (3, "3 biggest arrows: a rough blob", 6),
    (10, "10 arrows: small fast ones add detail", 8),
    (50, "50 arrows: sharp corners", 10),
]
THUMB_SCALE = 0.4
SLOTS = [np.array([2.4, 1.15, 0]), np.array([5.0, 1.15, 0]),
         np.array([2.4, -1.75, 0]), np.array([5.0, -1.75, 0])]


def p3(z):
    return np.array([z.real, z.imag, 0.0])


def lagged(i, n, lag=0.5):
    """Rate function for item i of n, staggered like LaggedStart (without its wrapper Group)."""
    span = 1.0 / (1 + lag * (n - 1)) if n > 1 else 1.0
    start = i * lag * span
    return lambda a: smooth(min(1.0, max(0.0, (a - start) / span)))


def sample_polygon(verts, n):
    """n points spaced evenly along the closed polygon (so the pen moves at constant speed)."""
    v = np.array([complex(x, y) for x, y in verts] + [complex(*verts[0])])
    seg = np.abs(np.diff(v))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    d = np.linspace(0, cum[-1], n, endpoint=False)
    i = np.searchsorted(cum, d, side="right") - 1
    return v[i] + (v[i + 1] - v[i]) * ((d - cum[i]) / seg[i])


def fourier_terms(z, n_terms, k_max=80):
    """Centre (k = 0) and the n_terms largest arrows (k, c_k), biggest first."""
    s = np.arange(len(z)) / len(z)
    terms = [(k, (z * np.exp(-2j * np.pi * k * s)).mean())
             for k in range(-k_max, k_max + 1) if k != 0]
    terms.sort(key=lambda kc: (-abs(kc[1]), abs(kc[0]), kc[0]))
    return z.mean(), terms[:n_terms]


class Term:
    """One spinning arrow: c (length and start angle, complex) turning k times per loop."""

    def __init__(self, k, c, color=C_ARROW, grow=1.0):
        self.k, self.c, self.color = k, complex(c), color
        self.grow = ValueTracker(grow)    # 0 -> 1 grows the arrow out of the previous tip
        self.blend = ValueTracker(0.0)    # 0 -> 1 turns a new (orange) arrow blue

    def colour(self):
        return interpolate_color(self.color, C_ARROW, self.blend.get_value())

    def vec(self, t):
        return self.c * self.grow.get_value() * np.exp(2j * np.pi * self.k * t)


class Chain:
    """Arrows tip to tail from a pivot; t (0 -> 1) is one loop."""

    def __init__(self, anchor, terms, t):
        self.ax, self.ay = ValueTracker(anchor[0]), ValueTracker(anchor[1])
        self.terms = list(terms)
        self.t = t
        self.alpha = ValueTracker(1.0)        # whole rig
        self.ring_alpha = ValueTracker(1.0)   # the faint circles
        self.pen_alpha = ValueTracker(1.0)    # the yellow pen dot
        self.pivot_alpha = ValueTracker(1.0)

    def anchor(self):
        return complex(self.ax.get_value(), self.ay.get_value())

    def joints(self):
        t = self.t.get_value()
        pts = [self.anchor()]
        for term in self.terms:
            pts.append(pts[-1] + term.vec(t))
        return pts

    def build(self):
        a = self.alpha.get_value()
        pts = self.joints()
        rings, arrows = VGroup(), VGroup()
        for term, z0, z1 in zip(self.terms, pts, pts[1:]):
            r = abs(z1 - z0)
            if r < 0.004:
                continue
            col = term.colour()
            rings.add(Circle(radius=r, stroke_color=col, stroke_width=1.5,
                             stroke_opacity=0.45 * a * self.ring_alpha.get_value()).move_to(p3(z0)))
            arrows.add(Arrow(p3(z0), p3(z1), buff=0, color=col, stroke_width=4, tip_length=0.22,
                             max_tip_length_to_length_ratio=0.3).set_opacity(a))
        pivot = Dot(p3(pts[0]), radius=0.06, color=C_MUTED).set_opacity(a * self.pivot_alpha.get_value())
        pen = Dot(p3(pts[-1]), radius=0.07, color=C_PEN).set_opacity(a * self.pen_alpha.get_value())
        return VGroup(rings, arrows, pivot, pen).set_z_index(2)

    def rig(self):
        return always_redraw(self.build)

    def curve(self, t_end, width=4):
        """The pen's path from the start of the loop to t_end, computed exactly."""
        path = VMobject(stroke_color=C_PEN, stroke_width=width).set_z_index(1)
        if t_end <= 1e-4:
            return path
        s = np.linspace(0, t_end, max(2, int(SAMPLES * t_end) + 1))
        z = np.full(len(s), self.anchor(), dtype=complex)
        for term in self.terms:
            z += term.c * term.grow.get_value() * np.exp(2j * np.pi * term.k * s)
        return path.set_points_as_corners(np.stack([z.real, z.imag, np.zeros(len(s))], axis=1))

    def trace(self):
        return always_redraw(lambda: self.curve(self.t.get_value()))


class Explainer(LayoutGuard, Scene):
    def construct(self):
        self.cap = None
        self.beat_title()
        self.beat_one_arrow()
        self.beat_length_and_speed()
        self.beat_tip_to_tail()
        self.beat_more_arrows()
        self.beat_target()
        self.beat_passes()
        self.beat_recap()
        self.beat_formula()

    # --- helpers ------------------------------------------------------------------------
    def caption(self, text, run_time=0.9):
        new = Text(text, font_size=CAPTION_SIZE).to_edge(UP, buff=0.6)
        if self.cap is None:
            self.play(FadeIn(new, shift=0.15 * DOWN), run_time=run_time)
        else:  # old caption leaves first, so the two never sit on top of each other
            self.play(AnimationGroup(FadeOut(self.cap, shift=0.15 * UP), FadeIn(new, shift=0.15 * DOWN),
                                     lag_ratio=0.6), run_time=run_time)
        self.cap = new

    def grow(self, terms, run_time=1.5, extra=()):
        """Grow new arrows out of the chain's tip one after another."""
        n = len(terms)
        self.play(*extra, *[x.grow.animate(rate_func=lagged(i, n, min(0.5, 2.0 / n))).set_value(1)
                            for i, x in enumerate(terms)], run_time=run_time)

    def freeze(self, chain, trace):
        """Swap the live trace for a static copy and rewind the loop (same picture at t=0 and 1)."""
        static = chain.curve(1.0)
        self.add(static)
        self.remove(trace)
        chain.t.set_value(0)
        return static

    def run_loop(self, chain, seconds):
        trace = chain.trace()
        self.add(trace)
        self.play(chain.t.animate.set_value(1), run_time=seconds, rate_func=linear)
        return trace

    # --- beats --------------------------------------------------------------------------
    def beat_title(self):
        """Beat 1: hook."""
        title = Text("Drawing with spinning arrows", font_size=TITLE_SIZE)
        sub = Text("the Fourier series", font_size=LABEL_SIZE, color=C_MUTED)
        VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(sub, shift=0.2 * UP))
        self.wait(1.5)
        self.play(FadeOut(title, sub))

    def beat_one_arrow(self):
        """Beat 2: one spinning arrow; its tip draws a circle."""
        self.t = ValueTracker(0)
        self.term1 = Term(1, 1.9, C_ARROW, grow=0)
        ch = self.chain = Chain(CENTRE, [self.term1], self.t)
        ch.alpha.set_value(0)
        ch.ring_alpha.set_value(0)
        ch.pen_alpha.set_value(0)
        self.rig = ch.rig()
        self.add(self.rig)
        self.caption("One spinning arrow")
        self.play(ch.alpha.animate.set_value(1), self.term1.grow.animate.set_value(1), run_time=1.2)
        self.play(ch.pen_alpha.animate.set_value(1), run_time=0.5)
        self.wait(0.5)
        trace = self.run_loop(ch, 4)
        self.caption("Its tip draws a circle")
        self.wait(1)
        static = self.freeze(ch, trace)
        # the drawn circle becomes the arrow's own faint circle
        self.play(FadeOut(static), ch.ring_alpha.animate.set_value(1), run_time=1)
        self.wait(0.5)

    def beat_length_and_speed(self):
        """Beat 3: each arrow has a length and a speed (turns per loop)."""
        ch = self.chain
        self.term2 = Term(-2, 0.7, C_NEW, grow=0)
        ch2 = self.chain2 = Chain(np.array([3.2, -0.4, 0]), [self.term2], self.t)
        ch2.alpha.set_value(0)
        ch2.pen_alpha.set_value(0)
        self.rig2 = ch2.rig()
        self.add(self.rig2)
        self.caption("Each arrow: a length and a speed")
        self.play(ch.ax.animate.set_value(-3.2), ch.pen_alpha.animate.set_value(0), run_time=1.2)
        self.play(ch2.alpha.animate.set_value(1), self.term2.grow.animate.set_value(1), run_time=1)
        lab1 = Text("1 turn", font_size=LABEL_SIZE, color=C_ARROW)
        lab1.next_to(np.array([-3.2, -0.4 - 1.9, 0]), DOWN, buff=0.35)
        lab2 = Text("2 turns, backwards", font_size=LABEL_SIZE, color=C_NEW)
        lab2.next_to(np.array([3.2, -0.4 - 0.7, 0]), DOWN, buff=0.35)
        self.play(FadeIn(lab1, shift=0.1 * UP), FadeIn(lab2, shift=0.1 * UP), run_time=0.8)
        self.wait(0.5)
        self.play(self.t.animate.set_value(1), run_time=5, rate_func=linear)
        self.t.set_value(0)
        self.wait(1)
        self.labels = VGroup(lab1, lab2)

    def beat_tip_to_tail(self):
        """Beat 4: add the arrows tip to tail; the pen draws a new shape."""
        ch, ch2 = self.chain, self.chain2
        self.caption("Add them: tip to tail")
        self.play(FadeOut(self.labels), run_time=0.6)
        self.play(ch.ax.animate.set_value(CENTRE[0]), ch2.ax.animate.set_value(CENTRE[0] + 1.9),
                  ch2.pivot_alpha.animate.set_value(0), run_time=1.5)
        # merge: the orange arrow is now the second link of the blue chain (same picture)
        self.remove(self.rig2)
        ch.terms.append(self.term2)
        self.play(ch.pen_alpha.animate.set_value(1), run_time=0.5)
        self.wait(0.5)
        self.trace = self.run_loop(ch, 6)
        self.caption("Circle on circle: a new shape")
        self.wait(1.5)

    def beat_more_arrows(self):
        """Beat 5: chain more, smaller, faster arrows: a fancier closed curve."""
        ch = self.chain
        static = self.freeze(ch, self.trace)
        self.caption("Keep chaining arrows")
        new = [Term(3, 0.4, C_NEW, 0), Term(-5, 0.25, C_NEW, 0), Term(7, 0.15, C_NEW, 0)]
        ch.terms += new
        self.play(FadeOut(static), self.term2.blend.animate.set_value(1), run_time=0.8)
        self.grow(new)
        self.wait(0.5)
        self.trace = self.run_loop(ch, 7)
        self.wait(1.5)

    def beat_target(self):
        """Beat 6: the question: which arrows draw a shape we choose?"""
        ch = self.chain
        static = self.freeze(ch, self.trace)
        self.play(ch.alpha.animate.set_value(0), FadeOut(static), run_time=1)
        self.remove(self.rig)
        self.bolt = Polygon(*[BOLT_ORIGIN + np.array([x, y, 0]) for x, y in BOLT],
                            color=C_TARGET, stroke_width=3, stroke_opacity=0.6)
        self.caption("Which arrows draw this?")
        self.play(Create(self.bolt), run_time=1.5)
        self.wait(1.5)
        self.caption("Fourier's recipe gives the arrows")
        self.wait(2)

    def beat_passes(self):
        """Beats 7-10: Fourier's arrows for the bolt, 1, 3, 10, then 50 of them."""
        centre, terms = fourier_terms(sample_polygon(BOLT, 2000), PASSES[-1][0])
        self.all_terms = [Term(k, c, C_ARROW, 0) for k, c in terms]
        self.t = ValueTracker(0)
        ch = self.chain = Chain(BOLT_ORIGIN + p3(centre), [], self.t)
        ch.alpha.set_value(0)
        self.rig = ch.rig()
        self.add(self.rig)
        self.thumbs, self.thumb_labels = VGroup(), VGroup()
        for i, (n, text, seconds) in enumerate(PASSES):
            old = list(ch.terms)
            new = self.all_terms[len(old):n]
            for x in new:
                x.color = C_NEW if old else C_ARROW
            self.caption(text)
            ch.terms += new
            first = [ch.alpha.animate.set_value(1)] if not old else []
            recolour = [x.blend.animate.set_value(1) for x in old if x.color == C_NEW]
            self.grow(new, extra=first + recolour)
            self.wait(0.5)
            trace = self.run_loop(ch, seconds)
            self.wait(1)
            static = self.freeze(ch, trace)
            # a copy of the result shrinks into the side panel
            thumb = VGroup(self.bolt.copy(), static.copy())
            target = thumb.copy().scale(THUMB_SCALE, about_point=self.bolt.get_center())
            target.shift(SLOTS[i] - self.bolt.get_center())
            target[0].set_stroke(width=2)
            target[1].set_stroke(width=3)
            label = Text(f"{n} arrow" + ("s" if n > 1 else ""), font_size=SMALL_SIZE)
            label.move_to(SLOTS[i] + 1.25 * DOWN)
            self.add(thumb)
            self.play(Transform(thumb, target), FadeOut(static), FadeIn(label), run_time=1.2)
            self.thumbs.add(thumb)
            self.thumb_labels.add(label)
            self.wait(0.5)

    def beat_recap(self):
        """Beat 11: more arrows, sharper drawing."""
        ch = self.chain
        self.play(ch.alpha.animate.set_value(0), FadeOut(self.bolt), run_time=1)
        self.remove(self.rig)
        self.caption("More arrows, sharper drawing")
        xs = [-4.65, -1.55, 1.55, 4.65]
        moves = []
        for thumb, label, x in zip(self.thumbs, self.thumb_labels, xs):
            centre = thumb[0].get_center()
            target = thumb.copy().scale(1.6, about_point=centre).shift(np.array([x, -0.1, 0]) - centre)
            moves.append(AnimationGroup(Transform(thumb, target),
                                        label.animate.move_to(np.array([x, -2.2, 0]))))
        # one after another, so the thumbnails never cross on their way
        self.play(LaggedStart(*moves, lag_ratio=0.3), run_time=2.4)
        self.wait(2.5)

    def beat_formula(self):
        """Beat 12: name it: the sum of spinning arrows is a Fourier series."""
        self.caption("This sum is a Fourier series")
        self.play(FadeOut(self.thumb_labels), self.thumbs.animate.scale(0.7).move_to(1.35 * UP),
                  run_time=1.2)
        # line 1: the picture in words (tip to tail = adding)
        f1 = MathTex(r"\text{pen}", "=", r"\text{arrow}_1", "+", r"\text{arrow}_2", "+",
                     r"\text{arrow}_3", "+", r"\cdots", font_size=FORMULA_SIZE)
        f1[0].set_color(C_PEN)
        for i in (2, 4, 6):
            f1[i].set_color(C_ARROW)
        f1.move_to(0.45 * DOWN)
        self.play(Write(f1), run_time=2)
        self.wait(1.5)
        # line 2: the same sum in Fourier's notation, "=" under "="
        f2 = MathTex("=", r"\sum_{k}", r"c_k", r"\, e^{ikt}", font_size=FORMULA_SIZE)
        f2[2].set_color(C_ARROW)
        f2.next_to(f1, DOWN, buff=0.45)
        f2.shift((f1[1].get_center()[0] - f2[0].get_center()[0]) * RIGHT)
        self.play(Write(f2), run_time=1.5)
        # legend: what the symbols are in the picture
        ck = MathTex(r"c_k", font_size=FORMULA_SIZE, color=C_ARROW)
        ck_words = Text("an arrow", font_size=LABEL_SIZE, color=C_ARROW)
        leg1 = VGroup(ck, ck_words).arrange(RIGHT, buff=0.25)
        k = MathTex("k", font_size=FORMULA_SIZE)
        k_words = Text("turns per loop", font_size=LABEL_SIZE)
        leg2 = VGroup(k, k_words).arrange(RIGHT, buff=0.25)
        legend = VGroup(leg1, leg2).arrange(RIGHT, buff=1.2).to_edge(DOWN, buff=0.6)
        # one shared baseline: the bottom of "c"; flat-bottomed letters ("n", "r") sit on it
        y_base = ck[0][0].get_bottom()[1]
        for glyph, part in ((ck_words[1], ck_words), (k, k), (k_words[2], k_words)):
            part.shift((y_base - glyph.get_bottom()[1]) * UP)
        self.play(LaggedStart(FadeIn(leg1, shift=0.15 * UP), FadeIn(leg2, shift=0.15 * UP),
                              lag_ratio=0.5), run_time=1.2)
        self.wait(3)
        self.play(FadeOut(VGroup(self.cap, self.thumbs, f1, f2, legend)), run_time=1.2)
        self.wait(0.5)
