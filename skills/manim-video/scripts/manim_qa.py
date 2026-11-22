"""Headless layout checks for Manim Community scenes.

Mix ``LayoutGuard`` into a scene to log common layout bugs after every animation:

    try:
        from manim_qa import LayoutGuard      # on PYTHONPATH when rendered by render.sh
    except ImportError:                       # keeps the file renderable without the skill
        class LayoutGuard:
            pass

    class Explainer(LayoutGuard, Scene):
        def construct(self):
            ...

After each ``play``/``wait`` it prints lines starting with ``LAYOUT`` (render.sh shows them):

* ``CLIPPED``   a text object, or a shape smaller than the frame, sticks out of the frame
* ``OFFSCREEN`` a visible object lies entirely outside the frame (it will never be seen)
* ``OVERLAP``   two text objects overlap each other
* ``END``       what is still on screen when the scene ends (objects that never leave)

Call ``self.qa_ignore(mob, ...)`` for objects whose overlap or clipping is intentional
(for example a background grid). The checks look at bounding boxes, so they can miss
overlaps between curved shapes; they never replace looking at the frames.
ThreeDScene subclasses are skipped (projected positions are not checked).
"""

from __future__ import annotations

from manim import (
    Code,
    DecimalNumber,
    MarkupText,
    MathTex,
    Paragraph,
    SingleStringMathTex,
    Text,
    ThreeDScene,
    ValueTracker,
    config,
)

TEXT_TYPES = (Text, MarkupText, Paragraph, SingleStringMathTex, MathTex, DecimalNumber, Code)
MARGIN = 0.05          # scene units of tolerance at the frame edge
OVERLAP_FRACTION = 0.12  # share of the smaller text box that must be covered to report


def _label(mob) -> str:
    for attr in ("original_text", "tex_string", "text"):
        value = getattr(mob, attr, None)
        if isinstance(value, str) and value.strip():
            value = " ".join(value.split())
            return f"{type(mob).__name__}({value[:40]!r})"
    if isinstance(mob, DecimalNumber):
        return f"{type(mob).__name__}({mob.get_value():g})"
    return type(mob).__name__


def _visible(mob) -> bool:
    try:
        fill = mob.get_fill_opacity()
        stroke = mob.get_stroke_opacity() if mob.get_stroke_width() > 0 else 0
        return max(fill, stroke) > 0.02
    except Exception:  # ImageMobject and other non-VMobjects
        return True


def _family_visible(mob) -> bool:
    return any(_visible(m) for m in mob.get_family() if m.has_points())


def _box(mob):
    if mob.width == 0 and mob.height == 0:
        return None
    return (mob.get_left()[0], mob.get_bottom()[1], mob.get_right()[0], mob.get_top()[1])


class LayoutGuard:
    """Scene mixin. Put it first: ``class MyScene(LayoutGuard, Scene)``."""

    def qa_ignore(self, *mobjects):
        ignored = self.__dict__.setdefault("_qa_ignored", set())
        for mob in mobjects:
            for m in mob.get_family():
                ignored.add(id(m))
        return mobjects[0] if len(mobjects) == 1 else mobjects

    # --- hooks -----------------------------------------------------------------
    def play(self, *args, **kwargs):
        result = super().play(*args, **kwargs)
        try:
            self._qa_check()
        except Exception as exc:  # never break a render because of the checker
            print(f"LAYOUT checker-error {type(exc).__name__}: {exc}", flush=True)
        return result

    def tear_down(self):
        try:
            names = [_label(m) for m in self.mobjects
                     if not isinstance(m, ValueTracker) and _family_visible(m)]
            if names:
                shown = ", ".join(names[:12]) + (" ..." if len(names) > 12 else "")
                print(f"LAYOUT END {len(names)} object(s) still on screen: {shown}", flush=True)
        except Exception:
            pass
        return super().tear_down()

    # --- checks ----------------------------------------------------------------
    def _frame_box(self):
        frame = getattr(getattr(self, "camera", None), "frame", None)
        if frame is not None and hasattr(frame, "get_center"):
            cx, cy, _ = frame.get_center()
            w, h = frame.width, frame.height
        else:
            cx, cy = 0.0, 0.0
            w, h = config.frame_width, config.frame_height
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def _collect(self):
        ignored = self.__dict__.get("_qa_ignored", set())
        texts, shapes = [], []

        def walk(mob):
            if id(mob) in ignored:
                return
            if isinstance(mob, TEXT_TYPES):
                if _family_visible(mob):
                    texts.append(mob)
                return
            if mob.submobjects:
                for sub in mob.submobjects:
                    walk(sub)
            elif mob.has_points() and _visible(mob):
                shapes.append(mob)

        for mob in self.mobjects:
            if not isinstance(mob, ValueTracker):
                walk(mob)
        return texts, shapes

    def _qa_check(self):
        if isinstance(self, ThreeDScene):
            return
        seen = self.__dict__.setdefault("_qa_seen", set())
        t = getattr(getattr(self, "renderer", None), "time", 0.0)
        n = getattr(getattr(self, "renderer", None), "num_plays", 0)
        fx0, fy0, fx1, fy1 = self._frame_box()
        fw, fh = fx1 - fx0, fy1 - fy0
        texts, shapes = self._collect()

        def report(key, message):
            if key in seen:
                return
            seen.add(key)
            print(f"LAYOUT t={t:.1f}s after animation {n}: {message}", flush=True)

        for mob in texts + shapes:
            box = _box(mob)
            if box is None:
                continue
            x0, y0, x1, y1 = box
            is_text = mob in texts
            if not is_text and ((x1 - x0) >= fw * 0.98 or (y1 - y0) >= fh * 0.98):
                continue  # frame-sized backgrounds, planes and grids are usually intentional
            outside = x1 < fx0 or x0 > fx1 or y1 < fy0 or y0 > fy1
            if outside:
                report(("off", id(mob)), f"OFFSCREEN {_label(mob)} is entirely outside the frame "
                                         f"(center {mob.get_center()[0]:.2f}, {mob.get_center()[1]:.2f})")
                continue
            over = max(fx0 - x0, x1 - fx1, fy0 - y0, y1 - fy1)
            if over > MARGIN:
                sides = [s for s, d in (("left", fx0 - x0), ("right", x1 - fx1),
                                        ("bottom", fy0 - y0), ("top", y1 - fy1)) if d > MARGIN]
                report(("clip", id(mob)), f"CLIPPED {_label(mob)} crosses the {'/'.join(sides)} "
                                          f"edge by {over:.2f} units")

        boxes = [(m, _box(m)) for m in texts]
        boxes = [(m, b) for m, b in boxes if b is not None]
        for i in range(len(boxes)):
            a, (ax0, ay0, ax1, ay1) = boxes[i]
            for j in range(i + 1, len(boxes)):
                b, (bx0, by0, bx1, by1) = boxes[j]
                ix = min(ax1, bx1) - max(ax0, bx0)
                iy = min(ay1, by1) - max(ay0, by0)
                if ix <= 0 or iy <= 0:
                    continue
                smaller = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0)) or 1e-9
                if ix * iy / smaller >= OVERLAP_FRACTION:
                    report(("ovl", id(a), id(b)), f"OVERLAP {_label(a)} and {_label(b)} "
                                                  f"({100 * ix * iy / smaller:.0f}% of the smaller box)")
