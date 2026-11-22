#!/usr/bin/env python3
"""Extract still frames and contact sheets from a rendered video, for visual inspection.

Usage:
  frames.py VIDEO [--out DIR] [--beats | --count N | --at T1,T2,... | --holds]
                  [--mid] [--cols 4] [--per-sheet 16] [--tile-width 480]

Modes (default: --beats when Manim's partial-movie list is found, else --count 12):
  --beats      the last frame of every animation/wait (Manim writes one partial movie per
               play() or wait() call); this is the resting state the viewer sees after each beat
  --mid        with --beats, also take the midpoint of every animation (catches mid-transition bugs)
  --count N    N frames evenly spaced across the video
  --at ...     frames at the given times in seconds
  --holds      one frame from the middle of every static hold of 0.5 s or more

Writes DIR/frame_NNN_tSSS.ss.png, contact sheets DIR/sheet_NN.png (tiles in reading order) and
DIR/index.txt (tile number -> time -> beat). Prints the sheet paths, then the index.
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


def beat_times(video: Path, listing: Path, fps: float, mid: bool) -> list[tuple[float, str]]:
    files = []
    for line in listing.read_text().splitlines():
        m = re.match(r"file '(?:file:)?(.*)'", line.strip())
        if m:
            files.append(listing.parent / Path(m.group(1)).name)
    times, t = [], 0.0
    half_frame = 0.5 / fps
    for i, f in enumerate(files, 1):
        if not f.exists():
            continue
        d = float(probe(f)["format"].get("duration") or 0)
        if mid and d > 0.4:
            times.append((t + d / 2, f"beat {i} (mid)"))
        t += d
        times.append((max(0.0, t - half_frame), f"beat {i} (end)"))
    return times


def hold_times(video: Path) -> list[tuple[float, str]]:
    res = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", str(video), "-vf", "freezedetect=n=0.0005:d=0.5",
         "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", res.stderr)]
    duration = video_info(video)[0]
    ends += [duration] * (len(starts) - len(ends))
    return [((s + e) / 2, f"hold {s:.1f}-{e:.1f}s") for s, e in zip(starts, ends)]


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
    ap.add_argument("--out", type=Path, help="output dir (default: <video dir>/frames_<stem>)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--beats", action="store_true")
    mode.add_argument("--count", type=int)
    mode.add_argument("--at", type=str)
    mode.add_argument("--holds", action="store_true")
    ap.add_argument("--mid", action="store_true", help="with --beats, add mid-animation frames")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--per-sheet", type=int, default=16)
    ap.add_argument("--tile-width", type=int, default=480)
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"frames.py: no such file: {video}")
    duration, fps, width, height = video_info(video)
    out = (args.out or video.parent / f"frames_{video.stem}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("frame_*.png")) + list(out.glob("sheet_*.png")):
        old.unlink()

    listing = find_partial_list(video)
    if args.at:
        times = [(float(x), "requested") for x in args.at.split(",") if x.strip()]
    elif args.holds:
        times = hold_times(video)
    elif args.count:
        times = [(duration * (i + 0.5) / args.count, "even") for i in range(args.count)]
    elif listing is not None:
        times = beat_times(video, listing, fps, args.mid)
    else:
        if args.beats:
            print("frames.py: no partial_movie_file_list.txt next to the video; using --count 12", file=sys.stderr)
        times = [(duration * (i + 0.5) / 12, "even") for i in range(12)]

    times = [(min(max(t, 0.0), max(duration - 0.5 / fps, 0.0)), why) for t, why in times]
    frames, index, last_hash = [], [], None
    for t, why in times:
        dest = out / f"frame_{len(frames) + 1:03d}_t{t:07.2f}.png"
        extract(video, t, dest)
        if not dest.exists():
            continue
        digest = hashlib.sha1(dest.read_bytes()).hexdigest()
        if digest == last_hash:  # identical to the previous still (e.g. a wait after an animation)
            dest.unlink()
            index[-1] = index[-1] + f" = {why}"
            continue
        last_hash = digest
        frames.append(dest)
        index.append(f"tile {len(frames):>3}  t={t:7.2f}s  {why}  {dest.name}")

    if not frames:
        sys.exit("frames.py: no frames extracted")
    sheets = make_sheets(frames, out, args.cols, args.per_sheet, args.tile_width)
    (out / "index.txt").write_text(
        f"video: {video}\nduration: {duration:.2f}s  {width}x{height} @ {fps:g} fps\n"
        f"sheets hold {args.per_sheet} tiles each, {args.cols} per row, in reading order\n\n"
        + "\n".join(index) + "\n"
    )
    print(f"frames.py: {len(frames)} stills from {video.name} ({duration:.1f}s) -> {out}")
    for s in sheets:
        print(f"SHEET: {s}")
    print((out / "index.txt").read_text())


if __name__ == "__main__":
    main()
