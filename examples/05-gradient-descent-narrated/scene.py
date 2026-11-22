"""How a tiny network learns: training repeats forward pass, loss, backward pass (chain rule)
and a gradient-descent step; one step takes the loss of a two-weight network from 4 to 0.71.

Narrated with Kokoro (af_heart) through manim-voiceover. The words live in job.json
(narration.script, one beat per voiceover block) and are read with line(id).
Render: "$SKILL_DIR/scripts/render-in-container.sh" <this job directory> [--quality final]

Network: h = w1 * x, y_hat = w2 * h, loss L = (y_hat - y)^2, with x = 2, y = 3,
w1 = 1, w2 = 0.5, learning rate 0.05 (numbers checked in storyboard.md).
"""

from manim import *
from manim_voiceover import VoiceoverScene

from kokoro_service import KokoroService  # on PYTHONPATH in the render image
from narration_script import line         # narration text by beat id, from job.json

try:
    from manim_qa import LayoutGuard
except ImportError:
    print("LAYOUT-GUARD unavailable: manim_qa not importable; layout checks are off", flush=True)

    class LayoutGuard:
        pass

try:  # measured geometry rules (report.md "geometry" check)
    from geometry_qa import GeometryGuard, centered_in, concentric, symmetric, within_margin
except ImportError:
    print("GEOMETRY-GUARD unavailable: geometry_qa not importable; geometry checks are off", flush=True)

    class GeometryGuard:
        def geo_track(self, **named):
            return self

        def geo_rule(self, *rules):
            return self

    def _no_rule(*args, **kwargs):
        return None

    centered_in = concentric = symmetric = within_margin = _no_rule

config.background_color = "#0F1117"
# >100 animations: keep every partial movie so frames.py --beats can map stills to animations
config.max_files_cached = 1000
Text.set_default(font="Noto Sans")
MarkupText.set_default(font="Noto Sans")

# --- colour legend (storyboard.md) -------------------------------------------------------
C_SIG = BLUE        # signals x, h, y_hat
C_W = TEAL          # weights w1, w2
C_TGT = GREEN       # target y
C_LOSS = RED        # loss L
C_GRAD = ORANGE     # gradients, slopes, local rates
C_LOOK = YELLOW     # look here now: moving point, nudges, forward pulses
C_MUTED = GREY_B

TITLE_SIZE = 40
LABEL_SIZE = 34
EQ_SIZE = 44
SMALL_EQ = 40

# --- the numbers -------------------------------------------------------------------------
X_IN, Y_TGT, W1, W2, ETA = 2.0, 3.0, 1.0, 0.5, 0.05
NODE_Y = 1.45
NODE_X = {"x": -5.1, "h": -1.7, "yh": 1.7, "L": 5.1}
NL_ORIGIN = np.array([-5.9, -2.85, 0])   # number line: value 0 sits here
NL_UNIT = 1.25
EARLY_SHIFT = (NODE_X["L"] - NODE_X["yh"]) / 2   # x, h, y_hat sit centred until the loss box arrives
VALLEY_CX = (-7.11 + 2.6) / 2                    # valley plot: centred in the region left of the panel
END_HOLD, END_FADE, END_TAIL = 2.0, 1.0, 1.0      # silent outro after the last sentence
PANEL_X = 4.1                                    # side panel centre (keeps a 7% right margin)


def loss_w2(w):
    """Loss as a function of w2 with w1 frozen at 1: y_hat = 2 w2."""
    return (2 * w - 3) ** 2


def slope_w2(w):
    return 4 * (2 * w - 3)


def eq(*parts, size=EQ_SIZE):
    """MathTex from parts; a part is a tex string or (tex, colour). Each part is valid alone."""
    texs, cols = [], []
    for p in parts:
        if isinstance(p, tuple):
            texs.append(p[0])
            cols.append(p[1])
        else:
            texs.append(p)
            cols.append(WHITE)
    m = MathTex(*texs, font_size=size)
    for sub, c in zip(m, cols):
        sub.set_color(c)
    return m


def grad(var):
    return (r"\frac{\partial L}{\partial " + var + "}", C_GRAD)


def nl_point(v):
    return NL_ORIGIN + v * NL_UNIT * RIGHT


def number_line():
    """0..4 number line whose value 0 sits exactly on NL_ORIGIN, so nl_point(v) == line.n2p(v).
    (move_to would centre line plus tick numbers, leaving the line above the points.)"""
    nl = NumberLine(x_range=[0, 4, 1], length=4 * NL_UNIT, color=C_MUTED, include_numbers=True,
                    font_size=26, stroke_width=2)
    nl.shift(NL_ORIGIN - nl.n2p(0))
    return nl


