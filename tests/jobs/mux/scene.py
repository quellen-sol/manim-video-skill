from manim import *
from narration_timeline import Timeline

TL = Timeline()  # in the container: the timeline manim-job synthesized ($NARRATION_TIMELINE)


class Muxed(Scene):
    def construct(self):
        TL.sync(self, "intro")
        sq = Square(side_length=3, color=GREEN)
        self.play(Create(sq), run_time=TL.speech("intro"))
        TL.sync(self, "turn")
        self.play(Rotate(sq, PI / 2), run_time=TL.speech("turn"))
        TL.finish(self)
