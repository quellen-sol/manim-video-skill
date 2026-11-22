#!/usr/bin/env python3
"""Extract still frames and contact sheets from a rendered video, for visual inspection.

Usage:
  frames.py VIDEO [--out DIR] [--anims [--mid] | --count N | --at T1,T2,... | --holds | --cues [SRT]]
                  [--from S] [--to S] [--cols 4] [--per-sheet 16] [--tile-width 480]

Modes (default: --anims when Manim's partial-movie list is complete, else --count):
  --anims      the last frame of every play()/wait() call (Manim writes one partial movie per
               call): the resting state after each animation. Alias: --beats
  --mid        with --anims, also the midpoint of every animation (catches mid-transition bugs)
  --count N    N frames evenly spaced
  --at ...     frames at the given times in seconds
  --holds      one frame from the middle of every static hold of 0.5 s or more
  --cues [SRT] one frame in the middle of every subtitle cue (manim-voiceover writes
               <Scene>.srt next to the video): checks that each sentence has its visual
--from/--to limit any mode to a time window, to re-check only the part you changed.

Writes a new run folder (default <video dir>/frames_<stem>/<timestamp>/, so earlier runs stay for
before/after comparisons) with frame_NNN_tSSS.ss.png, contact sheets sheet_NN.png (tiles in reading
order) and index.txt. In index.txt, "anim K" is Manim's 0-based animation number: render that frame
at full resolution with  render.sh still scene.py Scene -- -n 0,K
Needs ffmpeg and ffprobe (on PATH or in ~/.local/share/manim-video/bin). Python 3.11+, stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from _ffbin import tool

FFMPEG, FFPROBE = tool("ffmpeg"), tool("ffprobe")


def probe(path: Path) -> dict:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def video_info(path: Path) -> tuple[float, float, int, int]:
    data = probe(path)
    v = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1)
    duration = float(data["format"].get("duration") or v.get("duration") or 0)
    return duration, fps, int(v["width"]), int(v["height"])


def find_partial_list(video: Path) -> Path | None:
    candidate = video.parent / "partial_movie_files" / video.stem / "partial_movie_file_list.txt"
    return candidate if candidate.exists() else None


def anim_times(listing: Path, fps: float, mid: bool, duration: float) -> list[tuple[float, str]] | None:
    """Times from Manim's partial movies, or None (with a warning) if they cannot be trusted."""
    files = []
    for line in listing.read_text().splitlines():
        m = re.match(r"file '(?:file:)?(.*)'", line.strip())
        if m:
            files.append(listing.parent / Path(m.group(1)).name)
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"frames.py: WARNING {len(missing)} of {len(files)} partial movie files are missing (Manim "
              f"deletes old ones beyond max_files_cached; render.sh raises that limit). Animation times "
              f"would be wrong, so falling back to evenly spaced frames.", file=sys.stderr)
        return None
    times, t = [], 0.0
    half_frame = 0.5 / fps
    for k, f in enumerate(files):
        d = float(probe(f)["format"].get("duration") or 0)
        if mid and d > 0.4:
            times.append((t + d / 2, f"anim {k} (mid)"))
        t += d
        times.append((max(0.0, t - half_frame), f"anim {k} (end)"))
    if abs(t - duration) > 0.25 + 0.5 * len(files) / fps:
        print(f"frames.py: WARNING partial movies add up to {t:.2f}s but the video lasts {duration:.2f}s "
              f"(stale list from an older render?). Falling back to evenly spaced frames.", file=sys.stderr)
        return None
    return times


def hold_times(video: Path, duration: float) -> list[tuple[float, str]]:
    res = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", str(video), "-vf", "freezedetect=n=0.0001:d=0.5",
         "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", res.stderr)]
    ends += [duration] * (len(starts) - len(ends))
    return [((s + e) / 2, f"hold {s:.1f}-{e:.1f}s") for s, e in zip(starts, ends)]


def cue_times(srt: Path) -> list[tuple[float, str]]:
    def secs(stamp: str) -> float:
        h, m, rest = stamp.split(":")
        s, ms = rest.replace(".", ",").split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    times = []
    for block in re.split(r"\n\s*\n", srt.read_text(encoding="utf-8", errors="replace").strip()):
        lines = block.strip().splitlines()
        stamp = next((l for l in lines if "-->" in l), None)
        if not stamp:
            continue
        start, end = (secs(x.strip().split()[0]) for x in stamp.split("-->"))
        text = " ".join(l for l in lines[lines.index(stamp) + 1:]).strip()
        times.append(((start + end) / 2, f"cue {start:.1f}-{end:.1f}s: {text[:70]}"))
    return times


def extract(video: Path, t: float, dest: Path) -> None:
    subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
         "-frames:v", "1", str(dest)],
        check=True,
    )


