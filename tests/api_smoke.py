"""Exercise the API claims in references/api-cheatsheet.md (render: render.sh preview tests/api_smoke.py -a)."""
from manim import *

config.background_color = "#0F1117"
Text.set_default(font="Noto Sans")


class TextAndShapes(Scene):
    def construct(self):
        items = VGroup(
            Text("Hello", font_size=36, color=BLUE),
            Text("tan θ", t2c={"tan": YELLOW}),
            MarkupText('<span fgcolor="#58C4DD">sin</span> wave'),
            Paragraph("line one", "line two", alignment="left", font_size=28),
            MathTex(r"\sin^2\theta + \cos^2\theta = 1"),
            MathTex(r"\tan\theta", "=", r"\frac{\sin\theta}{\cos\theta}"),
            MathTex(r"{{a}}^2 + {{b}}^2 = {{c}}^2"),
            MathTex(r"y = mx + b", substrings_to_isolate=["m", "b"]).set_color_by_tex("m", YELLOW),
            Tex(r"A \textbf{bold} claim"),
            DecimalNumber(0.5, num_decimal_places=2, font_size=36),
            Integer(3),
            BulletedList("first", "second", font_size=32),
            Code(code_string="git commit -m 'msg'", language="bash", background="window",
                 paragraph_config={"font": "Noto Mono"}),
        )
        eq = MathTex(r"\sin\theta", "+", r"\cos\theta"); eq[0].set_color(BLUE)
        items.add(eq, Title("Section title"))
        items.arrange_in_grid(rows=4, buff=0.3).scale_to_fit_width(13)
        self.play(LaggedStart(*[FadeIn(m) for m in items], lag_ratio=0.05))
        self.play(FadeOut(items))
        a, b = LEFT * 2, RIGHT * 2
        l1, l2 = Line(ORIGIN, RIGHT), Line(ORIGIN, UP)
        sq = Square(side_length=2)
        shapes = VGroup(
            Dot(ORIGIN, radius=0.08, color=WHITE), LabeledDot("A"), Circle(radius=1, color=BLUE),
            Ellipse(width=3, height=1.5), sq, Rectangle(width=4, height=2),
            RoundedRectangle(corner_radius=0.2, width=3, height=1), Polygon(ORIGIN, RIGHT, UP),
            RegularPolygon(n=6), Triangle(), Star(), Arc(radius=1, start_angle=0, angle=PI / 3),
            Sector(radius=1, angle=PI / 4), Annulus(inner_radius=1, outer_radius=1.5),
            Line(a, b), DashedLine(a, b), Arrow(a, b, buff=0), DoubleArrow(a, b), Vector([2, 1]),
            CurvedArrow(a, b, angle=-PI / 4), ArcBetweenPoints(a, b, angle=PI / 3),
            VGroup(l1, l2, Angle(l1, l2, radius=0.5, other_angle=False), RightAngle(l1, l2, length=0.3)),
            Brace(sq, direction=DOWN), BraceLabel(sq, r"\Delta x"),
            SurroundingRectangle(sq, color=YELLOW, buff=0.1, corner_radius=0.1), BackgroundRectangle(sq),
            Cross(sq), Underline(sq),
        )
        shapes.add(Brace(sq, direction=DOWN).get_text("width"))
        shapes.arrange_in_grid(rows=4, buff=0.3).scale_to_fit_width(13)
        self.play(Create(shapes), run_time=2)
        self.play(FadeOut(shapes))


