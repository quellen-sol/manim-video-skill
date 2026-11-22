#!/usr/bin/env python3
"""Render every scene in references/scene-patterns.md, to prove the reference code works.

Usage: tests/check_patterns.py [--out DIR] [--only ClassName ...]
Writes one scene file per pattern into DIR (default: out/patterns), renders each with
render.sh preview, and prints render status, layout warnings and qa_check results.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "manim-video"
DOC = SKILL / "references" / "scene-patterns.md"

ap = argparse.ArgumentParser()
ap.add_argument("--out", type=Path, default=ROOT / "out" / "patterns")
ap.add_argument("--only", nargs="*")
args = ap.parse_args()

blocks = re.findall(r"```python\n(.*?)```", DOC.read_text(), flags=re.S)
header, bodies = blocks[0], blocks[1:]
args.out.mkdir(parents=True, exist_ok=True)
failed = 0
for body in bodies:
    classes = re.findall(r"^class (\w+)\(", body, flags=re.M)
    if not classes:
        continue
    name = classes[-1]
    if args.only and name not in args.only:
        continue
    path = args.out / f"{name}.py"
    path.write_text(header + "\n\n" + body)
    res = subprocess.run([str(SKILL / "scripts" / "render.sh"), "preview", str(path), name],
                         capture_output=True, text=True)
    out = res.stdout + res.stderr
    video = next((l.split()[1] for l in out.splitlines() if l.startswith("VIDEO:")), None)
    status = "OK" if res.returncode == 0 and video else f"FAILED ({res.returncode})"
    print(f"== {name}: {status}")
    for line in out.splitlines():
        if line.startswith("LAYOUT") and " END " not in line:
            print("   " + line)
    if status != "OK":
        failed += 1
        print("\n".join("   " + l for l in out.splitlines()[-25:]))
        continue
    qa = subprocess.run([sys.executable, str(SKILL / "scripts" / "qa_check.py"), video],
                        capture_output=True, text=True)
    for line in qa.stdout.splitlines():
        if line.strip().startswith(("WARN", "FAIL")):
            print("   qa " + line.strip())
print(f"{failed} pattern(s) failed")
sys.exit(1 if failed else 0)
