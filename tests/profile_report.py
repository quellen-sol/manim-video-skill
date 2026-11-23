#!/usr/bin/env python3
"""Print the time split of a profiled render (tests/profile_render.sh): out/profile.json from the
stage timers inside the manim process, plus out/summary.json from the job runner."""
import json
import sys
from pathlib import Path


def main(out: Path, container_wall: float | None) -> int:
    prof = json.loads((out / "profile.json").read_text())
    summ = json.loads((out / "summary.json").read_text())
    t = summ.get("timings", {})
    total = container_wall or t.get("total", 0)
    main_rows = [s for s in prof["stages"] if s["thread"] == "main"]
    enc_rows = [s for s in prof["stages"] if s["thread"] == "encoder"]
    merged: dict = {}
    for s in main_rows:
        merged.setdefault(s["stage"], [0.0, 0])
        merged[s["stage"]][0] += s["s"]
        merged[s["stage"]][1] += s["calls"]
    accounted = sum(v[0] for v in merged.values())
    startup = prof["wall_s"] - accounted
    print(f"## Time split: {summ.get('scene')} {summ.get('quality')} {summ.get('resolution')} @ {summ.get('fps')} fps\n")
    print(f"Job wall time {total:.1f} s (container start to exit). Manim process {prof['wall_s']:.1f} s wall, "
          f"{prof['cpu_self_s']:.1f} s CPU in-process ({prof['cpu_self_s'] / prof['wall_s']:.2f} cores on average), "
          f"{prof['cpu_children_s']:.1f} s CPU in subprocesses (latex, dvisvgm); peak RSS {prof['max_rss_mb']:.0f} MB.\n")
    print("| Stage (main thread, exclusive wall time) | s | % of job | calls |")
    print("|---|---|---|---|")
    rows = sorted(merged.items(), key=lambda kv: -kv[1][0])
    for stage, (s, c) in rows:
        print(f"| {stage} | {s:.1f} | {100 * s / total:.1f} | {c} |")
    print(f"| manim: startup, imports, CLI, config (unwrapped) | {startup:.1f} | {100 * startup / total:.1f} | - |")
    other = total - prof["wall_s"] - t.get("checks", 0) - t.get("stills", 0)
    for label, s in (("job: automated checks (qa_check.py: decode + filters)", t.get("checks", 0)),
                     ("job: stills and contact sheets (frames.py)", t.get("stills", 0)),
                     ("job: container start, job.json, copy, report (rest)", other)):
        print(f"| {label} | {s:.1f} | {100 * s / total:.1f} | - |")
    if enc_rows:
        print("\nEncoder threads (overlap the main thread; only the 'encode wait' rows above are exposed):\n")
        print("| Stage (encoder threads) | s | calls |")
        print("|---|---|---|")
        for s in enc_rows:
            print(f"| {s['stage']} | {s['s']:.1f} | {s['calls']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), float(sys.argv[2]) if len(sys.argv) > 2 else None))
