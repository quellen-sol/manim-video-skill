#!/usr/bin/env python3
"""Regression test for the measured geometry checker (skills/manim-video/scripts/geometry_qa.py).

  python3 tests/test_geometry.py              unit tests (no Manim) + container regression
  python3 tests/test_geometry.py --unit-only  unit tests only (host Python, stdlib)

The container part renders tests/jobs/geometry-old-unit-circle (the original unit-circle layout,
whose circle did not look centred on its axes and sat against the frame edge) and
tests/jobs/geometry-fixed-unit-circle through render-in-container.sh. The checker must report
the old layout's violations (exit 1, geometry FAIL) and pass the fixed one.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "manim-video"
sys.path.insert(0, str(SKILL / "scripts"))
from geometry_qa import centered_in, concentric, evaluate, symmetric, within_margin  # noqa: E402

FRAME = (-64 / 9, -4.0, 64 / 9, 4.0)   # Manim's default 14.22 x 8 frame
FAILS = 0


def check(cond: bool, what: str) -> None:
    global FAILS
    print(("PASS  " if cond else "FAIL  ") + what)
    FAILS += 0 if cond else 1


def unit_tests() -> None:
    # The original layout, measured from its code: O = (-3.8, -0.8), R = 2.5, XR = YU = 1.25.
    old = {"circle": (-6.3, -3.3, -1.3, 1.7),
           "x_axis": (-6.4, -0.8, -3.8 + 2.5 * 1.25, -0.8),
           "y_axis": (-3.8, -3.4, -3.8, -0.8 + 2.5 * 1.25)}
    old["figure"] = (-6.4, -3.4, old["x_axis"][2], old["y_axis"][3])
    res = {r["rule"]: r for r in evaluate(
        [concentric("circle", "x_axis", "y_axis"), symmetric("x_axis", about="circle", axis="x"),
         symmetric("y_axis", about="circle", axis="y"), within_margin("figure", pct=6)], old, FRAME)}
    check(not res["concentric(circle, x_axis, y_axis)"]["ok"], "old layout: concentric() fails "
          f"({res['concentric(circle, x_axis, y_axis)']['detail']})")
    check(not res["symmetric(x_axis, about=circle, axis=x)"]["ok"],
          f"old layout: x axis asymmetric ({res['symmetric(x_axis, about=circle, axis=x)']['detail']})")
    check(not res["symmetric(y_axis, about=circle, axis=y)"]["ok"], "old layout: y axis asymmetric")
    check(not res["within_margin(figure, 6%)"]["ok"],
          f"old layout: figure too close to the edge ({res['within_margin(figure, 6%)']['detail']})")
    # The fixed layout: symmetric axes, figure centred in the left half.
    cx = FRAME[0] / 2
    fixed = {"circle": (cx - 2, -2, cx + 2, 2), "x_axis": (cx - 2.5, 0, cx + 2.5, 0),
             "y_axis": (cx, -2.5, cx, 2.5), "figure": (cx - 2.5, -2.5, cx + 2.5, 2.5)}
    rules = [concentric("circle", "x_axis", "y_axis"), symmetric("x_axis", about="circle", axis="x"),
             symmetric("y_axis", about="circle", axis="y"), within_margin("figure", pct=6),
             centered_in("figure", region=(FRAME[0], FRAME[1], 0, FRAME[3]))]
    out = evaluate(rules, fixed, FRAME)
    check(all(r["ok"] for r in out) and len(out) == 5, "fixed layout: all five rules hold")
    # Rules whose objects are not on screen are skipped, not failed.
    check(evaluate([concentric("circle", "nowhere")], fixed, FRAME) == [], "rules with off-screen names are skipped")
    check(evaluate([concentric("circle", (cx, 0))], fixed, FRAME)[0]["ok"], "concentric() accepts a point")
    check(not evaluate([centered_in("figure")], fixed, FRAME)[0]["ok"], "centered_in(frame) fails for a left-half figure")
    # A group only partly on screen: centring rules wait, margins are still checked.
    half = {"figure": (FRAME[0] + 0.1, -1, -2, 1)}
    out = evaluate([centered_in("figure", region=(FRAME[0], FRAME[1], 0, FRAME[3])), within_margin("figure", pct=6)],
                   half, FRAME, partial={"figure"})
    check([r["rule"] for r in out] == ["within_margin(figure, 6%)"] and not out[0]["ok"],
          "partly built group: centred_in skipped, within_margin still enforced")
    title = {"title": (-2.0, 3.0, 2.0, 3.6)}
    check(evaluate([centered_in("title", axis="x")], title, FRAME)[0]["ok"]
          and not evaluate([centered_in("title")], title, FRAME)[0]["ok"], "centered_in(axis='x') checks x only")


def container_tests() -> None:
    if not shutil.which("docker"):
        print("SKIP  container regression: docker not available")
        return
    wrapper = SKILL / "scripts" / "render-in-container.sh"
    work = ROOT / "out" / "test-geometry"
    shutil.rmtree(work, ignore_errors=True)
    for name, expect_fail in (("geometry-old-unit-circle", True), ("geometry-fixed-unit-circle", False)):
        job = work / name
        shutil.copytree(ROOT / "tests" / "jobs" / name, job)
        res = subprocess.run([str(wrapper), str(job)], capture_output=True, text=True)
        try:
            report = json.loads((job / "out" / "report.json").read_text())
        except (OSError, json.JSONDecodeError):
            check(False, f"{name}: no report (exit {res.returncode}): {(res.stdout + res.stderr)[-400:]}")
            continue
        geo = report.get("geometry", {})
        rules = {v["rule"] for v in geo.get("violations", [])}
        if expect_fail:
            check(res.returncode == 1 and geo.get("status") == "FAIL",
                  f"{name}: render exits 1 and report.json shows geometry FAIL")
            for want in ("concentric(circle, x_axis, y_axis)", "symmetric(x_axis, about=circle, axis=x)",
                         "symmetric(y_axis, about=circle, axis=y)", "within_margin(figure, 6%)"):
                check(want in rules, f"{name}: flags {want}")
            check((job / "out" / "geometry.json").is_file(), f"{name}: out/geometry.json written")
            g = subprocess.run([str(wrapper), str(job), "--geometry"], capture_output=True, text=True)
            txt = (job / "out" / "geometry-check.txt").read_text() if (job / "out" / "geometry-check.txt").is_file() else ""
            check(g.returncode == 1 and "4 violation(s)" in txt,
                  f"{name}: --geometry (dry run, no frames) reproduces the 4 violations")
        else:
            check(res.returncode == 0 and geo.get("status") == "PASS" and not rules,
                  f"{name}: geometry PASS, no violations ({geo.get('message')})")


if __name__ == "__main__":
    unit_tests()
    if "--unit-only" not in sys.argv:
        container_tests()
    print(f"\ntest_geometry: {'OK' if FAILS == 0 else f'{FAILS} failure(s)'}")
    sys.exit(1 if FAILS else 0)
