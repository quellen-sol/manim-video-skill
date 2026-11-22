"""Regression fixture: the unit-circle layout done right (compare geometry-old-unit-circle).

Axes reach equally far on both sides of the centre (and grow symmetrically), and the figure is
centred in the left half of the frame with a margin of more than 6% on every side.
"""
from manim import *
from geometry_qa import GeometryGuard, centered_in, concentric, symmetric, within_margin

LEFT_HALF = (-config.frame_width / 2, -config.frame_height / 2, 0, config.frame_height / 2)


class FixedLayout(GeometryGuard, Scene):
    def construct(self):
        R = 2.0
        O = np.array([-config.frame_width / 4, 0.0, 0.0])   # centre of the left half
        EXT = ValueTracker(1.25)                            # axis reach, in radii, both ways
        x_axis = always_redraw(lambda: Line(O + LEFT * R * EXT.get_value(), O + RIGHT * R * EXT.get_value(), stroke_width=2))
        y_axis = always_redraw(lambda: Line(O + DOWN * R * EXT.get_value(), O + UP * R * EXT.get_value(), stroke_width=2))
        circle = Circle(radius=R, stroke_width=3).move_to(O)
        figure = VGroup(x_axis, y_axis, circle)
        self.geo_track(circle=circle, x_axis=x_axis, y_axis=y_axis, figure=figure)
        self.geo_rule(concentric("circle", "x_axis", "y_axis"),
                      symmetric("x_axis", about="circle", axis="x"),
                      symmetric("y_axis", about="circle", axis="y"),
                      within_margin("figure", pct=6),
                      centered_in("figure", region=LEFT_HALF))
        self.play(Create(x_axis), Create(y_axis), run_time=0.5)
        self.play(Create(circle), run_time=0.5)
        self.wait(0.5)
        self.play(EXT.animate.set_value(1.3), run_time=0.5)   # 1.4 would leave a 5.3% margin
        self.wait(0.5)
