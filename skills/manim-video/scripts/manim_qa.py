"""Headless layout checks for Manim Community scenes.

Mix ``LayoutGuard`` into a scene to log common layout bugs after every animation:

    try:
        from manim_qa import LayoutGuard      # on PYTHONPATH when rendered by render.sh
    except ImportError:                       # keeps the file renderable without the skill
        print("LAYOUT-GUARD unavailable: manim_qa not importable", flush=True)
        class LayoutGuard:
            pass

    class Explainer(LayoutGuard, Scene):
        def construct(self):
            ...

At scene start it prints ``LAYOUT-GUARD active`` (render.sh reports whether it ran). After each
``play``/``wait`` it prints lines starting with ``LAYOUT``:

* ``CLIPPED``   text, or a shape smaller than the frame, sticks out of the frame
* ``UNSAFE``    text sits outside the safe area (x within ±6.5, y within ±3.5) but inside the frame
* ``OFFSCREEN`` a visible object lies entirely outside the frame (it will never be seen)
* ``OVERLAP``   two text objects overlap, or text overlaps a brace
* ``CROSSED``   a straight line or arrow runs through a text object
* ``END``       what is still on screen when the scene ends (objects that never leave)

Call ``self.qa_ignore(mob, ...)`` for objects whose overlap or position is intentional. The checks
use bounding boxes and straight segments only, and run after each animation (not during it), so they
can miss curved or transient collisions: they never replace looking at the frames.
ThreeDScene subclasses are skipped (projected positions are not checked).
"""

from __future__ import annotations

import numpy as np
from manim import (
    Brace,
    Code,
    DecimalNumber,
    ImageMobject,
    Line,
    MarkupText,
    MathTex,
    NumberPlane,
    Paragraph,
    SingleStringMathTex,
    Text,
    ThreeDScene,
    ValueTracker,
    VMobject,
    config,
)

TEXT_TYPES = (Text, MarkupText, Paragraph, SingleStringMathTex, MathTex, DecimalNumber, Code)
MARGIN = 0.05            # scene units of tolerance at an edge
SAFE_X, SAFE_Y = 6.5, 3.5  # safe area from references/style-guide.md
OVERLAP_FRACTION = 0.12  # share of the smaller box that must be covered to report


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
    if isinstance(mob, ValueTracker) or not mob.has_points():
        return isinstance(mob, ImageMobject)
    if isinstance(mob, VMobject):
        fill = mob.get_fill_opacity()
        stroke = mob.get_stroke_opacity() if mob.get_stroke_width() > 0 else 0
        return max(fill, stroke) > 0.02
    return True


def _family_visible(mob) -> bool:
    return any(_visible(m) for m in mob.get_family())


def _box(mob):
    if mob.width == 0 and mob.height == 0:
        return None
    return (mob.get_left()[0], mob.get_bottom()[1], mob.get_right()[0], mob.get_top()[1])


def _segment_hits_box(p, q, box) -> bool:
    """Liang-Barsky clip test: does segment p->q pass through the box?"""
    x0, y0, x1, y1 = box
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pk) < 1e-12:
            if qk < 0:
                return False
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


