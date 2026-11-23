"""Parallel-sections traps (tests/test_container.sh renders each with "workers": 2 and serially).

Traced:   a TracedPath and a dt-based updater carry state across the section seams. The workers
          must step those animations frame by frame, so the output equals the serial render.
Stateful: an updater WITHOUT dt moves the square a little on every frame (frame-rate dependent).
          Jumping an animation to its end applies it once instead of once per frame, so the
          seam check or the GeometryGuard cross-check must catch it and render serially.
"""
from manim import *
from geometry_qa import GeometryGuard


class Traced(Scene):
    def construct(self):
        dot = Dot(RIGHT * 2, color=YELLOW)
        path = TracedPath(dot.get_center, stroke_color=YELLOW, stroke_width=6)
        spin = Square(1.5, color=BLUE)
        spin.add_updater(lambda m, dt: m.rotate(0.8 * dt))
        self.add(path, dot, spin)
        for _ in range(6):
            self.play(Rotate(dot, PI / 3, about_point=ORIGIN), run_time=0.8)
        self.wait(0.5)


class Stateful(GeometryGuard, Scene):
    def construct(self):
        sq = Square(1.5, color=GREEN).shift(LEFT * 2)
        sq.add_updater(lambda m: m.shift(RIGHT * 0.01))
        self.add(sq)
        self.geo_track(sq=sq)
        label = Text("frame-rate dependent", font_size=28).to_edge(UP)
        for k in range(6):
            self.play(FadeIn(label) if k == 0 else Indicate(label), run_time=0.8)
        self.wait(0.5)
