"""Six trig functions on one unit circle: every one of them is a length in a single picture.

The point on the unit circle is (cos θ, sin θ); the tangent line at that point is cut by the
axes into tan θ and cot θ; the distances from the centre to those crossings are sec θ and csc θ.

Render: "$SKILL_DIR/scripts/render-in-container.sh" JOB_DIR   (job.json: {"scene": "Explainer"})
"""

from manim import *

try:  # layout checker; on PYTHONPATH in the render image
    from manim_qa import LayoutGuard
except ImportError:  # keeps the file renderable without the skill
    print("LAYOUT-GUARD unavailable: manim_qa not importable; layout checks are off", flush=True)

    class LayoutGuard:
        pass

try:  # measured geometry checker (render image)
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

# --- style (references/style-guide.md) -----------------------------------------------
config.background_color = "#0F1117"
config.max_files_cached = 1000   # >100 animations: keep every partial movie so frames.py --beats works
Text.set_default(font="Noto Sans")
MarkupText.set_default(font="Noto Sans")

# --- colour legend: one colour per concept, used everywhere ---------------------------
C_SIN = BLUE
C_COS = RED
C_TAN = YELLOW      # yellow means tan in this video, not "look here"
C_SEC = GREEN
C_COT = PURPLE_A
C_CSC = ORANGE
C_ONE = WHITE       # radius 1, the angle, the moving point
C_SCAFFOLD = GREY_B
FUNC_COLOURS = {r"\sin": C_SIN, r"\cos": C_COS, r"\tan": C_TAN,
                r"\sec": C_SEC, r"\cot": C_COT, r"\csc": C_CSC}

CAPTION_SIZE = 30
LABEL_SIZE = 32
EQ_SIZE = 40
READOUT_SIZE = 36
SEG_W = 6

# --- layout ---------------------------------------------------------------------------
THETA0 = 55 * DEGREES
# The axes are always symmetric about the circle's centre (half-lengths XR, YU in radii), so
# the figure (axes + circle) is centred on O. Each layout centres it in its own region with at
# least 7% of the frame width/height as margin (checked by GeometryGuard).
HOME = {"ox": -2.45, "oy": 0.0, "r": 2.0}    # diagram centred in the left region, panel right
WIDE = {"ox": 0.0, "oy": -0.35, "r": 0.95}   # zoomed out for the limit sweep: below the caption band
HOME_REGION = (-7.11, -4.0, 2 * HOME["ox"] + 7.11, 4.0)   # left of the panel; centre = O
WIDE_REGION = (-7.11, -4.0, 7.11, 3.3)                    # under the caption band; centre = O
AX0 = 1.25                                   # axis half-length (radii) before the tangent line
XR_TAN = (1 / np.cos(THETA0) + 0.06) / 1.0   # reaches just past E (sec θ0) on both sides
YU_TAN = 1 / np.sin(THETA0) + 0.125          # reaches just past F (csc θ0) on both sides
XR_WIDE = 1 / np.cos(80 * DEGREES) + 0.13    # past E at 80°
YU_WIDE = 1 / np.sin(20 * DEGREES) + 0.26    # past F at 20°
PANEL_X = 2.35                               # left edge of the side panel (HOME)
RD_X = 1.5                                   # left edge of captions/readouts in WIDE (first quadrant)
CAPTION_Y = 3.0
SEC_DROP = 0.7       # the sec dimension line runs this far below the x-axis (cos is on the axis)
SAFE_X, SAFE_Y = 6.4, 3.4


def tex(*parts, size=EQ_SIZE):
    """MathTex whose parts are coloured by the legend (each part containing \\sin is blue...)."""
    m = MathTex(*parts, font_size=size)
    for sub, part in zip(m, parts):
        for key, col in FUNC_COLOURS.items():
            if key in part:
                sub.set_color(col)
    return m


def label(s, colour, size=LABEL_SIZE):
    return MathTex(s, font_size=size, color=colour)


