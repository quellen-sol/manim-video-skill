from manim import *
from manim_qa import LayoutGuard

Text.set_default(font="Noto Sans")


class Smoke(LayoutGuard, Scene):
    def construct(self):
        title = Text("Container smoke test", font_size=44).to_edge(UP, buff=0.5)
        euler = MathTex(r"e^{i\pi} + 1 = 0", font_size=60)
        integral = MathTex(r"\int_0^1 x^2\,dx = \frac{1}{3}", r"\quad \sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}")
        tex = Tex(r"Text mode: $\alpha + \beta$ and \textbf{bold}", font_size=36)
        VGroup(euler, integral, tex).arrange(DOWN, buff=0.5).next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(Write(euler))
        self.play(FadeIn(integral, shift=UP * 0.3))
        self.play(Write(tex))
        self.wait(1)
        self.play(FadeOut(VGroup(euler, integral, tex)))
        ax = Axes(x_range=[0, 6.3, 1], y_range=[-1.2, 1.2, 1], x_length=8, y_length=3).shift(DOWN * 0.5)
        curve = ax.plot(np.sin, color=BLUE)
        self.play(Create(ax), Create(curve), run_time=1.5)
        self.wait(1)
        self.play(FadeOut(ax, curve, title))
