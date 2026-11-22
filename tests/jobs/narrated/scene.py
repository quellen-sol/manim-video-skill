from manim import *
from manim_voiceover import VoiceoverScene
from kokoro_service import KokoroService
from narration_script import line

Text.set_default(font="Noto Sans")


class Narrated(VoiceoverScene):
    def construct(self):
        self.set_speech_service(KokoroService())
        circle = Circle(radius=2, color=BLUE)
        with self.voiceover(text=line("circle")) as tracker:
            self.play(Create(circle), run_time=tracker.duration)
        dot = Dot(circle.point_at_angle(0), color=YELLOW)
        with self.voiceover(text=line("point")) as tracker:
            self.play(FadeIn(dot))
            self.play(MoveAlongPath(dot, circle), run_time=max(tracker.get_remaining_duration(), 1))
        self.wait(0.5)
