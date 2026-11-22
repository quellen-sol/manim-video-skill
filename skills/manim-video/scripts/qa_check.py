#!/usr/bin/env python3
"""Headless sanity checks for a rendered explainer video.

Usage:
  qa_check.py VIDEO [--expect-audio | --expect-silent] [--expect-res 1920x1080]
                    [--min-duration S] [--max-duration S] [--light-bg] [--json]

Checks (each line is PASS, WARN or FAIL; exit status 1 if any FAIL):
  stream     a video stream exists; resolution, frame rate and duration are sane
  audio      narration present when expected (and absent when --expect-silent);
             audio is not silent; audio and video lengths agree; no long gaps in speech
  blank      intervals where the frame is (almost) empty background (--light-bg for light themes)
  holds      static stretches: long ones read as stalls, none at all means no time to read
  cuts       abrupt full-frame changes between consecutive frames (pop-ins, flicker)

These checks complement, never replace, looking at the frames (frames.py).
Needs ffmpeg and ffprobe (on PATH or in ~/.local/share/manim-video/bin). Python 3.11+, stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from _ffbin import tool


FFMPEG, FFPROBE = tool("ffmpeg"), tool("ffprobe")
results: list[dict] = []


def add(level: str, check: str, message: str) -> None:
    results.append({"level": level, "check": check, "message": message})


def ffmpeg_filter(video: Path, args: list[str]) -> str:
    res = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(video), *args, "-f", "null", "-"],
                         capture_output=True, text=True)
    return res.stderr


def merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1] + 0.001:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--expect-audio", action="store_true", help="the video should carry narration")
    g.add_argument("--expect-silent", action="store_true", help="the video should have no audio stream")
    ap.add_argument("--expect-res", help="WIDTHxHEIGHT, e.g. 1920x1080")
    ap.add_argument("--min-duration", type=float, default=3.0)
    ap.add_argument("--max-duration", type=float, default=900.0)
    ap.add_argument("--long-hold", type=float, default=None,
                    help="seconds of no motion reported as a stall (default 6 silent, 12 narrated)")
    ap.add_argument("--light-bg", action="store_true", help="the scene uses a light background")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"qa_check.py: no such file: {video}")

    data = json.loads(subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)],
        check=True, capture_output=True, text=True).stdout)
    vstreams = [s for s in data["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in data["streams"] if s["codec_type"] == "audio"]
    duration = float(data["format"].get("duration") or 0)

    # stream ------------------------------------------------------------------------------
    if not vstreams:
        add("FAIL", "stream", "no video stream")
        return finish(args, video, duration)
    v = vstreams[0]
    w, h = int(v["width"]), int(v["height"])
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den or 1)
    add("PASS", "stream", f"{v.get('codec_name')} {w}x{h} @ {fps:g} fps, {duration:.2f}s, "
                          f"{len(astreams)} audio stream(s)")
    if args.expect_res:
        ew, eh = (int(x) for x in args.expect_res.lower().split("x"))
        if (w, h) != (ew, eh):
            add("FAIL", "stream", f"resolution {w}x{h}, expected {ew}x{eh}")
    if duration < args.min_duration:
        add("FAIL", "stream", f"duration {duration:.2f}s is below {args.min_duration}s")
    if duration > args.max_duration:
        add("WARN", "stream", f"duration {duration:.1f}s is above {args.max_duration}s")
    if fps < 10:
        add("WARN", "stream", f"frame rate {fps:g} is very low")

    # audio -------------------------------------------------------------------------------
    narrated = bool(astreams)
    if args.expect_audio and not astreams:
        add("FAIL", "audio", "narration expected but the file has no audio stream")
    if args.expect_silent and astreams:
        add("WARN", "audio", "silent video expected but the file has an audio stream")
    if astreams:
        a = astreams[0]
        adur = float(a.get("duration") or duration)
        if adur > duration + 0.5:
            add("WARN", "audio", f"audio lasts {adur:.2f}s but video only {duration:.2f}s: narration is cut off")
        elif adur < duration - 8:
            add("WARN", "audio", f"audio ends at {adur:.2f}s, {duration - adur:.1f}s before the video ends "
                                 f"(long silent tail?)")
        vol = ffmpeg_filter(video, ["-map", "0:a:0", "-af", "volumedetect"])
        mean = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
        peak = re.search(r"max_volume: (-?[\d.]+) dB", vol)
        if mean and float(mean.group(1)) < -45:
            add("FAIL", "audio", f"audio is (nearly) silent: mean {mean.group(1)} dB")
        elif mean:
            add("PASS", "audio", f"audio level mean {mean.group(1)} dB, peak {peak.group(1) if peak else '?'} dB")
        if peak and float(peak.group(1)) >= -0.1:
            add("WARN", "audio", "audio peaks at 0 dB; it may be clipping")
        sil = ffmpeg_filter(video, ["-map", "0:a:0", "-af", "silencedetect=noise=-40dB:d=4"])
        ss = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", sil)]
        se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)]
        se += [duration] * (len(ss) - len(se))
        gaps = [(s, e) for s, e in zip(ss, se) if s > 0.5 and e < duration - 0.5]
        for s, e in gaps[:8]:
            add("WARN", "audio", f"no speech for {e - s:.1f}s at {s:.1f}-{e:.1f}s (is the narration out of step?)")

    # blank frames ------------------------------------------------------------------------
    pre = "negate," if args.light_bg else ""
    out = ffmpeg_filter(video, ["-map", "0:v:0", "-vf", f"{pre}blackdetect=d=0.5:pic_th=0.998:pix_th=0.12"])
    blanks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out)]
    total_blank = sum(e - s for s, e in blanks)
    mid_blank = 0.0
    for s, e in blanks:
        at_edge = s < 0.25 or e > duration - 0.25  # fade-in at the start or fade-out at the end
        if not at_edge:
            mid_blank += e - s
        if e - s > (2.5 if at_edge else 1.0):
            where = "at the start" if s < 0.25 else ("at the end" if at_edge else "mid-video")
            add("WARN", "blank", f"empty screen for {e - s:.1f}s {where} ({s:.1f}-{e:.1f}s)")
    if duration and mid_blank / duration > 0.15:
        add("FAIL", "blank", f"{100 * mid_blank / duration:.0f}% of the video (mid-video) is an empty screen")
    elif not any(r["check"] == "blank" for r in results):
        add("PASS", "blank", f"no long empty-screen stretches (total {total_blank:.1f}s, incl. start/end)")

    # holds -------------------------------------------------------------------------------
    long_hold = args.long_hold or (12.0 if narrated else 6.0)
    out = ffmpeg_filter(video, ["-map", "0:v:0", "-vf", "freezedetect=n=0.0001:d=0.4"])
    fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", out)]
    fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", out)]
    fe += [duration] * (len(fs) - len(fe))
    holds = merge(list(zip(fs, fe)))
    static = sum(e - s for s, e in holds)
    for s, e in holds:
        if e - s >= long_hold:
            add("WARN", "holds", f"nothing moves for {e - s:.1f}s at {s:.1f}-{e:.1f}s (stall? cut the wait "
                                 f"or add motion)")
    share = static / duration if duration else 0
    if duration > 10 and share < 0.08:
        add("WARN", "holds", f"only {100 * share:.0f}% of the video is still; viewers get no time to read "
                             f"(add self.wait() after key reveals)")
    elif share > 0.7:
        add("WARN", "holds", f"{100 * share:.0f}% of the video is still; pacing may drag")
    else:
        add("PASS", "holds", f"{100 * share:.0f}% still time across {len(holds)} hold(s)")

    # abrupt cuts / flicker ---------------------------------------------------------------
    out = ffmpeg_filter(video, ["-map", "0:v:0", "-vf", "select='gt(scene,0.30)',metadata=print"])
    cuts = [float(t) for t in re.findall(r"pts_time:([\d.]+)", out)]
    cuts = [t for t in cuts if t > 0.1]
    flicker = [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a <= 0.25]
    for a, b in flicker[:6]:
        add("WARN", "cuts", f"two abrupt changes {b - a:.2f}s apart at {a:.2f}s: possible flicker")
    if cuts:
        listed = ", ".join(f"{t:.2f}s" for t in cuts[:12]) + (" ..." if len(cuts) > 12 else "")
        add("WARN", "cuts", f"{len(cuts)} abrupt full-frame change(s) at {listed}: check each is an intended "
                            f"scene change, not a pop-in (self.add) or a flash")
    else:
        add("PASS", "cuts", "no abrupt full-frame changes")

    finish(args, video, duration)


def finish(args, video: Path, duration: float) -> None:
    worst = "FAIL" if any(r["level"] == "FAIL" for r in results) else (
        "WARN" if any(r["level"] == "WARN" for r in results) else "PASS")
    if args.json:
        print(json.dumps({"video": str(video), "duration": duration, "result": worst, "checks": results}, indent=2))
    else:
        print(f"qa_check: {video}")
        for r in results:
            print(f"  {r['level']:<4} {r['check']:<6} {r['message']}")
        print(f"qa_check: overall {worst}")
    sys.exit(1 if worst == "FAIL" else 0)


if __name__ == "__main__":
    main()