class GraphsAndAnims(Scene):
    def construct(self):
        axes = Axes(x_range=[-1, 7, 1], y_range=[-1.5, 1.5, 0.5], x_length=9, y_length=4,
                    axis_config={"include_numbers": False, "color": GREY_B}, tips=False)
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        sine = axes.plot(lambda x: np.sin(x), x_range=[0, TAU], color=BLUE)
        lab = axes.get_graph_label(sine, label=r"\sin x", x_val=2, direction=UP)
        v = axes.get_vertical_line(axes.c2p(2, np.sin(2)))
        area = axes.get_area(sine, x_range=[0, PI], color=BLUE, opacity=0.3)
        rects = axes.get_riemann_rectangles(sine, x_range=[0, PI], dx=0.25)
        _ = axes.p2c(axes.c2p(1, 0.5))
        self.play(Create(axes), FadeIn(labels), Create(sine), Write(lab), Create(v), FadeIn(area), FadeIn(rects))
        self.play(FadeOut(VGroup(axes, labels, sine, lab, v, area, rects)))
        others = VGroup(NumberPlane(background_line_style={"stroke_opacity": 0.4}).scale(0.3),
                        NumberLine(x_range=[0, 10, 1], length=10, include_numbers=True).scale(0.4),
                        ParametricFunction(lambda t: np.array([np.cos(t), np.sin(t), 0]), t_range=[0, TAU]),
                        FunctionGraph(lambda x: x ** 2, x_range=[-2, 2]),
                        Graph([1, 2, 3], [(1, 2), (2, 3)], layout="circular", labels=True),
                        Table([["1", "2"], ["3", "4"]], col_labels=[Text("a"), Text("b")]).scale(0.4),
                        Matrix([[1, 0], [0, 1]])).arrange_in_grid(rows=2, buff=0.4).scale_to_fit_width(12)
        self.play(FadeIn(others))
        self.play(FadeOut(others))
        m, t1 = Square(), Text("typing")
        a2, b2 = Circle(), Square().shift(RIGHT)
        e1, e2 = MathTex(r"{{a}}^2"), MathTex(r"{{a}}^3")
        self.play(Create(m)); self.play(Uncreate(m))
        m = Square()  # Uncreate collapses m to zero size; use a fresh object
        self.play(Write(t1)); self.play(Unwrite(t1))
        self.play(FadeIn(m, shift=UP, scale=0.8)); self.play(FadeOut(m, shift=DOWN))
        self.play(DrawBorderThenFill(Square())); self.clear()
        self.play(GrowFromCenter(m)); self.play(GrowArrow(Arrow(LEFT, RIGHT)))
        self.play(SpinInFromNothing(Square())); self.play(GrowFromPoint(Circle(), UP))
        self.clear()
        self.play(Transform(a2, b2)); self.play(ReplacementTransform(a2, Circle()))
        self.clear()
        self.play(TransformMatchingTex(e1, e2)); self.play(TransformMatchingShapes(Text("abc"), Text("cab")))
        self.play(FadeTransform(Square(), Circle()))
        self.play(m.animate.shift(RIGHT).set_color(RED)); self.play(m.animate(run_time=2, rate_func=smooth).scale(2))
        self.play(Rotate(m, angle=PI / 2, about_point=ORIGIN))
        self.play(MoveAlongPath(Dot(), Circle())); self.play(Indicate(m)); self.play(Circumscribe(m))
        self.play(Flash(ORIGIN)); self.play(Wiggle(m)); self.play(FocusOn(ORIGIN)); self.play(ShowPassingFlash(m.copy()))
        self.play(ApplyWave(m)); self.play(Broadcast(Circle()))
        items = VGroup(*[Dot() for _ in range(3)]).arrange(RIGHT)
        self.play(LaggedStart(*[FadeIn(x) for x in items], lag_ratio=0.2))
        self.play(AnimationGroup(FadeOut(items[0]), FadeOut(items[1]), lag_ratio=0.5))
        self.play(Succession(FadeOut(items[2]), FadeOut(m)))
        self.play(AddTextLetterByLetter(Text("typing")))
        number = DecimalNumber(0)
        self.play(ChangeDecimalToValue(number, 3.14))
        self.play(Create(Square()), rate_func=there_and_back)
        for rf in (linear, smooth, rush_into, rush_from, double_smooth):
            self.play(m.animate.shift(0.1 * UP), rate_func=rf, run_time=0.2)
        self.wait(0.5)


class Updaters(Scene):
    def construct(self):
        circle = Circle(radius=2)
        theta = ValueTracker(30 * DEGREES)
        dot = always_redraw(lambda: Dot(circle.point_at_angle(theta.get_value()), color=YELLOW))
        radius = always_redraw(lambda: Line(ORIGIN, dot.get_center(), color=BLUE))
        value = always_redraw(lambda: DecimalNumber(np.sin(theta.get_value())).next_to(dot, UR, buff=0.1))
        label = Text("P", font_size=30)
        label.add_updater(lambda m: m.next_to(dot, UP, buff=0.15))
        trail = TracedPath(dot.get_center, stroke_color=YELLOW, stroke_width=3)
        spinner = Square(0.5).to_corner(UL)
        spinner.add_updater(lambda m, dt: m.rotate(dt * 0.5))
        self.add(circle, radius, dot, value, label, trail, spinner)
        self.play(theta.animate.set_value(150 * DEGREES), run_time=2)
        label.clear_updaters()
        self.next_section("sounds")
        self.wait(0.5)


class Zoom(MovingCameraScene):
    def construct(self):
        target = Square(0.5).shift(2 * RIGHT)
        self.add(target)
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.5).move_to(target))
        self.play(Restore(self.camera.frame))


class Space(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
        axes = ThreeDAxes(x_range=[-3, 3], y_range=[-3, 3], z_range=[-2, 2])
        surface = Surface(lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
                          u_range=[-3, 3], v_range=[-3, 3], resolution=(12, 12))
        title = Text("A surface", font_size=36).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)
        self.play(Create(axes), Create(surface))
        self.begin_ambient_camera_rotation(rate=0.2); self.wait(1); self.stop_ambient_camera_rotation()
        self.move_camera(phi=45 * DEGREES, theta=30 * DEGREES, run_time=1)
        self.add(Sphere(radius=0.3), Cube(side_length=0.3), Prism(), Cylinder(radius=0.2, height=0.5),
                 Cone(base_radius=0.2, height=0.5), Arrow3D(ORIGIN, OUT), Line3D(ORIGIN, UP), Dot3D())
        self.wait(0.2)
        _ = (interpolate_color(BLUE, RED, 0.3), ManimColor("#123456"), color_gradient([BLUE, GREEN], 5),
             BLUE_A, BLUE_E, GREY_B, DARK_GREY, TEAL, GOLD, MAROON, PINK)
