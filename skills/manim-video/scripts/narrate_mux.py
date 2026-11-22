#!/usr/bin/env python3
"""Narration fallback without manim-voiceover: one WAV per beat, measured, then muxed.

Step 1, before rendering: synthesize and measure.
  narrate_mux.py tts NARRATION.json [--out-dir DIR]
NARRATION.json:
  {"lead_in": 0.5, "gap": 0.6,
   "beats": [{"id": "intro", "text": "Start with a circle of radius one."},
             {"id": "sine", "text": "...", "gap": 1.2}]}
Writes DIR (default: audio/ next to the JSON) with NN_<id>.wav and timeline.json:
  {"lead_in": 0.5, "total": 41.7,
   "beats": [{"id": "intro", "file": "01_intro.wav", "duration": 2.9, "start": 0.5, "slot": 3.5}, ...]}
Beat i starts at lead_in + the sum of earlier slots; slot = duration + gap. The scene reads
timeline.json and gives every beat exactly `slot` seconds (see references/narration.md).

Step 2, after rendering: lay the clips on the video's timeline.
  narrate_mux.py mux VIDEO TIMELINE.json [--out OUT.mp4] [--offset SECONDS]

Settings: KOKORO_BASE_URL [http://127.0.0.1:8880/v1], KOKORO_MODEL [kokoro], KOKORO_VOICE [af_heart],
KOKORO_API_KEY (optional; read from the environment, never printed). Needs ffmpeg and ffprobe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _ffbin import tool


def duration_of(path: Path) -> float:
    out = subprocess.run([tool("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def synthesize(text: str, dest: Path, voice: str, model: str, base_url: str, speed: float) -> None:
    body = json.dumps({"model": model, "input": text, "voice": voice, "response_format": "wav",
                       "speed": speed}).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("KOKORO_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["KOKORO_API_KEY"]
    req = urllib.request.Request(f"{base_url.rstrip('/')}/audio/speech", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            audio = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f"narrate_mux.py: TTS request to {base_url} failed: {exc}")
    if len(audio) < 100:
        sys.exit(f"narrate_mux.py: TTS returned {len(audio)} bytes for {text[:50]!r}")
    dest.write_bytes(audio)


def cmd_tts(args) -> None:
    spec = json.loads(args.narration.read_text())
    out_dir = (args.out_dir or args.narration.parent / "audio").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = os.environ.get("KOKORO_VOICE", "af_heart")
    model = os.environ.get("KOKORO_MODEL", "kokoro")
    base = os.environ.get("KOKORO_BASE_URL", "http://127.0.0.1:8880/v1")
    speed = float(spec.get("speed", 1.0))
    lead_in, default_gap = float(spec.get("lead_in", 0.5)), float(spec.get("gap", 0.6))
    old = {}
    if (out_dir / "timeline.json").exists():
        old = {b["id"]: b for b in json.loads((out_dir / "timeline.json").read_text())["beats"]}
    beats, t = [], lead_in
    for i, beat in enumerate(spec["beats"], 1):
        bid = beat["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", bid):
            sys.exit(f"narrate_mux.py: beat id {bid!r} must be letters, digits, _ or -")
        text = " ".join(beat["text"].split())
        digest = hashlib.sha256(f"{model}|{voice}|{speed}|{text}".encode()).hexdigest()[:12]
        dest = out_dir / f"{i:02d}_{bid}.wav"
        if not (dest.exists() and old.get(bid, {}).get("hash") == digest):
            synthesize(text, dest, voice, model, base, speed)
            print(f"tts: {dest.name}")
        d = duration_of(dest)
        slot = d + float(beat.get("gap", default_gap))
        beats.append({"id": bid, "file": dest.name, "text": text, "hash": digest,
                      "duration": round(d, 3), "start": round(t, 3), "slot": round(slot, 3)})
        t += slot
    timeline = {"lead_in": lead_in, "total": round(t, 3), "voice": voice, "beats": beats}
    (out_dir / "timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")
    print(f"narrate_mux.py: {len(beats)} clips, narration ends at {t:.1f}s -> {out_dir / 'timeline.json'}")
    for b in beats:
        print(f"  {b['id']:<20} start {b['start']:7.2f}s  speech {b['duration']:5.2f}s  slot {b['slot']:5.2f}s")


def cmd_mux(args) -> None:
    timeline = json.loads(args.timeline.read_text())
    base = args.timeline.parent.resolve()
    video = args.video.resolve()
    out = (args.out or video.with_name(video.stem + "_narrated.mp4")).resolve()
    vdur = duration_of(video)
    end = timeline["total"] + args.offset
    if end > vdur + 0.25:
        print(f"narrate_mux.py: WARNING narration ends at {end:.2f}s but the video is {vdur:.2f}s; "
              f"the tail will be cut. Lengthen the scene's waits.", file=sys.stderr)
    cmd = [tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-i", str(video)]
    parts = []
    for i, b in enumerate(timeline["beats"], 1):
        cmd += ["-i", str(base / b["file"])]
        ms = int(round((b["start"] + args.offset) * 1000))
        parts.append(f"[{i}:a]aresample=48000,adelay={ms}:all=1[a{i}]")
    n = len(timeline["beats"])
    mix = "".join(f"[a{i}]" for i in range(1, n + 1))
    # Pad or trim the mix to exactly the video's length (no -shortest: it can hang with apad).
    graph = (";".join(parts) + f";{mix}amix=inputs={n}:normalize=0:dropout_transition=0,"
             f"apad=whole_dur={vdur:.3f},atrim=0:{vdur:.3f}[aout]")
    cmd += ["-filter_complex", graph, "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"VIDEO: {out}  (video {vdur:.2f}s, narration ends {end:.2f}s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tts", help="synthesize one WAV per beat and write timeline.json")
    t.add_argument("narration", type=Path)
    t.add_argument("--out-dir", type=Path)
    m = sub.add_parser("mux", help="mux the clips onto a rendered video")
    m.add_argument("video", type=Path)
    m.add_argument("timeline", type=Path)
    m.add_argument("--out", type=Path)
    m.add_argument("--offset", type=float, default=0.0, help="shift all clips by this many seconds")
    args = ap.parse_args()
    cmd_tts(args) if args.cmd == "tts" else cmd_mux(args)


if __name__ == "__main__":
    main()
