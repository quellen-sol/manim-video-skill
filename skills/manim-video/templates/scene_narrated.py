"""<Title>: <one-sentence learning goal>. Narrated with Kokoro through manim-voiceover.

Render: "$SKILL_DIR/scripts/render.sh" preview scene.py Explainer
(render.sh sees VoiceoverScene/KokoroService and lets the renderer reach the TTS server;
clips are cached in media/voiceovers/, so re-renders only synthesize changed sentences.)
"""

from manim import *
from manim_voiceover import VoiceoverScene

from kokoro_service import KokoroService  # on PYTHONPATH when rendered with render.sh

try:
    from manim_qa import LayoutGuard
except ImportError:
    class LayoutGuard:
        pass

config.background_color = "#0F1117"
Text.set_default(font="Noto Sans")
MarkupText.set_default(font="Noto Sans")

C_MAIN = BLUE
C_ACCENT = YELLOW
C_MUTED = GREY_B
LABEL_SIZE = 30


class Explainer(LayoutGuard, VoiceoverScene):
    def construct(self):
        # Voice, model and server come from KOKORO_VOICE / KOKORO_MODEL / KOKORO_BASE_URL.
        self.set_speech_service(KokoroService())
        self.beat_intro()
        self.beat_idea()
        self.wait(0.5)

    def beat_intro(self):
        circle = Circle(radius=2, color=C_MAIN)
        with self.voiceover(text="Start with a circle whose radius is one.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)
        self.circle = circle

    def beat_idea(self):
        dot = Dot(self.circle.point_at_angle(0), color=C_ACCENT)
        label = Text("a point", font_size=LABEL_SIZE, color=C_ACCENT).next_to(dot, RIGHT, buff=0.2)
        with self.voiceover(
            text="Put a point on it. As the point travels around, watch its height."
        ) as tracker:
            # Split one sentence's time across several animations with fractions of the duration.
            self.play(FadeIn(dot, scale=0.5), FadeIn(label), run_time=0.3 * tracker.duration)
            self.play(
                MoveAlongPath(dot, self.circle),
                FadeOut(label),
                run_time=tracker.get_remaining_duration(),
            )
        self.play(FadeOut(self.circle, dot))
