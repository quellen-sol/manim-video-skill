"""<Title>: <one-sentence learning goal>.

Render: "$SKILL_DIR/scripts/render.sh" preview scene.py Explainer
"""

from manim import *

try:  # layout checker; on PYTHONPATH when rendered with render.sh
    from manim_qa import LayoutGuard
except ImportError:  # keeps the file renderable without the skill
    print("LAYOUT-GUARD unavailable: manim_qa not importable; layout checks are off", flush=True)

    class LayoutGuard:
        pass

# --- style (references/style-guide.md) -----------------------------------------------
config.background_color = "#0F1117"
Text.set_default(font="Noto Sans")        # the Docker image's default font is a serif
MarkupText.set_default(font="Noto Sans")

# --- colour legend: one colour per concept, used everywhere ---------------------------
C_MAIN = BLUE       # e.g. the object being studied
C_ACCENT = YELLOW   # e.g. the quantity being explained
C_GOOD = GREEN
C_BAD = RED
C_MUTED = GREY_B

TITLE_SIZE = 44
LABEL_SIZE = 30


class Explainer(LayoutGuard, Scene):
    def construct(self):
        self.beat_hook()
        self.beat_build()
        self.beat_recap()

    # Helpers ----------------------------------------------------------------------------
    def swap(self, old, new, run_time=0.35):
        """Replace a caption/title in place: old leaves first, then new arrives (no overlap,
        no scrambled letters). Returns new."""
        if old is not None:
            self.play(FadeOut(old, shift=0.15 * UP), run_time=run_time)
        self.play(FadeIn(new, shift=0.15 * UP), run_time=run_time)
        return new

    def caption(self, text, color=WHITE):
        cap = Text(text, font_size=LABEL_SIZE, color=color).to_edge(DOWN, buff=0.6)
        return cap.scale_to_fit_width(12) if cap.width > 12 else cap

    # One method per storyboard beat ------------------------------------------------------
    def beat_hook(self):
        """Beat 1: a concrete picture the viewer already understands."""
        title = Text("Title of the idea", font_size=TITLE_SIZE).to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.cap = self.swap(None, self.caption("a short caption"))
        self.wait(1)
        self.cap = self.swap(self.cap, self.caption("the next caption"))
        self.wait(1)
        self.play(FadeOut(title, self.cap))

    def beat_build(self):
        """Beat 2: build the diagram piece by piece; one idea per beat."""
        shape = Circle(radius=2, color=C_MAIN)
        label = Text("one idea", font_size=LABEL_SIZE, color=C_ACCENT).next_to(shape, DOWN, buff=0.3)
        self.play(Create(shape), run_time=1.5)
        self.play(FadeIn(label, shift=0.2 * UP))
        self.wait(1.5)
        self.play(FadeOut(shape, label))

    def beat_recap(self):
        """Last beat: tie the pieces together."""
        recap = VGroup(
            Text("1. first point", font_size=LABEL_SIZE),
            Text("2. second point", font_size=LABEL_SIZE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        self.play(LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in recap], lag_ratio=0.3))
        self.wait(2)
        self.play(FadeOut(recap))