class LayoutGuard:
    """Scene mixin. Put it first: ``class MyScene(LayoutGuard, Scene)``."""

    def qa_ignore(self, *mobjects):
        ignored = self.__dict__.setdefault("_qa_ignored", {})
        for mob in mobjects:
            for m in mob.get_family():
                ignored[id(m)] = m  # keep a reference so the id cannot be reused
        return mobjects[0] if len(mobjects) == 1 else mobjects

    # --- hooks -----------------------------------------------------------------
    def setup(self):
        print(f"LAYOUT-GUARD active for {type(self).__name__}", flush=True)
        return super().setup()

    def play(self, *args, **kwargs):
        result = super().play(*args, **kwargs)
        try:
            self._qa_check()
        except Exception as exc:  # never break a render because of the checker
            print(f"LAYOUT checker-error {type(exc).__name__}: {exc}", flush=True)
        return result

    def tear_down(self):
        try:
            names = [_label(m) for m in self.mobjects if _family_visible(m)]
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
        ignored = self.__dict__.get("_qa_ignored", {})
        texts, shapes, lines, braces = [], [], [], []

        def walk(mob):
            if id(mob) in ignored or isinstance(mob, ValueTracker):
                return
            if isinstance(mob, TEXT_TYPES):
                if _family_visible(mob):
                    texts.append(mob)
                return
            if isinstance(mob, NumberPlane):
                return  # background grid: lines everywhere by design
            if isinstance(mob, Brace):
                if _family_visible(mob):
                    braces.append(mob)
                return
            if isinstance(mob, Line) and _family_visible(mob):
                lines.append(mob)  # Arrow, DashedLine, Vector, NumberLine... are Lines
            if mob.submobjects:
                for sub in mob.submobjects:
                    walk(sub)
            elif mob.has_points() and _visible(mob):
                shapes.append(mob)

        for mob in self.mobjects:
            walk(mob)
        return texts, shapes, lines, braces

    def _qa_check(self):
        if isinstance(self, ThreeDScene):
            return
        seen = self.__dict__.setdefault("_qa_seen", set())
        t = getattr(getattr(self, "renderer", None), "time", 0.0)
        n = getattr(getattr(self, "renderer", None), "num_plays", 0)
        fx0, fy0, fx1, fy1 = self._frame_box()
        fw, fh = fx1 - fx0, fy1 - fy0
        scale = fh / config.frame_height
        cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        sx0, sx1 = cx - SAFE_X * scale, cx + SAFE_X * scale
        sy0, sy1 = cy - SAFE_Y * scale, cy + SAFE_Y * scale
        texts, shapes, lines, braces = self._collect()

        def report(message):
            if message in seen:
                return
            seen.add(message)
            print(f"LAYOUT t={t:.1f}s after animation {n}: {message}", flush=True)

        def sides(b, l, bo, r, t_):
            return "/".join(s for s, d in (("left", l - b[0]), ("bottom", bo - b[1]), ("right", b[2] - r),
                                            ("top", b[3] - t_)) if d > MARGIN)

        text_ids = {id(m) for m in texts}
        for mob in texts + shapes:
            box = _box(mob)
            if box is None:
                continue
            x0, y0, x1, y1 = box
            is_text = id(mob) in text_ids
            if not is_text and ((x1 - x0) >= fw * 0.98 or (y1 - y0) >= fh * 0.98):
                continue  # frame-sized backgrounds, planes and grids are usually intentional
            if x1 < fx0 or x0 > fx1 or y1 < fy0 or y0 > fy1:
                c = mob.get_center()
                report(f"OFFSCREEN {_label(mob)} is entirely outside the frame (center {c[0]:.2f}, {c[1]:.2f})")
                continue
            over = max(fx0 - x0, x1 - fx1, fy0 - y0, y1 - fy1)
            if over > MARGIN:
                report(f"CLIPPED {_label(mob)} crosses the {sides(box, fx0, fy0, fx1, fy1)} frame edge "
                       f"by {over:.2f} units")
            elif is_text and max(sx0 - x0, x1 - sx1, sy0 - y0, y1 - sy1) > MARGIN:
                report(f"UNSAFE {_label(mob)} is outside the safe area on the "
                       f"{sides(box, sx0, sy0, sx1, sy1)} (keep x within ±{SAFE_X}, y within ±{SAFE_Y})")

        boxes = [(m, _box(m)) for m in texts]
        boxes = [(m, b) for m, b in boxes if b is not None]
        brace_boxes = [(br, _box(br)) for br in braces]
        brace_boxes = [(br, b) for br, b in brace_boxes if b is not None]
        for i in range(len(boxes)):
            a, (ax0, ay0, ax1, ay1) = boxes[i]
            for b, (bx0, by0, bx1, by1) in boxes[i + 1:] + brace_boxes:
                ix = min(ax1, bx1) - max(ax0, bx0)
                iy = min(ay1, by1) - max(ay0, by0)
                if ix <= 0 or iy <= 0:
                    continue
                smaller = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0)) or 1e-9
                if ix * iy / smaller >= OVERLAP_FRACTION:
                    report(f"OVERLAP {_label(a)} and {_label(b)} ({100 * ix * iy / smaller:.0f}% of the smaller box)")

        for mob, (x0, y0, x1, y1) in boxes:
            pad_x, pad_y = 0.15 * (x1 - x0), 0.2 * (y1 - y0)   # only lines through the text's core
            core = (x0 + pad_x, y0 + pad_y, x1 - pad_x, y1 - pad_y)
            for line in lines:
                try:
                    p, q = np.asarray(line.get_start()), np.asarray(line.get_end())
                except Exception:
                    continue
                if _segment_hits_box(p, q, core):
                    report(f"CROSSED {type(line).__name__} from ({p[0]:.1f}, {p[1]:.1f}) to ({q[0]:.1f}, {q[1]:.1f}) "
                           f"runs through {_label(mob)}")