def support(m, u):
    """Half the extent of m's bounding box in the direction of unit vector u."""
    return (abs(u[0]) * m.width + abs(u[1]) * m.height) / 2


class Explainer(GeometryGuard, LayoutGuard, Scene):
    def construct(self):
        self.setup_geometry()
        self.beat_circle()
        self.beat_angle()
        self.beat_cos()
        self.beat_sin()
        self.beat_sweep_sin_cos()
        self.beat_pythagoras()
        self.beat_tangent_line()
        self.beat_tan()
        self.beat_sec()
        self.beat_cot()
        self.beat_csc()
        self.beat_ratio_cos()
        self.beat_ratio_sin()
        self.beat_extremes()
        self.beat_recap()

    # --- geometry: everything is computed from these trackers ---------------------------
    def setup_geometry(self):
        self.TH = ValueTracker(0)
        self.OX = ValueTracker(HOME["ox"])
        self.OY = ValueTracker(HOME["oy"])
        self.RR = ValueTracker(HOME["r"])
        self.XR = ValueTracker(AX0)    # x-axis half-length, in radii (same on both sides)
        self.YU = ValueTracker(AX0)    # y-axis half-length, in radii (same on both sides)
        self.cap = None
        self.cap_x = PANEL_X
        self._safe_seen = set()

    def th(self):
        return self.TH.get_value()

    def R(self):
        return self.RR.get_value()

    def O(self):
        return np.array([self.OX.get_value(), self.OY.get_value(), 0.0])

    def pt(self, x, y):
        return self.O() + self.R() * np.array([x, y, 0.0])

    def P(self):
        return self.pt(np.cos(self.th()), np.sin(self.th()))

    def Q(self):
        return self.pt(np.cos(self.th()), 0)

    def E(self):  # where the tangent line meets the x-axis
        return self.pt(1 / np.cos(self.th()), 0)

    def F(self):  # where the tangent line meets the y-axis
        return self.pt(0, 1 / np.sin(self.th()))

    def u(self):  # outward, along the radius
        return np.array([np.cos(self.th()), np.sin(self.th()), 0.0])

    def t(self):  # along the tangent line, toward E
        return np.array([np.sin(self.th()), -np.cos(self.th()), 0.0])

    def zoom(self, cfg, xr, yu, run_time=1.5):
        self.play(self.RR.animate.set_value(cfg["r"]), self.OX.animate.set_value(cfg["ox"]),
                  self.OY.animate.set_value(cfg["oy"]), self.XR.animate.set_value(xr),
                  self.YU.animate.set_value(yu), run_time=run_time)

    # --- captions and a safe-area check --------------------------------------------------
    def caption(self, *parts):
        mobs = [Text(p, font_size=CAPTION_SIZE) if isinstance(p, str) else p for p in parts]
        new = VGroup(*mobs).arrange(RIGHT, buff=0.18)
        width = SAFE_X - self.cap_x
        if new.width > width:
            new.scale_to_fit_width(width)
        new.move_to([self.cap_x + new.width / 2, CAPTION_Y, 0])
        if self.cap is None:
            self.play(FadeIn(new, shift=0.15 * DOWN), run_time=0.7)
        else:
            # old caption leaves first, then the new one arrives (a crossfade smears both texts)
            self.play(FadeOut(self.cap, shift=0.15 * UP), run_time=0.4)
            self.play(FadeIn(new, shift=0.15 * DOWN), run_time=0.5)
        self.cap = new

    def play(self, *args, **kwargs):
        result = super().play(*args, **kwargs)
        for m in self.mobjects:
            if isinstance(m, ValueTracker) or m.width == 0 and m.height == 0:
                continue
            over = max(m.get_right()[0] - SAFE_X, -SAFE_X - m.get_left()[0],
                       m.get_top()[1] - SAFE_Y, -SAFE_Y - m.get_bottom()[1])
            if over > 0.05 and id(m) not in self._safe_seen:
                self._safe_seen.add(id(m))
                print(f"LAYOUT t={self.renderer.time:.1f}s SAFE-AREA {type(m).__name__} "
                      f"at ({m.get_x():.2f}, {m.get_y():.2f}) exceeds the safe area by {over:.2f}",
                      flush=True)
        return result

    # --- label placement rules -----------------------------------------------------------
    def place_one(self, m):
        n = np.array([-np.sin(self.th()), np.cos(self.th()), 0.0])
        m.move_to((self.O() + self.P()) / 2 + (0.12 + support(m, n)) * n)

    def place_theta(self, m):
        a = self.th() / 2
        m.move_to(self.O() + (self.arc_r() + 0.35) * np.array([np.cos(a), np.sin(a), 0.0]))

    def arc_r(self):
        return 0.16 * self.R()

    def place_cos(self, m):
        o = self.O()
        x = max(o[0] + self.R() * np.cos(self.th()) / 2, o[0] + 0.12 + m.width / 2)
        m.move_to([x, o[1] - 0.12 - m.height / 2, 0])

    def place_sin(self, m):
        q = self.Q()
        m.move_to([q[0] + 0.08 + m.width / 2, self.O()[1] + 0.3, 0])

    def place_outside(self, m, a, b):
        m.move_to((a + b) / 2 + (0.15 + support(m, self.u())) * self.u())

    def place_sec(self, m):
        e = self.E()
        m.move_to([e[0] + 0.18 + m.width / 2, e[1] - SEC_DROP, 0])

    def place_csc(self, m):
        o = self.O()
        m.move_to([o[0] - 0.15 - m.width / 2, o[1] + self.R() / np.sin(self.th()) / 2, 0])

    def right_angle_mark(self):
        s = 0.09 * self.R()
        p, u, t = self.P(), self.u(), self.t()
        return VMobject(color=C_ONE, stroke_width=2).set_points_as_corners(
            [p - s * u, p - s * u + s * t, p + s * t])

    def sec_dimension(self):
        o, e = self.O(), self.E()
        y = o[1] - SEC_DROP
        bar = Line([o[0], y, 0], [e[0], y, 0], color=C_SEC, stroke_width=SEG_W)
        ticks = VGroup(*[Line([x, y - 0.12, 0], [x, y + 0.12, 0], color=C_SEC, stroke_width=3)
                         for x in (o[0], e[0])])
        tie = DashedLine(e, [e[0], y, 0], color=C_SCAFFOLD, stroke_width=2, dash_length=0.08)
        return VGroup(tie, bar, ticks)

    def triangle(self, a, b, c):
        """A copy of the small triangle O, Q, P: cos leg, sin leg, radius 1."""
        return VGroup(Polygon(a, b, c, stroke_width=0, fill_color=WHITE, fill_opacity=0.15),
                      Line(a, b, color=C_COS, stroke_width=9),
                      Line(b, c, color=C_SIN, stroke_width=9),
                      Line(a, c, color=C_ONE, stroke_width=9))

    def geo_layout(self, which, drawing=None):
        """Point the layout-specific rule names at the figure for the current layout only."""
        fig = VGroup(self.x_axis, self.y_axis, self.circle)
        none = VGroup()
        self.geo_track(figure_home=fig if which == "home" else none,
                       figure_wide=fig if which == "wide" else none)
        if drawing is not None:
            self._geo_drawing = drawing
        if getattr(self, "_geo_drawing", None) is not None:
            self.geo_track(drawing_home=self._geo_drawing if which == "home" else none,
                           drawing_wide=self._geo_drawing if which == "wide" else none)

    # --- beats ---------------------------------------------------------------------------
    def beat_circle(self):
        """Beat 1: a circle of radius 1, and a point that can be anywhere on it."""
        self.x_axis = always_redraw(lambda: Line(
            self.O() + LEFT * self.R() * self.XR.get_value(),
            self.O() + RIGHT * self.R() * self.XR.get_value(), color=C_SCAFFOLD, stroke_width=2))
        self.y_axis = always_redraw(lambda: Line(
            self.O() + DOWN * self.R() * self.YU.get_value(),
            self.O() + UP * self.R() * self.YU.get_value(), color=C_SCAFFOLD, stroke_width=2))
        self.circle = always_redraw(lambda: Circle(radius=self.R(), color=C_SCAFFOLD,
                                                   stroke_width=3).move_to(self.O()))
        self.geo_track(circle=self.circle, x_axis=self.x_axis, y_axis=self.y_axis)
        self.geo_rule(concentric("circle", "x_axis", "y_axis"),
                      symmetric("x_axis", about="circle", axis="x"),
                      symmetric("y_axis", about="circle", axis="y"),
                      within_margin("figure_home", pct=7), centered_in("figure_home", region=HOME_REGION),
                      within_margin("figure_wide", pct=7), centered_in("figure_wide", region=WIDE_REGION),
                      within_margin("drawing_home", pct=7), within_margin("drawing_wide", pct=7))
        self.geo_layout("home")
        self.radius = always_redraw(lambda: Line(self.O(), self.P(), color=C_ONE, stroke_width=4))
        self.dot = always_redraw(lambda: Dot(self.P(), radius=0.08, color=C_ONE).set_z_index(5))
        self.one = label("1", C_ONE)
        self.one.add_updater(lambda m: self.place_one(m))
        self.one.update()

        self.play(Create(self.x_axis), Create(self.y_axis), run_time=1.2)
        self.play(Create(self.circle), run_time=1.5)
        self.caption("A circle of radius 1")
        self.play(Create(self.radius), FadeIn(self.dot))
        self.play(FadeIn(self.one))
        self.wait(1)
        self.play(self.TH.animate.set_value(TAU), run_time=3.5)
        self.TH.set_value(0)   # same position, so nothing jumps
        self.wait(0.5)

    def beat_angle(self):
        """Beat 2: the point is set by one number, the angle."""
        self.arc = always_redraw(lambda: Arc(radius=self.arc_r(), start_angle=0, angle=max(self.th(), 1e-3),
                                             arc_center=self.O(), color=C_ONE, stroke_width=3))
        self.theta_lbl = label(r"\theta", C_ONE)
        self.theta_lbl.add_updater(lambda m: self.place_theta(m))
        self.caption("Turn by an angle")
        self.add(self.arc)
        self.play(self.TH.animate.set_value(THETA0), run_time=2)
        self.theta_lbl.update()
        self.play(FadeIn(self.theta_lbl))
        self.wait(1.2)

    def beat_cos(self):
        """Beat 3: cos θ is how far across the point is."""
        self.caption("How far across?")
        self.drop = DashedLine(self.P(), self.Q(), color=C_SCAFFOLD, stroke_width=2)
        self.play(Create(self.drop), run_time=0.8)
        self.cos_seg = always_redraw(lambda: Line(self.O(), self.Q(), color=C_COS,
                                                  stroke_width=SEG_W))
        self.play(Create(self.cos_seg), run_time=1.2)
        self.cos_lbl = label(r"\cos\theta", C_COS)
        self.cos_lbl.add_updater(lambda m: self.place_cos(m))
        self.cos_lbl.update()
        self.play(FadeIn(self.cos_lbl, shift=0.1 * DOWN))
        self.wait(1.2)

    def beat_sin(self):
        """Beat 4: sin θ is how far up; so the point is (cos θ, sin θ)."""
        self.caption("How far up?")
        self.sin_seg = always_redraw(lambda: Line(self.Q(), self.P(), color=C_SIN,
                                                  stroke_width=SEG_W))
        self.play(Create(self.sin_seg), FadeOut(self.drop), run_time=1.2)
        self.sin_lbl = label(r"\sin\theta", C_SIN)
        self.sin_lbl.add_updater(lambda m: self.place_sin(m))
        self.sin_lbl.update()
        self.play(FadeIn(self.sin_lbl, shift=0.1 * RIGHT))
        self.wait(0.8)

        self.coords = tex("(", r"\cos\theta", ",", r"\sin\theta", ")", size=LABEL_SIZE)
        self.coords.add_updater(lambda m: m.next_to(self.P(), UR, buff=0.12))
        self.coords.update()
        c = self.coords
        # Rigid copies of the two labels travel into place (TransformFromCopy morphed them point by
        # point: doubled, smeared glyphs mid-way); the brackets arrive once they have landed.
        cos_c = self.cos_lbl.copy().clear_updaters()
        sin_c = self.sin_lbl.copy().clear_updaters()
        # rush_from: they leave their originals at once (a slow start reads as a doubled label)
        self.play(cos_c.animate.move_to(c[1]), sin_c.animate.move_to(c[3]), run_time=1.1,
                  rate_func=rush_from)
        brackets = VGroup(c[0], c[2], c[4])
        self.play(FadeIn(brackets), run_time=0.4)
        self.remove(cos_c, sin_c, brackets)
        self.add(c)
        self.wait(1.5)

    def readout(self, name, value_fn, colour, size, places=2, unit=None):
        lhs = tex(name, "=", size=size)
        num = DecimalNumber(value_fn(), num_decimal_places=places, unit=unit,
                            font_size=size, color=colour)
        num.add_updater(lambda m: m.set_value(value_fn()).next_to(lhs, RIGHT, buff=0.2))
        num.next_to(lhs, RIGHT, buff=0.2)
        return VGroup(lhs, num)

    def beat_sweep_sin_cos(self):
        """Beat 5: both lengths change as the point moves."""
        self.caption("Move the point")
        rows = VGroup(
            self.readout(r"\theta", lambda: self.th() / DEGREES, C_ONE, EQ_SIZE, 0, r"^\circ"),
            self.readout(r"\cos\theta", lambda: np.cos(self.th()), C_COS, EQ_SIZE),
            self.readout(r"\sin\theta", lambda: np.sin(self.th()), C_SIN, EQ_SIZE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        rows.move_to([PANEL_X + rows.width / 2, 2.1 - rows.height / 2 + 0.25, 0])
        labels = [self.one, self.theta_lbl, self.cos_lbl, self.sin_lbl]
        self.play(FadeOut(*labels), FadeIn(rows))
        self.play(self.TH.animate.set_value(80 * DEGREES), run_time=2.5)
        self.wait(0.5)
        self.play(self.TH.animate.set_value(20 * DEGREES), run_time=4)
        self.wait(0.5)
        self.play(self.TH.animate.set_value(THETA0), run_time=2.5)
        for row in rows:
            row[1].clear_updaters()
        self.play(FadeOut(rows), FadeIn(*labels))
        self.wait(0.8)

    def beat_pythagoras(self):
        """Beat 6: a right triangle with long side 1, so sin² + cos² = 1."""
        self.caption("Pythagoras: long side 1")
        fill = Polygon(self.O(), self.Q(), self.P(), stroke_width=0, fill_color=WHITE,
                       fill_opacity=0.15)
        self.row1 = tex(r"\sin^2\theta", "+", r"\cos^2\theta", "=", "1")
        self.row1.move_to([PANEL_X + self.row1.width / 2, 2.1, 0])
        self.play(FadeIn(fill))
        self.play(Write(self.row1), run_time=1.5)
        self.play(Indicate(self.one, color=WHITE), Indicate(self.row1[4], color=WHITE))
        self.wait(1.5)
        self.play(FadeOut(fill))

    def beat_tangent_line(self):
        """Beat 7: the tangent line touches the circle at the point, at a right angle."""
        self.caption("Four more, on one line")
        self.play(FadeOut(self.coords), self.XR.animate.set_value(XR_TAN),
                  self.YU.animate.set_value(YU_TAN), run_time=1)
        self.tangent = always_redraw(lambda: Line(self.F() - 0.35 * self.t(),
                                                  self.E() + 0.35 * self.t(),
                                                  color=C_SCAFFOLD, stroke_width=3))
        self.play(GrowFromPoint(self.tangent, self.P()), run_time=1.5)
        self.mark = always_redraw(self.right_angle_mark)
        self.play(Create(self.mark), run_time=0.8)
        self.wait(1.2)

    def beat_tan(self):
        """Beat 8: tan θ is the piece of the tangent line down to the x-axis."""
        self.caption("Along it, to the x-axis")
        self.tan_seg = always_redraw(lambda: Line(self.P(), self.E(), color=C_TAN,
                                                  stroke_width=SEG_W))
        self.play(Create(self.tan_seg), run_time=1.2)
        self.tan_lbl = label(r"\tan\theta", C_TAN)
        self.tan_lbl.add_updater(lambda m: self.place_outside(m, self.P(), self.E()))
        self.tan_lbl.update()
        self.play(FadeIn(self.tan_lbl))
        self.wait(1.2)

    def beat_sec(self):
        """Beat 9: sec θ is the distance from the centre to that crossing."""
        self.caption("Centre to that crossing")
        self.sec_dim = always_redraw(self.sec_dimension)
        self.play(Create(self.sec_dim), run_time=1.2)
        self.sec_lbl = label(r"\sec\theta", C_SEC)
        self.sec_lbl.add_updater(lambda m: self.place_sec(m))
        self.sec_lbl.update()
        self.play(FadeIn(self.sec_lbl))
        self.wait(1.2)

    def beat_cot(self):
        """Beat 10: cot θ is the piece of the same line up to the y-axis."""
        self.caption("Same line, other axis")
        self.cot_seg = always_redraw(lambda: Line(self.P(), self.F(), color=C_COT,
                                                  stroke_width=SEG_W))
        self.play(Create(self.cot_seg), run_time=1.2)
        self.cot_lbl = label(r"\cot\theta", C_COT)
        self.cot_lbl.add_updater(lambda m: self.place_outside(m, self.P(), self.F()))
        self.cot_lbl.update()
        self.play(FadeIn(self.cot_lbl))
        self.wait(1.2)

    def beat_csc(self):
        """Beat 11: csc θ is the distance from the centre to the y-axis crossing."""
        self.caption("Centre to that crossing")
        self.csc_seg = always_redraw(lambda: Line(self.O(), self.F(), color=C_CSC,
                                                  stroke_width=SEG_W))
        self.play(Create(self.csc_seg), run_time=1.2)
        self.csc_lbl = label(r"\csc\theta", C_CSC)
        self.csc_lbl.add_updater(lambda m: self.place_csc(m))
        self.csc_lbl.update()
        self.play(FadeIn(self.csc_lbl))
        self.geo_layout("home", drawing=VGroup(
            self.x_axis, self.y_axis, self.circle, self.radius, self.dot, self.arc, self.tangent,
            self.mark, self.cos_seg, self.sin_seg, self.tan_seg, self.cot_seg, self.csc_seg,
            self.sec_dim, self.one, self.theta_lbl, self.cos_lbl, self.sin_lbl, self.tan_lbl,
            self.sec_lbl, self.cot_lbl, self.csc_lbl))
        self.wait(1.5)

    def flash_copy(self, seg):
        """A fresh white line over a segment (or the bar of the sec dimension), for a flash."""
        line = seg[1] if isinstance(seg, VGroup) and len(seg) == 3 else seg
        return Line(line.get_start(), line.get_end(), color=WHITE, stroke_width=10)

    def side_flash(self, side):
        """Highlight one side of a triangle copy without moving it (Indicate would stretch it)."""
        flash = Line(side.get_start(), side.get_end(), color=WHITE, stroke_width=12).set_z_index(3)
        return ShowPassingFlash(flash, time_width=0.6)

    def panel_row(self, row, y, eq_x):
        row.shift(RIGHT * (eq_x - row[1].get_x()) + UP * (y - row.get_y()))
        return row

    def beat_ratio_cos(self):
        """Beat 12: the small triangle, flipped and scaled by 1/cos θ, is the tan/sec triangle."""
        o, q, p = self.O(), self.Q(), self.P()
        th = self.th()
        self.rows = VGroup(
            tex(r"\tan\theta", "=", r"\sin\theta", "/", r"{\cos\theta}"),
            tex(r"\sec\theta", "=", "1", "/", r"{\cos\theta}"),
            tex(r"\cot\theta", "=", r"\cos\theta", "/", r"{\sin\theta}"),
            tex(r"\csc\theta", "=", "1", "/", r"{\sin\theta}"),
        )
        eq_x = PANEL_X + max(r[0].width for r in self.rows) + 0.3
        for row, y in zip(self.rows, (1.15, 0.45, -0.25, -0.95)):
            self.panel_row(row, y, eq_x)

        self.caption("Same shape, just bigger")
        tri = self.triangle(o, q, p)
        self.play(FadeIn(tri))
        self.wait(0.5)
        axis = np.array([np.cos(th / 2), np.sin(th / 2), 0.0])
        # the flipped copy's sin side would run through the "sin θ" label: hide it meanwhile
        self.play(Rotate(tri, angle=PI, axis=axis, about_point=o), FadeOut(self.sin_lbl), run_time=1.6)
        self.wait(0.6)
        self.caption("Stretch until", tex(r"\cos\theta"), "is 1")
        self.play(tri.animate.scale(1 / np.cos(th), about_point=o), run_time=1.6)
        self.play(FadeIn(self.sin_lbl), run_time=0.8)
        self.play(Write(self.rows[0]), self.side_flash(tri[2]), run_time=1.3)
        self.wait(0.6)
        self.play(Write(self.rows[1]), self.side_flash(tri[3]), run_time=1.3)
        self.wait(1.5)
        self.play(FadeOut(tri))

    def beat_ratio_sin(self):
        """Beat 13: same trick from the y-axis: scale by 1/sin θ to get cot and csc."""
        o, q, p = self.O(), self.Q(), self.P()
        th = self.th()
        self.caption("Same trick, other axis")
        tri = self.triangle(o, q, p)
        self.play(FadeIn(tri))
        self.play(Rotate(tri, angle=PI, about_point=(o + p) / 2), run_time=1.4)
        self.wait(0.5)
        axis = np.array([np.cos((th + PI / 2) / 2), np.sin((th + PI / 2) / 2), 0.0])
        self.play(Rotate(tri, angle=PI, axis=axis, about_point=o), run_time=1.6)
        self.wait(0.6)
        self.caption("Stretch until", tex(r"\sin\theta"), "is 1")
        self.play(tri.animate.scale(1 / np.sin(th), about_point=o), run_time=1.6)
        self.wait(0.8)
        self.play(Write(self.rows[2]), self.side_flash(tri[1]), run_time=1.3)
        self.wait(0.6)
        self.play(Write(self.rows[3]), self.side_flash(tri[3]), run_time=1.3)
        self.wait(1.5)
        self.play(FadeOut(tri))

    def beat_extremes(self):
        """Beat 14: near 90° tan and sec run away; near 0° cot and csc do."""
        self.labels = [self.one, self.theta_lbl, self.cos_lbl, self.sin_lbl, self.tan_lbl,
                       self.sec_lbl, self.cot_lbl, self.csc_lbl]
        panel = VGroup(self.row1, *self.rows)
        self.cap_x = RD_X
        self.caption("Toward 90°")
        self.play(FadeOut(*self.labels), FadeOut(panel), run_time=0.8)
        self.geo_layout("wide")
        self.zoom(WIDE, xr=XR_WIDE, yu=YU_WIDE)

        def rd(name, fn, col):
            return self.readout(name, fn, col, READOUT_SIZE)
        th = self.th
        grid = VGroup(
            rd(r"\sin\theta", lambda: np.sin(th()), C_SIN),
            rd(r"\cos\theta", lambda: np.cos(th()), C_COS),
            rd(r"\tan\theta", lambda: np.tan(th()), C_TAN),
            rd(r"\cot\theta", lambda: 1 / np.tan(th()), C_COT),
            rd(r"\sec\theta", lambda: 1 / np.cos(th()), C_SEC),
            rd(r"\csc\theta", lambda: 1 / np.sin(th()), C_CSC),
        )
        col_gap = max(g.width for g in grid) + 0.45
        for i, g in enumerate(grid):
            g.move_to([RD_X + (i % 2) * col_gap + g.width / 2, 1.8 - (i // 2) * 0.55, 0])
        theta_row = self.readout(r"\theta", lambda: th() / DEGREES, C_ONE, READOUT_SIZE, 0, r"^\circ")
        theta_row.move_to([RD_X + theta_row.width / 2, 2.38, 0])
        readouts = VGroup(theta_row, grid)
        self.play(FadeIn(readouts))
        self.wait(0.5)
        self.play(self.TH.animate.set_value(80 * DEGREES), run_time=3.5)
        self.wait(0.5)
        self.caption(tex(r"\theta \to 90^\circ\colon", r"\tan\theta", ",", r"\sec\theta", r"\to \infty"))
        self.wait(1.5)
        self.caption("Toward 0°")
        self.play(self.TH.animate.set_value(20 * DEGREES), run_time=5)
        self.wait(0.5)
        self.caption(tex(r"\theta \to 0^\circ\colon", r"\cot\theta", ",", r"\csc\theta", r"\to \infty"))
        self.wait(1.5)
        self.play(self.TH.animate.set_value(THETA0), run_time=2.5)
        for row in [theta_row, *grid]:
            row[1].clear_updaters()
        self.play(FadeOut(readouts), run_time=0.8)
        self.geo_layout("home")
        self.zoom(HOME, xr=XR_TAN, yu=YU_TAN)
        self.cap_x = PANEL_X
        self.panel = panel

    def beat_recap(self):
        """Beat 15: six lengths, one picture."""
        self.caption("Six lengths, one circle")
        self.play(FadeIn(*self.labels), FadeIn(self.panel))
        self.wait(1)
        pairs = [
            ([self.sin_seg, self.sin_lbl, self.cos_seg, self.cos_lbl], [self.row1]),
            ([self.tan_seg, self.tan_lbl, self.cot_seg, self.cot_lbl], [self.rows[0], self.rows[2]]),
            ([self.sec_dim, self.sec_lbl, self.csc_seg, self.csc_lbl], [self.rows[1], self.rows[3]]),
        ]
        for (mobs, rows), cols in zip(pairs, ([C_SIN, C_SIN, C_COS, C_COS],
                                              [C_TAN, C_TAN, C_COT, C_COT],
                                              [C_SEC, C_SEC, C_CSC, C_CSC])):
            boxes = [SurroundingRectangle(r, buff=0.12, corner_radius=0.08, color=GREY_B,
                                          stroke_width=2) for r in rows]
            segs, lbls = mobs[0::2], mobs[1::2]
            flashes = [ShowPassingFlash(self.flash_copy(m), time_width=0.6) for m in segs]
            self.play(*flashes, *[Indicate(m, color=c, scale_factor=1.15)
                                  for m, c in zip(lbls, cols[1::2])],
                      *[Create(b) for b in boxes], run_time=1.4)
            self.wait(0.6)
            self.play(*[FadeOut(b) for b in boxes], run_time=0.5)
        self.wait(2.5)
        everything = [m for m in self.mobjects if not isinstance(m, ValueTracker)]
        for m in everything:
            m.clear_updaters()
        self.play(FadeOut(*everything), run_time=1.2)
        self.wait(0.5)
