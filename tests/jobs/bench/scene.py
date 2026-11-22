from manim import *

# Benchmark scene: rotating vectors drawing a path, a plotted wave, a formula.
# Uses only features that work under both the Cairo and the OpenGL renderer.
N = 24


class Bench(Scene):
    def construct(self):
        t = ValueTracker(0)
        center = LEFT * 3
        coeffs = [(k, 1.6 / (k * k)) for k in range(1, 2 * N, 2)]

        def tips():
            p = center.copy()
            pts = [p.copy()]
            for k, r in coeffs:
                p = p + r * np.array([np.cos(k * t.get_value()), np.sin(k * t.get_value()), 0])
                pts.append(p.copy())
            return pts

        def arms():
            pts = tips()
            g = VGroup()
            for (k, r), a, b in zip(coeffs, pts[:-1], pts[1:]):
                g.add(Circle(radius=r, stroke_width=1, stroke_opacity=0.4, color=BLUE).move_to(a))
                g.add(Line(a, b, stroke_width=2, color=WHITE))
            return g

        rig = always_redraw(arms)
        # TracedPath, not a bare VMobject(): a bare VMobject breaks the OpenGL renderer.
        path = TracedPath(lambda: tips()[-1], stroke_color=YELLOW, stroke_width=3)
        ax = Axes(x_range=[0, 7, 1], y_range=[-2, 2, 1], x_length=5, y_length=3).shift(RIGHT * 3.5 + DOWN * 0.5)
        wave = always_redraw(lambda: ax.plot(lambda x: np.sin(3 * x + t.get_value()), x_range=[0, 7], color=RED))
        formula = MathTex(r"f(t)=\sum_{k\ \mathrm{odd}} \frac{1}{k^2} e^{ikt}", font_size=40).to_edge(UP)
        self.add(rig, path, ax, wave)
        self.play(Write(formula), run_time=1)
        self.play(t.animate.set_value(2 * PI), run_time=8, rate_func=linear)
        path.clear_updaters()
        self.wait(1)
