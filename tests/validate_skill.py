#!/usr/bin/env python3
"""Validate skills/manim-video for cross-agent portability.

1. The agentskills.io reference validator (`skills-ref`), run through uvx if available.
2. Our own lint: frontmatter keys limited to the spec's portable set, name matches the folder,
   description length, SKILL.md under 500 lines, no agent-specific syntax or tool names, and every
   relative link in SKILL.md and references/ points to a file that exists.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "manim-video"
errors: list[str] = []

text = (SKILL / "SKILL.md").read_text()
m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
if not m:
    sys.exit("SKILL.md has no frontmatter")
front = {}
for line in m.group(1).splitlines():
    if not line.strip():
        continue
    if line.startswith((" ", "\t")):
        errors.append(f"nested frontmatter is not portable: {line!r}")
        continue
    key, _, value = line.partition(":")
    front[key.strip()] = value.strip()

allowed = {"name", "description", "license", "compatibility"}
if set(front) - allowed:
    errors.append(f"frontmatter keys outside the portable set: {sorted(set(front) - allowed)}")
if front.get("name") != SKILL.name:
    errors.append(f"name {front.get('name')!r} does not match folder {SKILL.name!r}")
if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", front.get("name", "")) or len(front.get("name", "")) > 64:
    errors.append("name must be lowercase letters, digits and single hyphens, at most 64 chars")
if not 1 <= len(front.get("description", "")) <= 1024:
    errors.append("description must be 1-1024 characters")
if len(front.get("compatibility", "")) > 500:
    errors.append("compatibility must be at most 500 characters")

lines = text.count("\n") + 1
if lines >= 500:
    errors.append(f"SKILL.md has {lines} lines; keep it under 500")

banned = {
    r"\{baseDir\}": "OpenClaw-only {baseDir}",
    r"\$\{CLAUDE_SKILL_DIR\}": "Claude Code-only ${CLAUDE_SKILL_DIR}",
    r"!`": "Claude Code-only backtick-bang command",
    r"\b(Read|Write|Edit|Bash|Glob|Grep|WebFetch|Task) tool\b": "agent-specific tool name",
    r"\bread_file\b|\bapply_patch\b|\bexec_command\b|\bterminal\(": "agent-specific tool name",
    r"metadata\.hermes|metadata\.openclaw": "agent-specific metadata",
}
docs = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md")), *sorted((SKILL / "templates").glob("*"))]
for doc in docs:
    body = doc.read_text()
    for pattern, why in banned.items():
        for hit in re.finditer(pattern, body):
            line_no = body.count("\n", 0, hit.start()) + 1
            errors.append(f"{doc.relative_to(ROOT)}:{line_no}: {why}: {hit.group(0)!r}")
    if doc.suffix == ".md":
        for link in re.findall(r"\]\(([^)#\s]+)\)", body):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if not (doc.parent / link).exists():
                errors.append(f"{doc.relative_to(ROOT)}: broken link {link}")

for rel in re.findall(r"`((?:scripts|references|templates)/[\w./-]+)`", text):
    if not (SKILL / rel).exists():
        errors.append(f"SKILL.md mentions missing file {rel}")

uvx = shutil.which("uvx") or str(Path.home() / ".local/bin/uvx")
if Path(uvx).exists():
    res = subprocess.run([uvx, "--from", "skills-ref==0.1.1", "agentskills", "validate", str(SKILL)],
                         capture_output=True, text=True)
    print("skills-ref:", (res.stdout + res.stderr).strip().splitlines()[-1])
    if res.returncode != 0:
        errors.append("skills-ref validate failed")
else:
    print("skills-ref: skipped (uvx not found)")

print(f"SKILL.md: {lines} lines, frontmatter keys {sorted(front)}, description {len(front['description'])} chars")
if errors:
    print("\n".join("ERROR " + e for e in errors))
    sys.exit(1)
print("validate_skill: OK")
