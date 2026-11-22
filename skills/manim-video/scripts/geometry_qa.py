"""Measured geometry checks for Manim Community scenes.

Eyeballing stills misses "almost right" geometry: a circle a few pixels off its axes' crossing,
axes that reach 1.1 radii on one side and 2 on the other, a figure 5% from the frame edge. Declare
what must hold; GeometryGuard measures bounding boxes after every animation and reports violations.

    from geometry_qa import GeometryGuard, concentric, symmetric, within_margin, centered_in

    class Explainer(GeometryGuard, LayoutGuard, Scene):
        def construct(self):
            ...
            self.geo_track(circle=circle, x_axis=x_axis, y_axis=y_axis, figure=figure)
            self.geo_rule(concentric("circle", "x_axis", "y_axis"))  # same centre
            self.geo_rule(symmetric("x_axis", about="circle"))        # equal reach both sides
            self.geo_rule(within_margin("figure", pct=7))             # >= 7% of the frame each side
            self.geo_rule(centered_in("figure", region=(-7.1, -4, 0, 4)))  # centred in the left half

A tracked group does not have to be added to the scene itself: its box is the union of its
members that are on screen (found at any depth). While a group is only partly on screen (built up
piece by piece), only within_margin is checked for it; concentric, symmetric and centered_in wait
until all of it is on screen. self.geo_untrack("name", ...) retires names (and the rules that use
them) when a chapter ends; geo_track can rebind a name to a new object.

Rules (names are geo_track names; tolerances are in scene units, the frame is about 14.2 x 8):
  concentric(*names, tol=0.1)      bounding-box centres coincide. Two axis lines are concentric
                                   with a circle only if they cross at its centre AND reach equally
                                   far both ways. A name may also be an (x, y) point.
  symmetric(name, about=..., axis="both", tol=0.1)
                                   the box reaches equally far on both sides of `about` (a name's
                                   centre or an (x, y) point; default ORIGIN), along "x", "y" or both
  within_margin(name, pct=6)       the box keeps at least pct % of the frame width/height from
                                   every frame edge
  centered_in(name, region="frame", axis="both", tol=0.15)
                                   the box centre is the centre of region: "frame", an
                                   (x0, y0, x1, y1) rectangle, or another tracked name; axis="x"
                                   checks horizontal centring only (e.g. a title at the top)
A rule is checked after every play()/wait() in which all its names are on screen. A default rule
also applies: everything on screen keeps 2% of the frame from every edge (full-frame backgrounds
excepted; self.geo_ignore(mob) opts an object out). Tips of arrows count as part of a box; widen
`tol` (or track the shaft) when an arrowhead makes an axis deliberately asymmetric.

Output: lines starting with GEOMETRY in the render log (out/report.md in the container), and a JSON
dump (env GEOMETRY_JSON, default media/geometry-<Scene>.json) with every tracked object's box and
centre after every animation, and every rule result. `python3 geometry_qa.py DUMP.json` prints the
violations and exits 1 if there are any. This module needs Manim only for GeometryGuard.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

Box = tuple  # (x0, y0, x1, y1) in scene units


def _centre(b: Box) -> tuple[float, float]:
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def _point(spec, boxes: dict) -> tuple[float, float]:
    if isinstance(spec, str):
        return _centre(boxes[spec])
    return (float(spec[0]), float(spec[1]))


def _fmt(spec) -> str:
    return spec if isinstance(spec, str) else f"({spec[0]:g}, {spec[1]:g})"


def _dirn(dx: float, dy: float) -> str:
    parts = []
    if abs(dx) >= 0.005:
        parts.append(f"{abs(dx):.2f} {'right' if dx > 0 else 'left'}")
    if abs(dy) >= 0.005:
        parts.append(f"{abs(dy):.2f} {'up' if dy > 0 else 'down'}")
    return ", ".join(parts) or "0"


class Rule:
    """A declared geometric relation. check(boxes, frame) -> (ok, detail)."""

    kind = "rule"
    needs_complete = True  # skip while a named group is only partly on screen

    def __init__(self, names, text):
        self.names = [n for n in names if isinstance(n, str)]
        self.text = text

    def __repr__(self):
        return self.text


class concentric(Rule):
    kind = "concentric"

    def __init__(self, *specs, tol: float = 0.1):
        if len(specs) < 2:
            raise ValueError("concentric() needs at least two names or points")
        super().__init__(specs, f"concentric({', '.join(_fmt(s) for s in specs)})")
        self.specs, self.tol = specs, tol

    def check(self, boxes, frame):
        ref = _point(self.specs[0], boxes)
        bad = []
        for s in self.specs[1:]:
            c = _point(s, boxes)
            dx, dy = c[0] - ref[0], c[1] - ref[1]
            if max(abs(dx), abs(dy)) > self.tol:
                bad.append(f"{_fmt(s)} centre is {_dirn(dx, dy)} of {_fmt(self.specs[0])} centre")
        return (not bad, "; ".join(bad) or "centres coincide")


class symmetric(Rule):
    kind = "symmetric"

    def __init__(self, name: str, about=(0.0, 0.0), axis: str = "both", tol: float = 0.1):
        if axis not in ("x", "y", "both"):
            raise ValueError('axis must be "x", "y" or "both"')
        super().__init__([name, about], f"symmetric({name}, about={_fmt(about)}, axis={axis})")
        self.name, self.about, self.axis, self.tol = name, about, axis, tol

    def check(self, boxes, frame):
        x0, y0, x1, y1 = boxes[self.name]
        cx, cy = _point(self.about, boxes)
        bad = []
        if self.axis in ("x", "both"):
            left, right = cx - x0, x1 - cx
            if abs(left - right) > self.tol:
                bad.append(f"reaches {left:.2f} left and {right:.2f} right of {_fmt(self.about)}")
        if self.axis in ("y", "both"):
            down, up = cy - y0, y1 - cy
            if abs(down - up) > self.tol:
                bad.append(f"reaches {down:.2f} down and {up:.2f} up from {_fmt(self.about)}")
        return (not bad, f"{self.name} " + "; ".join(bad) if bad else "symmetric")


class within_margin(Rule):
    kind = "within_margin"
    needs_complete = False  # what is on screen must keep its margins, complete or not

    def __init__(self, name: str, pct: float = 6.0):
        super().__init__([name], f"within_margin({name}, {pct:g}%)")
        self.name, self.pct = name, pct

    def check(self, boxes, frame):
        return _margin_check(self.name, boxes[self.name], frame, self.pct)


class centered_in(Rule):
    kind = "centered_in"

    def __init__(self, name: str, region="frame", axis: str = "both", tol: float = 0.15):
        if axis not in ("x", "y", "both"):
            raise ValueError('axis must be "x", "y" or "both"')
        label = region if isinstance(region, str) else "(" + ", ".join(f"{v:g}" for v in region) + ")"
        names = [name] + ([region] if isinstance(region, str) and region != "frame" else [])
        extra = "" if axis == "both" else f", axis={axis}"
        super().__init__(names, f"centered_in({name}, {label}{extra})")
        self.name, self.region, self.axis, self.tol = name, region, axis, tol

    def check(self, boxes, frame):
        if self.region == "frame":
            target = frame
        elif isinstance(self.region, str):
            target = boxes[self.region]
        else:
            target = tuple(self.region)
        c, t = _centre(boxes[self.name]), _centre(target)
        dx = c[0] - t[0] if self.axis in ("x", "both") else 0.0
        dy = c[1] - t[1] if self.axis in ("y", "both") else 0.0
        if max(abs(dx), abs(dy)) > self.tol:
            return False, f"{self.name} centre is {_dirn(dx, dy)} of the region centre"
        return True, "centred"


def _margin_check(name, b, frame, pct):
    fx0, fy0, fx1, fy1 = frame
    mx, my = (fx1 - fx0) * pct / 100, (fy1 - fy0) * pct / 100
    gaps = {"left": (b[0] - fx0) / (fx1 - fx0), "right": (fx1 - b[2]) / (fx1 - fx0),
            "bottom": (b[1] - fy0) / (fy1 - fy0), "top": (fy1 - b[3]) / (fy1 - fy0)}
    need = {"left": mx, "right": mx, "bottom": my, "top": my}
    bad = [f"{side} margin {100 * g:.1f}%" for side, g in gaps.items()
           if g * ((fx1 - fx0) if side in ("left", "right") else (fy1 - fy0)) < need[side] - 1e-6]
    if bad:
        return False, f"{name}: " + ", ".join(bad) + f" (need {pct:g}%)"
    return True, "inside the margins"


def evaluate(rules, boxes: dict, frame: Box, partial=frozenset()) -> list[dict]:
    """Check every rule whose names all have boxes. Pure function (no Manim).
    `partial`: names of groups only partly on screen; rules that need the whole group skip them."""
    out = []
    for r in rules:
        if any(n not in boxes for n in r.names):
            continue
        if r.needs_complete and any(n in partial for n in r.names):
            continue
        ok, detail = r.check(boxes, frame)
        out.append({"rule": r.text, "ok": bool(ok), "detail": detail})
    return out


EDGE_PCT = 2.0  # default rule: nothing on screen within this % of the frame edge


class GeometryGuard:
    """Scene mixin. Put it first: ``class MyScene(GeometryGuard, LayoutGuard, Scene)``."""

    def geo_track(self, **named):
        """Name mobjects for the rules (call again to add or replace names)."""
        self.__dict__.setdefault("_geo_named", {}).update(named)
        return self

    def geo_untrack(self, *names):
        """Retire names; rules that use them are no longer checked."""
        named = self.__dict__.setdefault("_geo_named", {})
        for n in names:
            named.pop(n, None)
        return self

    def geo_rule(self, *rules):
        """Declare relations that must hold whenever their objects are on screen."""
        self.__dict__.setdefault("_geo_rules", []).extend(rules)
        return self

    def geo_ignore(self, *mobjects):
        """Exclude objects from the default frame-edge rule (e.g. an intentional bleed)."""
        ignored = self.__dict__.setdefault("_geo_ignored", {})
        for mob in mobjects:
            for m in mob.get_family():
                ignored[id(m)] = m
        return mobjects[0] if len(mobjects) == 1 else mobjects

    # --- hooks -----------------------------------------------------------------------------
    def setup(self):
        print(f"GEOMETRY-GUARD active for {type(self).__name__}", flush=True)
        self.__dict__.setdefault("_geo_snapshots", [])
        return super().setup()

    def play(self, *args, **kwargs):
        result = super().play(*args, **kwargs)
        try:
            self._geo_check()
        except Exception as exc:  # never break a render because of the checker
            print(f"GEOMETRY checker-error {type(exc).__name__}: {exc}", flush=True)
        return result

    def tear_down(self):
        try:
            self._geo_finish()
        except Exception as exc:
            print(f"GEOMETRY checker-error {type(exc).__name__}: {exc}", flush=True)
        return super().tear_down()

    # --- internals -------------------------------------------------------------------------
    def _geo_frame(self):
        from manim import config
        frame = getattr(getattr(self, "camera", None), "frame", None)
        if frame is not None and hasattr(frame, "get_center"):
            cx, cy, _ = frame.get_center()
            w, h = frame.width, frame.height
        else:
            cx, cy, w, h = 0.0, 0.0, config.frame_width, config.frame_height
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    @staticmethod
    def _geo_visible(mob) -> bool:
        from manim import ImageMobject, ValueTracker, VMobject
        for m in mob.get_family():
            if isinstance(m, ValueTracker) or not m.has_points():
                if isinstance(m, ImageMobject):
                    return True
                continue
            if isinstance(m, VMobject):
                stroke = m.get_stroke_opacity() if m.get_stroke_width() > 0 else 0
                if max(m.get_fill_opacity(), stroke) > 0.02:
                    return True
            else:
                return True
        return False

    @staticmethod
    def _geo_box(mob):
        if not mob.has_points() and not mob.submobjects:
            return None
        if mob.width == 0 and mob.height == 0:
            return None
        return (float(mob.get_left()[0]), float(mob.get_bottom()[1]),
                float(mob.get_right()[0]), float(mob.get_top()[1]))

    def _geo_check(self):
        from manim import ThreeDScene
        if isinstance(self, ThreeDScene):
            return
        frame = self._geo_frame()
        on_screen = {id(m) for top in self.mobjects for m in top.get_family()}
        def parts_of(mob):
            """(visible on-screen parts, complete?) for a tracked object, at any depth."""
            if id(mob) in on_screen:
                return ([mob] if self._geo_visible(mob) else []), True
            if not mob.submobjects:
                return [], not mob.has_points()   # a drawable leaf that is not on screen
            parts, complete = [], True
            for sub in mob.submobjects:
                p, c = parts_of(sub)
                parts += p
                complete = complete and c
            return parts, complete

        boxes, partial = {}, set()
        for name, mob in self.__dict__.get("_geo_named", {}).items():
            parts, complete = parts_of(mob)
            part_boxes = [b for b in (self._geo_box(m) for m in parts) if b is not None]
            if part_boxes:
                boxes[name] = (min(b[0] for b in part_boxes), min(b[1] for b in part_boxes),
                               max(b[2] for b in part_boxes), max(b[3] for b in part_boxes))
                if not complete:
                    partial.add(name)
        results = evaluate(self.__dict__.get("_geo_rules", []), boxes, frame, partial)
        # Default rule: nothing visible on screen near or past the frame edge.
        ignored = self.__dict__.get("_geo_ignored", {})
        fw, fh = frame[2] - frame[0], frame[3] - frame[1]
        for top in self.mobjects:
            if id(top) in ignored or not self._geo_visible(top):
                continue
            b = self._geo_box(top)
            if b is None or ((b[2] - b[0]) >= 0.95 * fw and (b[3] - b[1]) >= 0.95 * fh):
                continue  # full-frame background
            ok, detail = _margin_check(_mob_label(top), b, frame, EDGE_PCT)
            if not ok:
                results.append({"rule": f"frame_edge({EDGE_PCT:g}%)", "ok": False, "detail": detail})
        renderer = getattr(self, "renderer", None)
        n = max(getattr(renderer, "num_plays", 1) - 1, 0)
        t = float(getattr(renderer, "time", 0.0))
        snap = {"anim": n, "t": round(t, 2),
                "objects": {k: {"box": [round(v, 3) for v in b], "centre": [round(c, 3) for c in _centre(b)],
                                **({"partial": True} if k in partial else {})}
                            for k, b in boxes.items()},
                "results": results}
        self.__dict__.setdefault("_geo_snapshots", []).append(snap)
        seen = self.__dict__.setdefault("_geo_seen", set())
        for r in results:
            if not r["ok"] and r["rule"] + r["detail"].split(":")[0] not in seen:
                seen.add(r["rule"] + r["detail"].split(":")[0])
                print(f"GEOMETRY FAIL {r['rule']} at anim {n} (t={t:.1f}s): {r['detail']}", flush=True)

    def _geo_finish(self):
        snaps = self.__dict__.get("_geo_snapshots", [])
        rules = [r.text for r in self.__dict__.get("_geo_rules", [])]
        dump = {"scene": type(self).__name__, "frame": list(self._geo_frame()),
                "rules": rules, "tracked": sorted(self.__dict__.get("_geo_named", {})),
                "snapshots": snaps}
        summary = summarize_dump(dump)
        dump["summary"] = summary
        path = Path(os.environ.get("GEOMETRY_JSON") or f"media/geometry-{type(self).__name__}.json")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(dump, indent=1) + "\n")
        except OSError as exc:
            print(f"GEOMETRY checker-error cannot write {path}: {exc}", flush=True)
        never = [r for r in rules if r not in summary["checked_rules"]]
        print(f"GEOMETRY SUMMARY {len(rules)} rule(s) declared, {len(summary['violations'])} violated, "
              f"checked over {len(snaps)} animation(s); dump: {path}", flush=True)
        for r in never:
            print(f"GEOMETRY UNCHECKED {r}: its objects were never on screen together", flush=True)


def _mob_label(mob) -> str:
    for attr in ("original_text", "tex_string", "text"):
        v = getattr(mob, attr, None)
        if isinstance(v, str) and v.strip():
            return f"{type(mob).__name__}({' '.join(v.split())[:30]!r})"
    return type(mob).__name__


def summarize_dump(dump: dict) -> dict:
    """Group violations by rule: first and last animation, count, first detail."""
    viol: dict = {}
    checked = set()
    for s in dump.get("snapshots", []):
        for r in s.get("results", []):
            checked.add(r["rule"])
            if r["ok"]:
                continue
            key = r["rule"] if not r["rule"].startswith("frame_edge") else r["rule"] + " " + r["detail"].split(":")[0]
            v = viol.setdefault(key, {"rule": r["rule"], "first_anim": s["anim"], "first_t": s["t"],
                                      "count": 0, "detail": r["detail"]})
            v["count"] += 1
            v["last_anim"], v["last_t"] = s["anim"], s["t"]
    return {"violations": list(viol.values()), "checked_rules": sorted(checked),
            "animations": len(dump.get("snapshots", []))}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    dump = json.loads(Path(argv[0]).read_text())
    s = dump.get("summary") or summarize_dump(dump)
    if "--json" in argv:
        print(json.dumps(s, indent=2))
    else:
        print(f"geometry: {dump.get('scene')}: {len(dump.get('rules', []))} rule(s) declared, "
              f"{s['animations']} animation(s) checked, {len(s['violations'])} violation(s)")
        for v in s["violations"]:
            print(f"  FAIL {v['rule']} anims {v['first_anim']}-{v['last_anim']} "
                  f"(t={v['first_t']}-{v['last_t']}s, {v['count']}x): {v['detail']}")
        for r in dump.get("rules", []):
            if r not in s["checked_rules"]:
                print(f"  UNCHECKED {r} (its objects were never on screen together)")
    return 1 if s["violations"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
