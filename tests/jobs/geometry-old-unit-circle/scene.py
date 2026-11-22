"""Regression fixture: the ORIGINAL unit-circle layout (examples/01-unit-circle at 9641aa2, beat_circle).

Same constants and axis construction as that scene: centre (-3.8, -0.8), radius 2.5, the x axis
from O + LEFT*(R + 0.1) to O + RIGHT*R*XR and the y axis from O + DOWN*(R + 0.1) to O + UP*R*YU,
with XR = YU = 1.25 growing to 2.05 and 1.35. The circle sits at the crossing, but the axes reach
much further on one side, and the figure is about 5% from the left edge of the frame.
GeometryGuard must report these (tests/test_geometry.py).
"""
from manim import *
from geometry_qa import GeometryGuard, concentric, symmetric, within_margin

HOME = {"ox": -3.8, "oy": -0.8, "r": 2.5}


class OldLayout(GeometryGuard, Scene):
    def construct(self):
        R = HOME["r"]
        O = np.array([HOME["ox"], HOME["oy"], 0.0])
        XR, YU = ValueTracker(1.25), ValueTracker(1.25)
        x_axis = always_redraw(lambda: Line(O + LEFT * (R + 0.1), O + RIGHT * R * XR.get_value(), stroke_width=2))
        y_axis = always_redraw(lambda: Line(O + DOWN * (R + 0.1), O + UP * R * YU.get_value(), stroke_width=2))
        circle = Circle(radius=R, stroke_width=3).move_to(O)
        figure = VGroup(x_axis, y_axis, circle)
        self.geo_track(circle=circle, x_axis=x_axis, y_axis=y_axis, figure=figure)
        self.geo_rule(concentric("circle", "x_axis", "y_axis"),
                      symmetric("x_axis", about="circle", axis="x"),
                      symmetric("y_axis", about="circle", axis="y"),
                      within_margin("figure", pct=6))
        self.play(Create(x_axis), Create(y_axis), run_time=0.5)
        self.play(Create(circle), run_time=0.5)
        self.wait(0.5)
        self.play(XR.animate.set_value(2.05), YU.animate.set_value(1.35), run_time=0.5)
        self.wait(0.5)