class Explainer(GeometryGuard, LayoutGuard, VoiceoverScene):
    def construct(self):
        self.set_speech_service(KokoroService())
        self.title = None
        self.declare_geometry()
        self.beat_network()
        self.beat_forward()
        self.beat_loss()
        self.beat_which_way()
        self.beat_slope()
        self.beat_step()
        self.beat_repeat()
        self.beat_many_weights()
        self.beat_nudge()
        self.beat_chain_rule()
        self.beat_backward()
        self.beat_update()
        self.beat_forward_again()
        self.beat_recap()
        self.wait(END_TAIL)

    # --- geometry rules (checked by GeometryGuard after every animation) --------------------
    def declare_geometry(self):
        line_y = (0.0, float(NL_ORIGIN[1]))
        self.geo_rule(
            # network row: centred left-right in the frame (it lives in the upper band by design;
            # the lower band holds formulas, the number line and the gradients), 7% margins
            centered_in("network", region="frame", axis="x"),
            within_margin("network", pct=7),
            within_margin("formulas", pct=6),
            # number line (beats 3 and 13): symmetric about its middle (it ends at the 0 and 4
            # ticks), its line exactly where the points are computed, every marker ON the line
            symmetric("nl", about=tuple(nl_point(2)[:2]), axis="x"),
            symmetric("nl_ticks", about=line_y, axis="y"),
            symmetric("pred_dot", about="nl_ticks", axis="y"),
            symmetric("tgt_dot", about="nl_ticks", axis="y"),
            symmetric("gap", about="nl_ticks", axis="y"),
            concentric("square", tuple(nl_point(2)[:2] + np.array([0, NL_UNIT]))),
            # valley plot: centred in the region left of the side panel, 7% margins
            centered_in("valley", region=(-7.11, -4, 2.6, 4), axis="x"),
            within_margin("valley", pct=7),
            within_margin("panel", pct=6),
            # recap: the four-box loop is symmetric and centred, the loss history centred under it
            symmetric("loop", about=(0.0, 0.3)),
            centered_in("loop", region="frame", axis="x"),
            within_margin("loop", pct=7),
            centered_in("loss_hist", region="frame", axis="x"),
        )

    # --- helpers ------------------------------------------------------------------------
    def rest(self, tracker, minimum=0.4):
        return max(tracker.get_remaining_duration(), minimum)

    def new_title(self, text):
        title = Text(text, font_size=TITLE_SIZE, color=WHITE)
        title.to_edge(UP, buff=0.5).to_edge(LEFT, buff=0.8)
        if self.title is None:
            anims = [FadeIn(title, shift=0.3 * DOWN)]
        else:  # old title leaves before the new one arrives, so the two never overlap
            anims = [AnimationGroup(FadeOut(self.title, shift=0.3 * UP), FadeIn(title, shift=0.3 * DOWN),
                                    lag_ratio=0.8)]
        self.title = title
        return anims

    def build_network(self, w1="1", w2="0.5"):
        """Nodes, edges and weight labels (no values yet)."""
        nodes = {}
        for key, sym, col in (("x", "x", C_SIG), ("h", "h", C_SIG), ("yh", r"\hat{y}", C_SIG)):
            circ = Circle(radius=0.55, color=col, fill_color=col, fill_opacity=0.12, stroke_width=4)
            circ.move_to([NODE_X[key], NODE_Y, 0])
            label = MathTex(sym, font_size=48, color=col).next_to(circ, UP, buff=0.2)
            nodes[key] = VGroup(circ, label)
        box = RoundedRectangle(corner_radius=0.15, width=1.3, height=1.1, color=C_LOSS,
                               fill_color=C_LOSS, fill_opacity=0.12, stroke_width=4)
        box.move_to([NODE_X["L"], NODE_Y, 0])
        nodes["L"] = VGroup(box, MathTex("L", font_size=48, color=C_LOSS).next_to(box, UP, buff=0.2))
        edges = {}
        for a, b in (("x", "h"), ("h", "yh"), ("yh", "L")):
            edges[a + b] = Arrow(nodes[a][0].get_right(), nodes[b][0].get_left(), buff=0.1,
                                 color=C_MUTED, stroke_width=3)
        wlabels = {
            "w1": eq(("w_1", C_W), "=", (w1, C_W), size=SMALL_EQ).next_to(edges["xh"], UP, buff=0.15),
            "w2": eq(("w_2", C_W), "=", (w2, C_W), size=SMALL_EQ).next_to(edges["hyh"], UP, buff=0.15),
        }
        return nodes, edges, wlabels

    def pred_label_pos(self, v):
        return nl_point(v) + 0.42 * LEFT + 0.45 * UP

    def pred_label(self, dot):
        lbl = MathTex(r"\hat{y}", font_size=SMALL_EQ, color=C_SIG)
        return lbl.move_to(dot.get_center() + 0.42 * LEFT + 0.45 * UP)

    def node_value(self, key, tex, col=C_SIG):
        return MathTex(tex, font_size=EQ_SIZE, color=col).move_to(self.nodes[key][0])

    def flash_edge(self, edge, color=C_LOOK, reverse=False):
        a, b = edge.get_start(), edge.get_end()
        if reverse:
            a, b = b, a
        path = Line(a, b, color=color, stroke_width=8)
        return ShowPassingFlash(path, time_width=0.6)

    def swap_tail(self, old, new, rt_out, rt_in, *with_in):
        """old and new MathTex share their leading parts ("w_1 =" ...) and differ in the last one.
        Pin new onto old, fade the old last part out, then the new one in: no glyph morphing."""
        new.shift(old[0].get_center() - new[0].get_center())
        self.play(FadeOut(old[-1], shift=0.1 * UP), run_time=rt_out)
        # FadeOut(old[-1]) split old into top-level parts; Scene.remove does not remove a
        # group's members, so remove them one by one (or "w_1 =" would stay on screen forever)
        self.remove(old, *old.submobjects)
        self.add(*new[:-1])
        self.play(FadeIn(new[-1], shift=0.1 * UP), *with_in, run_time=rt_in)
        return new

    def cover_outro_with_silence(self, seconds):
        """Manim's audio track ends with the last sentence, so without this the AAC stream would
        stop `seconds` before the video does. Lay a silent clip under the outro (from now to the
        last frame) so audio and video end together."""
        import tempfile
        import wave
        from pathlib import Path

        path = Path(tempfile.gettempdir()) / "outro_silence.wav"
        rate = 48000
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(b"\x00\x00\x00\x00" * int(round(rate * seconds)))
        self.add_sound(str(path))

    def box(self, mob, buff=0.12):
        return SurroundingRectangle(mob, color=C_LOOK, buff=buff, corner_radius=0.1, stroke_width=3)

    # --- beat 1 -------------------------------------------------------------------------
    def beat_network(self):
        nodes, edges, wl = self.build_network()
        self.nodes, self.edges, self.wl = nodes, edges, wl
        self.geo_track(network=VGroup(*nodes.values(), *edges.values(), *wl.values()))
        # Until the loss box arrives (beat 3), the three-node chain sits centred in the frame;
        # it slides left by half a node spacing when the loss box takes the right-hand slot.
        self.early = VGroup(nodes["x"], nodes["h"], nodes["yh"], edges["xh"], edges["hyh"], wl["w1"], wl["w2"])
        self.early.shift(EARLY_SHIFT * RIGHT)
        with self.voiceover(text=line("intro_small")) as tr:
            self.play(*self.new_title("How a tiny network learns"), run_time=0.4 * tr.duration)
            self.play(LaggedStart(*[FadeIn(nodes[k], shift=0.2 * UP) for k in ("x", "h", "yh")],
                                  lag_ratio=0.4), run_time=self.rest(tr))
        with self.voiceover(text=line("intro_parts")) as tr:
            self.play(Indicate(nodes["x"][1]), run_time=0.24 * tr.duration)
            self.play(Indicate(nodes["h"][1]), run_time=0.3 * tr.duration)
            self.play(Indicate(nodes["yh"][1]), run_time=0.2 * tr.duration)
            self.play(GrowArrow(edges["xh"]), GrowArrow(edges["hyh"]),
                      FadeIn(wl["w1"]), FadeIn(wl["w2"]), run_time=self.rest(tr))
        self.wait(0.5)

    # --- beat 2 -------------------------------------------------------------------------
    def beat_forward(self):
        n, e, wl = self.nodes, self.edges, self.wl
        f_h = eq(("h", C_SIG), "=", ("w_1", C_W), ("x", C_SIG), "=", ("1", C_W), r"\cdot",
                 ("2", C_SIG), "=", ("2", C_SIG))
        f_y = eq((r"\hat{y}", C_SIG), "=", ("w_2", C_W), ("h", C_SIG), "=", ("0.5", C_W), r"\cdot",
                 ("2", C_SIG), "=", ("1", C_SIG))
        f_L = eq(("L", C_LOSS), "=", "(", (r"\hat{y}", C_SIG), "-", ("y", C_TGT), ")^2", "=", "(",
                 ("1", C_SIG), "-", ("3", C_TGT), ")^2", "=", ("4", C_LOSS))
        panel = VGroup(f_h, f_y, f_L).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        panel.to_edge(RIGHT, buff=0.95).set_y(-1.75)
        self.f_h, self.f_y, self.f_L = f_h, f_y, f_L
        self.geo_track(formulas=panel)

        self.v_x = self.node_value("x", "2")
        self.v_h = self.node_value("h", "2")
        self.v_y = self.node_value("yh", "1")
        with self.voiceover(text=line("fwd_weights")) as tr:
            self.play(*self.new_title("Forward pass"), run_time=0.3 * tr.duration)
            self.play(Indicate(wl["w1"], color=C_LOOK), Indicate(wl["w2"], color=C_LOOK),
                      run_time=self.rest(tr))
        with self.voiceover(text=line("fwd_hidden")) as tr:
            self.play(FadeIn(self.v_x, scale=0.6), run_time=0.25 * tr.duration)
            self.play(self.flash_edge(e["xh"]), run_time=0.25 * tr.duration)
            self.play(FadeIn(self.v_h, scale=0.6), Write(f_h), run_time=self.rest(tr))
        with self.voiceover(text=line("fwd_output")) as tr:
            self.play(self.flash_edge(e["hyh"]), run_time=0.4 * tr.duration)
            self.play(FadeIn(self.v_y, scale=0.6), Write(f_y), run_time=self.rest(tr))
        self.wait(0.5)

    # --- beat 3 -------------------------------------------------------------------------
    def beat_loss(self):
        n, e = self.nodes, self.edges
        tgt = eq(("y", C_TGT), "=", ("3", C_TGT), size=SMALL_EQ).next_to(n["L"][0], DOWN, buff=0.25)
        self.tgt = tgt
        self.early.add(self.v_x, self.v_h, self.v_y)
        self.play(*self.new_title("Loss"), self.early.animate.shift(EARLY_SHIFT * LEFT),
                  FadeIn(n["L"], shift=0.3 * LEFT), run_time=1.0)
        with self.voiceover(text=line("loss_wanted")) as tr:
            self.play(GrowArrow(e["yhL"]), run_time=0.4 * tr.duration)
            self.play(FadeIn(tgt, shift=0.2 * UP), run_time=self.rest(tr))

        nline = number_line()
        d_pred = Dot(nl_point(1), color=C_SIG, radius=0.1)
        d_tgt = Dot(nl_point(3), color=C_TGT, radius=0.1)
        l_pred = self.pred_label(d_pred)
        l_tgt = MathTex("y", font_size=SMALL_EQ, color=C_TGT).next_to(d_tgt, RIGHT, buff=0.15).shift(0.3 * UP)
        gap = Line(nl_point(1), nl_point(3), color=C_LOOK, stroke_width=6)
        gap_lbl = MathTex("2", font_size=SMALL_EQ, color=C_LOOK).next_to(gap, UP, buff=0.3)  # clear of the ticks
        sq = Square(side_length=2 * NL_UNIT, color=C_LOSS, fill_color=C_LOSS, fill_opacity=0.3,
                    stroke_width=4)
        sq.move_to(nl_point(2) + NL_UNIT * UP)
        sq_lbl = MathTex("4", font_size=EQ_SIZE, color=C_LOSS).move_to(sq)
        self.nl = VGroup(nline, d_pred, d_tgt, l_pred, l_tgt)
        self.sq, self.sq_lbl = sq, sq_lbl
        self.geo_track(nl=nline, nl_ticks=nline.ticks, pred_dot=d_pred, tgt_dot=d_tgt, gap=gap, square=sq)
        with self.voiceover(text=line("loss_gap")) as tr:
            self.play(Create(nline), run_time=0.2 * tr.duration)
            self.play(FadeIn(d_pred, scale=0.5), FadeIn(l_pred), FadeIn(d_tgt, scale=0.5), FadeIn(l_tgt),
                      run_time=0.2 * tr.duration)
            self.play(Create(gap), FadeIn(gap_lbl), run_time=0.35 * tr.duration)
            self.play(GrowFromEdge(sq, DOWN), FadeOut(gap_lbl), run_time=self.rest(tr))
        self.gap = gap
        self.v_L = self.node_value("L", "4", C_LOSS)
        with self.voiceover(text=line("loss_value")) as tr:
            self.play(FadeIn(sq_lbl), Write(self.f_L), run_time=0.6 * tr.duration)
            self.play(TransformFromCopy(sq_lbl, self.v_L), run_time=self.rest(tr))
        self.wait(1)

    # --- beat 4 -------------------------------------------------------------------------
    def beat_which_way(self):
        n, e, wl = self.nodes, self.edges, self.wl
        with self.voiceover(text=line("which_way")) as tr:
            self.play(FadeOut(VGroup(self.nl, self.gap, self.sq, self.sq_lbl, self.f_h, self.f_y, self.f_L)),
                      run_time=0.3 * tr.duration)
            self.play(Wiggle(wl["w1"]), Wiggle(wl["w2"]), run_time=self.rest(tr))

        axes = Axes(x_range=[0, 3, 0.5], y_range=[0, 9, 3], x_length=6.4, y_length=5, tips=False,
                    axis_config={"color": C_MUTED, "stroke_width": 2},
                    x_axis_config={"numbers_to_include": [0.5, 1, 1.5, 2, 2.5, 3], "font_size": 26,
                                   "decimal_number_config": {"num_decimal_places": 1}},
                    y_axis_config={"numbers_to_include": [3, 6, 9], "font_size": 26,
                                   "decimal_number_config": {"num_decimal_places": 0}})
        axes.move_to([-2.2, -0.45, 0])
        x_lab = MathTex("w_2", font_size=EQ_SIZE, color=C_W).next_to(axes.x_axis, RIGHT, buff=0.25)
        y_lab = MathTex("L", font_size=EQ_SIZE, color=C_LOSS).next_to(axes.y_axis, UP, buff=0.2)
        plot = VGroup(axes, x_lab, y_lab)
        plot.shift((VALLEY_CX - plot.get_center()[0]) * RIGHT)   # centred in the left region
        self.axes = axes
        self.geo_track(valley=plot)
        wv = ValueTracker(0.0)
        self.wv = wv
        traced = always_redraw(lambda: axes.plot(loss_w2, x_range=[0, max(wv.get_value(), 1e-3)],
                                                 color=C_LOSS, stroke_width=5))
        dot = always_redraw(lambda: Dot(axes.c2p(wv.get_value(), loss_w2(wv.get_value())),
                                        color=C_LOOK, radius=0.11).set_z_index(3))
        marker = always_redraw(lambda: Triangle(color=C_W, fill_color=C_W, fill_opacity=1)
                               .scale(0.12).move_to(axes.c2p(wv.get_value(), 0) + 0.12 * DOWN))
        drop = always_redraw(lambda: DashedLine(axes.c2p(wv.get_value(), 0),
                                                axes.c2p(wv.get_value(), loss_w2(wv.get_value())),
                                                color=C_MUTED, stroke_width=2))
        self.dot, self.marker, self.drop = dot, marker, drop
        with self.voiceover(text=line("valley_slide")) as tr:
            net = VGroup(*[n[k] for k in n], *e.values(), wl["w1"], wl["w2"], self.v_x, self.v_h,
                         self.v_y, self.v_L, self.tgt)
            self.play(*self.new_title("Gradient descent"), wl["w1"].animate.set_opacity(0.35),
                      Indicate(wl["w2"], color=C_LOOK), run_time=0.25 * tr.duration)
            self.play(FadeOut(net), Create(axes), FadeIn(x_lab), FadeIn(y_lab), run_time=0.25 * tr.duration)
            self.add(traced, drop, marker, dot)
            self.play(wv.animate.set_value(3), run_time=self.rest(tr), rate_func=linear)
        curve = axes.plot(loss_w2, x_range=[0, 3], color=C_LOSS, stroke_width=5)
        traced.clear_updaters()
        self.remove(traced)
        self.add(curve)
        self.bring_to_front(drop, marker, dot)
        self.valley = VGroup(axes, x_lab, y_lab, curve)
        self.geo_track(curve=curve)
        self.geo_rule(symmetric("curve", about=tuple(axes.c2p(1.5, 0)[:2]), axis="x"))
        with self.voiceover(text=line("valley_wall")) as tr:
            self.play(wv.animate.set_value(0.5), run_time=0.7 * tr.duration)
        self.wait(0.5)

    # --- beat 5 -------------------------------------------------------------------------
    def beat_slope(self):
        axes, wv = self.axes, self.wv

        axis_y = axes.c2p(0, 0)[1]

        def tangent():
            w = wv.get_value()
            p = axes.c2p(w, loss_w2(w))
            q = axes.c2p(w + 0.05, loss_w2(w) + 0.05 * slope_w2(w))
            d = (q - p) / np.linalg.norm(q - p)
            # each half is at most 1.1 long and stops at the axis line (near the bottom of the
            # valley a full tangent would dip below the axis and through the "1.5" label)
            room = max(p[1] - axis_y, 0.0)
            ahead = 1.1 if d[1] >= -1e-6 else min(1.1, room / -d[1])
            behind = 1.1 if d[1] <= 1e-6 else min(1.1, room / d[1])
            return Line(p - max(behind, 0.01) * d, p + max(ahead, 0.01) * d, color=C_GRAD, stroke_width=5)

        tan = always_redraw(tangent)
        val = DecimalNumber(slope_w2(0.5), num_decimal_places=1, font_size=EQ_SIZE, color=C_GRAD)
        val.add_updater(lambda m: m.set_value(slope_w2(wv.get_value())))
        lhs = eq(grad("w_2"), "=")
        readout = VGroup(lhs, val).arrange(RIGHT, buff=0.2)
        readout.move_to([PANEL_X, 2.0, 0])
        val.add_updater(lambda m: m.next_to(lhs, RIGHT, buff=0.2))
        self.tan, self.slope_val, self.readout = tan, val, readout

        p0 = axes.c2p(0.5, loss_w2(0.5))
        q0 = axes.c2p(0.55, loss_w2(0.5) + 0.05 * slope_w2(0.5))
        d0 = (q0 - p0) / np.linalg.norm(q0 - p0)
        inside = np.array([-d0[1], d0[0], 0])         # perpendicular, pointing up-right into the valley
        down = Arrow(p0 + 0.2 * d0 + 0.5 * inside, p0 + 1.4 * d0 + 0.5 * inside, buff=0, color=WHITE,
                     stroke_width=5)                  # parallel to the tangent, clear of curve and drop line
        down_lbl = Text("downhill", font_size=28, color=WHITE).next_to(down.get_end(), RIGHT, buff=0.15)
        with self.voiceover(text=line("slope_value")) as tr:
            self.play(Create(tan), run_time=0.5 * tr.duration)
            self.play(FadeIn(readout), run_time=self.rest(tr))
        with self.voiceover(text=line("slope_meaning")) as tr:
            self.play(Indicate(readout, color=C_LOOK), run_time=0.4 * tr.duration)
            self.play(GrowArrow(down), FadeIn(down_lbl), run_time=self.rest(tr))
        self.wait(0.5)
        self.down = VGroup(down, down_lbl)

    # --- beat 6 -------------------------------------------------------------------------
    def beat_step(self):
        wv = self.wv
        rule = eq(("w_2", C_W), r"\leftarrow", ("w_2", C_W), "-", r"\eta", grad("w_2"))
        rule.move_to([PANEL_X, 0.6, 0])
        lr = eq(r"\eta", "=", "0.05").next_to(rule, DOWN, buff=0.4)
        arith = eq(("0.5", C_W), "-", "0.05", r"\cdot", ("(-8)", C_GRAD), "=", ("0.9", C_W), size=SMALL_EQ)
        arith.next_to(lr, DOWN, buff=0.5)
        self.rule, self.lr, self.arith = rule, lr, arith
        self.geo_track(panel=VGroup(self.readout, rule, lr, arith))
        with self.voiceover(text=line("step_rule")) as tr:
            self.play(FadeOut(self.down), Write(rule), run_time=0.55 * tr.duration)
            self.play(FadeIn(lr, shift=0.2 * UP), run_time=self.rest(tr))
        with self.voiceover(text=line("step_move")) as tr:
            self.play(Write(arith), run_time=0.4 * tr.duration)
            self.play(wv.animate.set_value(0.9), run_time=self.rest(tr))
        self.wait(0.5)

    # --- beat 7 -------------------------------------------------------------------------
    def beat_repeat(self):
        wv = self.wv
        with self.voiceover(text=line("repeat")) as tr:
            step_t = (tr.duration - 0.6) / 4
            self.play(FadeOut(self.arith), run_time=0.6)
            w = 0.9
            for _ in range(4):
                w = w - ETA * slope_w2(w)
                self.play(wv.animate.set_value(w), run_time=step_t)
        self.wait(1)

    # --- beat 8 -------------------------------------------------------------------------
    def beat_many_weights(self):
        for m in (self.tan, self.dot, self.marker, self.drop, self.slope_val):
            m.clear_updaters()
        chapter = VGroup(self.valley, self.tan, self.dot, self.marker, self.drop, self.readout,
                         self.rule, self.lr)
        nodes, edges, wl = self.build_network()
        self.nodes, self.edges, self.wl = nodes, edges, wl
        self.geo_track(network=VGroup(*nodes.values(), *edges.values(), *wl.values()))
        self.v_x = self.node_value("x", "2")
        self.v_h = self.node_value("h", "2")
        self.v_y = self.node_value("yh", "1")
        self.v_L = self.node_value("L", "4", C_LOSS)
        self.tgt = eq(("y", C_TGT), "=", ("3", C_TGT), size=SMALL_EQ).next_to(nodes["L"][0], DOWN, buff=0.25)
        net = VGroup(*[nodes[k] for k in nodes], *edges.values(), wl["w1"], wl["w2"], self.v_x, self.v_h,
                     self.v_y, self.v_L, self.tgt)
        q1 = eq(grad("w_1"), "=", ("?", C_GRAD), size=SMALL_EQ).next_to(edges["xh"], DOWN, buff=0.3)
        q2 = eq(grad("w_2"), "=", ("?", C_GRAD), size=SMALL_EQ).next_to(edges["hyh"], DOWN, buff=0.3)
        self.q1, self.q2 = q1, q2
        with self.voiceover(text=line("many_weights")) as tr:
            self.play(FadeOut(chapter), *self.new_title("Backpropagation"), run_time=0.35 * tr.duration)
            self.play(FadeIn(net), run_time=0.3 * tr.duration)
            self.play(FadeIn(q1, shift=0.2 * DOWN), FadeIn(q2, shift=0.2 * DOWN), run_time=self.rest(tr))
        with self.voiceover(text=line("buried")) as tr:
            self.play(Indicate(wl["w1"], color=C_LOOK), run_time=0.4 * tr.duration)
            self.play(self.flash_edge(edges["xh"]), run_time=0.2 * tr.duration)
            self.play(self.flash_edge(edges["hyh"]), run_time=0.2 * tr.duration)
            self.play(self.flash_edge(edges["yhL"]), run_time=self.rest(tr))
        self.wait(0.5)

    # --- beat 9 -------------------------------------------------------------------------
    def beat_nudge(self):
        e = self.edges
        row_y = -0.45
        mk = lambda tex: MathTex(tex, font_size=SMALL_EQ, color=C_LOOK)
        n_w1 = mk("+0.01").move_to([e["xh"].get_center()[0], row_y, 0])
        n_h = mk("+0.02").move_to([NODE_X["h"], row_y, 0])
        n_y = mk("+0.01").move_to([NODE_X["yh"], row_y, 0])
        n_L = mk("-0.04").move_to([NODE_X["L"], row_y, 0])
        self.nudges = VGroup(n_w1, n_h, n_y, n_L)
        with self.voiceover(text=line("nudge_w1")) as tr:
            self.play(FadeIn(n_w1, shift=0.2 * UP), Indicate(self.wl["w1"], color=C_LOOK),
                      run_time=self.rest(tr))
        with self.voiceover(text=line("nudge_h")) as tr:
            self.play(self.flash_edge(e["xh"]), run_time=0.4 * tr.duration)
            self.play(FadeIn(n_h, shift=0.2 * UP), run_time=self.rest(tr))
        with self.voiceover(text=line("nudge_out")) as tr:
            self.play(self.flash_edge(e["hyh"]), run_time=0.4 * tr.duration)
            self.play(FadeIn(n_y, shift=0.2 * UP), run_time=self.rest(tr))
        with self.voiceover(text=line("nudge_loss")) as tr:
            self.play(self.flash_edge(e["yhL"]), run_time=0.4 * tr.duration)
            self.play(FadeIn(n_L, shift=0.2 * UP), run_time=self.rest(tr))
        self.wait(0.5)

    # --- beat 10 ------------------------------------------------------------------------
    def beat_chain_rule(self):
        n_w1, n_h, n_y, n_L = self.nudges
        arcs, labels = VGroup(), VGroup()
        for a, b, tex in ((n_w1, n_h, r"\times 2"), (n_h, n_y, r"\times 0.5"), (n_y, n_L, r"\times (-4)")):
            arc = CurvedArrow(a.get_bottom() + 0.1 * DOWN, b.get_bottom() + 0.1 * DOWN, angle=PI / 3,
                              color=C_GRAD, stroke_width=3)
            lbl = MathTex(tex, font_size=SMALL_EQ, color=C_GRAD).next_to(arc, DOWN, buff=0.12)
            arcs.add(arc)
            labels.add(lbl)
        prod = eq(grad("w_1"), "=", ("2", C_GRAD), r"\cdot", ("0.5", C_GRAD), r"\cdot", ("(-4)", C_GRAD),
                  "=", ("-4", C_GRAD))
        prod.move_to([0, -2.75, 0])
        prod_box = self.box(prod)
        self.chain = VGroup(arcs, labels, prod, prod_box)
        with self.voiceover(text=line("chain_links")) as tr:
            # a flash runs along each link in turn (Indicate would stretch the arrows)
            self.play(LaggedStart(*[self.flash_edge(e, C_GRAD) for e in self.edges.values()], lag_ratio=0.6),
                      run_time=self.rest(tr))
        with self.voiceover(text=line("chain_rates")) as tr:
            t = tr.duration / 3
            for arc, lbl in zip(arcs, labels):
                self.play(Create(arc), FadeIn(lbl), run_time=t)
        with self.voiceover(text=line("chain_product")) as tr:
            self.play(Write(prod), run_time=0.55 * tr.duration)
            self.play(Create(prod_box), run_time=self.rest(tr))
        self.wait(1)

    # --- beat 11 ------------------------------------------------------------------------
    def beat_backward(self):
        e = self.edges
        g_y = eq(grad(r"\hat{y}"), "=", ("-4", C_GRAD), size=SMALL_EQ).move_to([NODE_X["yh"], -0.8, 0])
        g_h = eq(grad("h"), "=", ("-2", C_GRAD), size=SMALL_EQ).move_to([NODE_X["h"], -0.8, 0])
        g_w2 = eq(grad("w_2"), "=", ("-8", C_GRAD), size=SMALL_EQ).move_to(self.q2)
        g_w1 = eq(grad("w_1"), "=", ("-4", C_GRAD), size=SMALL_EQ).move_to(self.q1)
        s_y = eq(grad(r"\hat{y}"), "=", "2(", (r"\hat{y}", C_SIG), "-", ("y", C_TGT), ")", "=", "2(",
                 ("1", C_SIG), "-", ("3", C_TGT), ")", "=", ("-4", C_GRAD))
        s_w2 = eq(grad("w_2"), "=", grad(r"\hat{y}"), r"\cdot", ("h", C_SIG), "=", ("(-4)", C_GRAD),
                  r"\cdot", ("2", C_SIG), "=", ("-8", C_GRAD))
        s_h = eq(grad("h"), "=", grad(r"\hat{y}"), r"\cdot", ("w_2", C_W), "=", ("(-4)", C_GRAD),
                 r"\cdot", ("0.5", C_W), "=", ("-2", C_GRAD))
        s_w1 = eq(grad("w_1"), "=", grad("h"), r"\cdot", ("x", C_SIG), "=", ("(-2)", C_GRAD),
                  r"\cdot", ("2", C_SIG), "=", ("-4", C_GRAD))
        for s in (s_y, s_w2, s_h, s_w1):
            s.move_to([0, -2.6, 0])
        with self.voiceover(text=line("bp_start")) as tr:
            self.play(FadeOut(self.nudges), FadeOut(self.chain), run_time=0.4 * tr.duration)
            self.play(Indicate(self.nodes["L"][0], color=C_GRAD), run_time=self.rest(tr))
        with self.voiceover(text=line("bp_out")) as tr:
            self.play(self.flash_edge(e["yhL"], C_GRAD, reverse=True), run_time=0.3 * tr.duration)
            self.play(FadeIn(g_y, shift=0.2 * DOWN), Write(s_y), run_time=self.rest(tr))
        with self.voiceover(text=line("bp_w2")) as tr:
            self.play(FadeOut(s_y), self.flash_edge(e["hyh"], C_GRAD, reverse=True), run_time=0.3 * tr.duration)
            # "= ?" becomes "= -8": only the "?" changes (fade out, then the value in; no morph)
            g_w2 = self.swap_tail(self.q2, g_w2, 0.15 * tr.duration, self.rest(tr), Write(s_w2))
        with self.voiceover(text=line("bp_h")) as tr:
            self.play(FadeOut(s_w2), run_time=0.25 * tr.duration)
            self.play(FadeIn(g_h, shift=0.2 * DOWN), Write(s_h), run_time=self.rest(tr))
        with self.voiceover(text=line("bp_w1")) as tr:
            self.play(FadeOut(s_h), self.flash_edge(e["xh"], C_GRAD, reverse=True), run_time=0.3 * tr.duration)
            g_w1 = self.swap_tail(self.q1, g_w1, 0.15 * tr.duration, self.rest(tr), Write(s_w1))
        with self.voiceover(text=line("bp_done")) as tr:
            boxes = VGroup(self.box(g_w1, buff=0.08), self.box(g_w2, buff=0.08))
            self.play(Create(boxes), run_time=0.45 * tr.duration)
            self.wait(max(tr.get_remaining_duration() - 0.4, 0.1))
            self.play(FadeOut(boxes), run_time=0.4)
        self.wait(0.5)
        self.grads = VGroup(g_y, g_h)
        self.g_w1, self.g_w2, self.s_w1 = g_w1, g_w2, s_w1

    # --- beat 12 ------------------------------------------------------------------------
    def beat_update(self):
        wl = self.wl
        u1 = eq(("w_1", C_W), r"\leftarrow", ("1", C_W), "-", "0.05", r"\cdot", ("(-4)", C_GRAD), "=",
                ("1.2", C_W))
        u2 = eq(("w_2", C_W), r"\leftarrow", ("0.5", C_W), "-", "0.05", r"\cdot", ("(-8)", C_GRAD), "=",
                ("0.9", C_W))
        upd = VGroup(u1, u2).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -2.45, 0])
        new_w1 = eq(("w_1", C_W), "=", ("1.2", C_W), size=SMALL_EQ)
        new_w2 = eq(("w_2", C_W), "=", ("0.9", C_W), size=SMALL_EQ)
        with self.voiceover(text=line("upd_both")) as tr:
            self.play(*self.new_title("One training step"), FadeOut(self.s_w1), FadeOut(self.grads),
                      run_time=0.4 * tr.duration)
            self.play(Write(u1), Write(u2), run_time=self.rest(tr))
        with self.voiceover(text=line("upd_values")) as tr:
            # only the number changes: "1" fades out, then "1.2" fades in (no glyph morphing)
            wl["w1"] = self.swap_tail(wl["w1"], new_w1, 0.15 * tr.duration, 0.35 * tr.duration,
                                      Indicate(u1[-1], color=C_LOOK))
            wl["w2"] = self.swap_tail(wl["w2"], new_w2, 0.15 * tr.duration, self.rest(tr),
                                      Indicate(u2[-1], color=C_LOOK))
        self.wait(0.5)
        self.upd = upd

    # --- beat 13 ------------------------------------------------------------------------
    def beat_forward_again(self):
        e = self.edges
        v_h2 = self.node_value("h", "2.4")
        v_y2 = self.node_value("yh", "2.16").scale(0.8)
        v_L2 = self.node_value("L", "0.71", C_LOSS).scale(0.8)
        nline = number_line()
        d_tgt = Dot(nl_point(3), color=C_TGT, radius=0.1)
        l_tgt = MathTex("y", font_size=SMALL_EQ, color=C_TGT).next_to(d_tgt, RIGHT, buff=0.15).shift(0.3 * UP)
        d_pred = Dot(nl_point(1), color=C_SIG, radius=0.1)
        l_pred = self.pred_label(d_pred)
        old_sq = Square(side_length=2 * NL_UNIT, color=C_LOSS, fill_color=C_LOSS, fill_opacity=0.3,
                        stroke_width=4).move_to(nl_point(2) + NL_UNIT * UP)
        side = (3 - 2.16) * NL_UNIT
        new_sq = Square(side_length=side, color=C_LOSS, fill_color=C_LOSS, fill_opacity=0.3, stroke_width=4)
        new_sq.move_to(nl_point(2.16) + side / 2 * (RIGHT + UP))
        new_lbl = MathTex("0.71", font_size=SMALL_EQ, color=C_LOSS).next_to(new_sq, UP, buff=0.15)
        old_lbl = MathTex("4", font_size=SMALL_EQ, color=C_LOSS).move_to(old_sq.get_center() + 0.5 * UL)
        f_L2 = eq(("L", C_LOSS), "=", "(", ("2.16", C_SIG), "-", ("3", C_TGT), ")^2", r"\approx",
                  ("0.71", C_LOSS))
        f_L2.move_to([3.4, -1.75, 0])
        self.geo_track(nl=nline, nl_ticks=nline.ticks, pred_dot=d_pred, tgt_dot=d_tgt, square=old_sq,
                       new_square=new_sq)
        self.geo_rule(concentric("new_square", tuple(nline.n2p(2.16)[:2] + side / 2)))
        # node values change by fading the old number out, then the new one in (no glyph morphing)
        with self.voiceover(text=line("fwd2_run")) as tr:
            self.play(FadeOut(self.upd), FadeOut(self.g_w1), FadeOut(self.g_w2), run_time=0.35 * tr.duration)
            self.play(self.flash_edge(e["xh"]), FadeOut(self.v_h), run_time=0.3 * tr.duration)
            self.play(FadeIn(v_h2, scale=0.6), run_time=self.rest(tr))
        self.v_h = v_h2
        with self.voiceover(text=line("fwd2_output")) as tr:
            self.play(self.flash_edge(e["hyh"]), FadeOut(self.v_y), run_time=0.2 * tr.duration)
            self.play(FadeIn(v_y2, scale=0.6), run_time=0.2 * tr.duration)
            self.v_y = v_y2
            self.play(Create(nline), FadeIn(d_tgt), FadeIn(l_tgt), FadeIn(d_pred), FadeIn(l_pred),
                      FadeIn(old_sq), FadeIn(old_lbl), run_time=0.3 * tr.duration)
            self.play(d_pred.animate.move_to(nl_point(2.16)), l_pred.animate.move_to(self.pred_label_pos(2.16)),
                      run_time=self.rest(tr))
        with self.voiceover(text=line("fwd2_loss")) as tr:
            self.play(self.flash_edge(e["yhL"]), FadeOut(self.v_L),
                      old_sq.animate.set_fill(opacity=0.06).set_stroke(opacity=0.35),
                      old_lbl.animate.set_opacity(0.4), run_time=0.2 * tr.duration)
            self.play(FadeIn(v_L2, scale=0.6), run_time=0.12 * tr.duration)
            self.v_L = v_L2
            self.play(TransformFromCopy(old_sq, new_sq), FadeIn(new_lbl), Write(f_L2), run_time=self.rest(tr))
        self.wait(1.5)

    # --- beat 14 ------------------------------------------------------------------------
    def beat_recap(self):
        def box(text, col, pos):
            r = RoundedRectangle(corner_radius=0.15, width=3.6, height=1.0, color=col, fill_color=col,
                                 fill_opacity=0.15, stroke_width=4)
            return VGroup(r, Text(text, font_size=LABEL_SIZE, color=WHITE).move_to(r)).move_to(pos)

        boxes = [box("forward pass", C_SIG, [-2.7, 1.3, 0]), box("loss", C_LOSS, [2.7, 1.3, 0]),
                 box("backward pass", C_GRAD, [2.7, -0.7, 0]), box("step downhill", C_W, [-2.7, -0.7, 0])]
        arrows = VGroup(
            Arrow(boxes[0].get_right(), boxes[1].get_left(), buff=0.15, color=C_MUTED),
            Arrow(boxes[1].get_bottom(), boxes[2].get_top(), buff=0.15, color=C_MUTED),
            Arrow(boxes[2].get_left(), boxes[3].get_right(), buff=0.15, color=C_MUTED),
            Arrow(boxes[3].get_top(), boxes[0].get_bottom(), buff=0.15, color=C_MUTED),
        )
        hist_nums = eq(("4", C_LOSS), r"\;\to\;", ("0.71", C_LOSS), r"\;\to\;", ("0.0005", C_LOSS),
                       size=48)
        hist_word = Text("loss", font_size=LABEL_SIZE, color=C_LOSS)
        hist = VGroup(hist_word, hist_nums).arrange(RIGHT, buff=0.4).move_to([0, -2.5, 0])
        with self.voiceover(text=line("recap_loop")) as tr:
            keep = [m for m in self.mobjects if m is not self.title and not isinstance(m, ValueTracker)]
            self.play(FadeOut(*keep), *self.new_title("The training loop"), run_time=0.17 * tr.duration)
            # each box arrives with its phrase: "a forward pass, / a loss, / a backward pass for the
            # slopes, / and a small step downhill" (fractions of the sentence, measured from the SRT)
            for i, (b, frac) in enumerate(zip(boxes, (0.15, 0.12, 0.2, None))):
                anims = [FadeIn(b, shift=0.2 * RIGHT)]
                if i:
                    anims.append(GrowArrow(arrows[i - 1]))
                self.play(*anims, run_time=frac * tr.duration if frac else self.rest(tr))
        # measured once the loop is complete (the boxes arrive one by one at their final places)
        self.geo_track(loop=VGroup(*boxes, *arrows))
        with self.voiceover(text=line("recap_repeat")) as tr:
            self.play(GrowArrow(arrows[3]), run_time=0.2 * tr.duration)
            self.play(LaggedStart(*[Indicate(b[0], color=C_LOOK, scale_factor=1.05) for b in boxes],
                                  lag_ratio=0.25), FadeIn(hist_word), FadeIn(hist_nums[:3]),
                      run_time=0.5 * tr.duration)
            self.play(FadeIn(hist_nums[3:], shift=0.2 * RIGHT), run_time=self.rest(tr))
        # the history arrived in slices (hist_nums[:3], then [3:]); re-add it as one group so the
        # geometry checker measures the whole line, not only the word "loss"
        self.add(hist)
        self.geo_track(loss_hist=hist)
        self.cover_outro_with_silence(END_HOLD + END_FADE + END_TAIL)
        self.wait(END_HOLD)
        self.play(FadeOut(*[m for m in self.mobjects if not isinstance(m, ValueTracker)]), run_time=END_FADE)
