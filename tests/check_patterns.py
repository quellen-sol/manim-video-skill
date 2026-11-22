#!/usr/bin/env python3
"""Render every scene in references/scene-patterns.md, to prove the reference code works.

Usage: tests/check_patterns.py [--route container|host] [--out DIR] [--only ClassName ...]
Writes one scene per pattern into DIR (default: out/patterns-<route>) and renders each at preview
quality: --route container (default) makes one job directory per pattern and runs
render-in-container.sh; --route host runs render.sh and qa_check.py on the host. Prints render
status, layout warnings and check results.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "manim-video"
DOC = SKILL / "references" / "scene-patterns.md"

ap = argparse.ArgumentParser()
ap.add_argument("--route", choices=["container", "host"], default="container")
ap.add_argument("--out", type=Path)
ap.add_argument("--only", nargs="*")
args = ap.parse_args()
args.out = args.out or ROOT / "out" / f"patterns-{args.route}"

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
    if args.route == "container":
        job = args.out / name
        job.mkdir(parents=True, exist_ok=True)
        (job / "scene.py").write_text(header + "\n\n" + body)
        (job / "job.json").write_text(json.dumps({"scene": name, "stills": "none"}) + "\n")
        res = subprocess.run([str(SKILL / "scripts" / "render-in-container.sh"), str(job)],
                             capture_output=True, text=True)
        ok = res.returncode in (0, 1) and (job / "out" / "report.json").is_file()
        print(f"== {name}: {'OK' if ok else f'FAILED ({res.returncode})'}")
        if not ok:
            failed += 1
            print("\n".join("   " + l for l in (res.stdout + res.stderr).splitlines()[-25:]))
            continue
        report = json.loads((job / "out" / "report.json").read_text())
        for w in report.get("scene_warnings", []):
            if " END " not in w:
                print("   " + w)
        for c in report.get("checks", []):
            if c["level"] in ("WARN", "FAIL"):
                print(f"   qa {c['level']} {c['check']} {c['message']}")
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