def make_sheets(frames: list[Path], out: Path, cols: int, per_sheet: int, tile_width: int) -> list[Path]:
    sheets = []
    for n, start in enumerate(range(0, len(frames), per_sheet), 1):
        chunk = frames[start:start + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        with tempfile.TemporaryDirectory() as tmp:
            for i, f in enumerate(chunk):
                os.symlink(f.resolve(), Path(tmp) / f"t_{i:04d}.png")
            sheet = out / f"sheet_{n:02d}.png"
            vf = (f"scale={tile_width}:-2,pad=iw+12:ih+12:6:6:color=0x555555,"
                  f"tile={cols}x{rows}:padding=0:color=0x555555")
            subprocess.run(
                [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1",
                 "-i", str(Path(tmp) / "t_%04d.png"), "-vf", vf, "-frames:v", "1", str(sheet)],
                check=True,
            )
        sheets.append(sheet)
    return sheets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, help="output dir (default: <video dir>/frames_<stem>/<timestamp>)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--anims", "--beats", dest="anims", action="store_true")
    mode.add_argument("--count", type=int)
    mode.add_argument("--at", type=str)
    mode.add_argument("--holds", action="store_true")
    mode.add_argument("--cues", nargs="?", const="auto", help="subtitle file (default <video stem>.srt)")
    ap.add_argument("--mid", action="store_true", help="with --anims, add mid-animation frames")
    ap.add_argument("--from", dest="t_from", type=float, default=None, help="start of time window (s)")
    ap.add_argument("--to", dest="t_to", type=float, default=None, help="end of time window (s)")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--per-sheet", type=int, default=16)
    ap.add_argument("--tile-width", type=int, default=480)
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"frames.py: no such file: {video}")
    duration, fps, width, height = video_info(video)
    lo = args.t_from if args.t_from is not None else 0.0
    hi = args.t_to if args.t_to is not None else duration
    span = max(hi - lo, 0.1)

    def even(n: int) -> list[tuple[float, str]]:
        return [(lo + span * (i + 0.5) / n, "even") for i in range(n)]

    default_count = int(min(48, max(12, span / 3)))
    listing = find_partial_list(video)
    if args.at:
        times = [(float(x), "requested") for x in args.at.split(",") if x.strip()]
    elif args.holds:
        times = hold_times(video, duration)
    elif args.count:
        times = even(args.count)
    elif args.cues:
        srt = video.with_suffix(".srt") if args.cues == "auto" else Path(args.cues)
        if not srt.exists():
            sys.exit(f"frames.py: no subtitle file {srt} (narrated scenes write <Scene>.srt next to the video)")
        times = cue_times(srt)
    else:
        times = anim_times(listing, fps, args.mid, duration) if listing is not None else None
        if times is None:
            if args.anims and listing is None:
                print("frames.py: no partial_movie_file_list.txt next to the video; using evenly spaced frames",
                      file=sys.stderr)
            times = even(default_count)

    times = [(t, why) for t, why in times if lo - 1e-6 <= t <= hi + 1e-6]
    times = [(min(max(t, 0.0), max(duration - 0.5 / fps, 0.0)), why) for t, why in times]
    if not times:
        sys.exit("frames.py: no frame times in the requested window")

    out = (args.out or video.parent / f"frames_{video.stem}" / time.strftime("%Y%m%d-%H%M%S")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("frame_*.png")) + list(out.glob("sheet_*.png")):
        old.unlink()

    frames, index, last_hash = [], [], None
    for t, why in times:
        dest = out / f"frame_{len(frames) + 1:03d}_t{t:07.2f}.png"
        extract(video, t, dest)
        if not dest.exists():
            continue
        digest = hashlib.sha1(dest.read_bytes()).hexdigest()
        if digest == last_hash and index:  # identical to the previous still (e.g. a wait)
            dest.unlink()
            index[-1] = (index[-1][0], index[-1][1] + f" = {why}", index[-1][2])
            continue
        last_hash = digest
        frames.append(dest)
        index.append((t, why, dest.name))

    if not frames:
        sys.exit("frames.py: no frames extracted")
    sheets = make_sheets(frames, out, args.cols, args.per_sheet, args.tile_width)
    lines = [f"video: {video}", f"duration: {duration:.2f}s  {width}x{height} @ {fps:g} fps",
             f"window: {lo:.2f}-{hi:.2f}s, {len(frames)} stills, {args.per_sheet} tiles per sheet, "
             f"{args.cols} per row, reading order",
             "anim K = Manim's 0-based animation number; full-resolution still: "
             "render.sh still scene.py Scene -- -n 0,K", ""]
    for n, start in enumerate(range(0, len(frames), args.per_sheet), 1):
        chunk = index[start:start + args.per_sheet]
        lines.append(f"sheet_{n:02d}.png  {chunk[0][0]:.1f}-{chunk[-1][0]:.1f}s")
        for i, (t, why, name) in enumerate(chunk, start + 1):
            lines.append(f"  tile {i:>3}  t={t:7.2f}s  {why}  {name}")
    (out / "index.txt").write_text("\n".join(lines) + "\n")
    print(f"frames.py: {len(frames)} stills from {video.name} ({duration:.1f}s) -> {out}")
    for s in sheets:
        print(f"SHEET: {s}")
    print((out / "index.txt").read_text())


if __name__ == "__main__":
    main()
