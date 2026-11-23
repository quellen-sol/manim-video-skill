#!/usr/bin/env python3
"""Make the manim-video skill discoverable by agents by linking ONE canonical copy
(skills/manim-video in this repo) into each agent's skills directory. No edits to any agent's
config. Linux, macOS and Windows; Python 3.9+, standard library only. The shims install.sh and
install.ps1 run this file with the same options.

Usage: install.py [--openclaw] [--no-claude] [--no-agents] [--copy] [--force] [--uninstall] [--dry-run]

Default links (~ is %USERPROFILE% on Windows):
  ~/.agents/skills/manim-video  -> Codex CLI and OpenClaw read this directory natively;
                                   Hermes reads it once you add it to skills.external_dirs.
  ~/.claude/skills/manim-video  -> Claude Code ($CLAUDE_CONFIG_DIR/skills if that is set).
How it links: a symlink; on Windows without symlink rights (Developer Mode off, not elevated) a
directory junction; if neither works, or with --copy, a copy marked with .manim-video-install.json
(re-run install.py after pulling to refresh a copy; links never go stale).
Options:
  --openclaw   also link ~/.openclaw/skills/manim-video (only if your OpenClaw does not read
               ~/.agents/skills; with both, OpenClaw sees the same skill twice)
  --no-claude  skip ~/.claude/skills       --no-agents  skip ~/.agents/skills
  --copy       copy instead of linking (for sandboxes that do not follow links)
  --force      replace a link (or a marked copy) that points to another checkout; never a real
               directory that this script did not create
  --uninstall  remove only links and marked copies that belong to this repo's skill
  --dry-run    print what would happen
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("install.py: needs Python 3.9 or newer")

NAME = "manim-video"
MARKER = ".manim-video-install.json"
SRC = (Path(__file__).resolve().parent / "skills" / NAME)
IS_WINDOWS = os.name == "nt"


def _norm(p) -> str:
    return os.path.normcase(os.path.realpath(str(p)))


def is_junction(p: Path) -> bool:
    if hasattr(os.path, "isjunction"):            # Python 3.12+
        return os.path.isjunction(p)
    if not IS_WINDOWS:
        return False
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)) \
        and getattr(st, "st_reparse_tag", None) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)


def is_link_like(p: Path) -> bool:
    return os.path.islink(p) or is_junction(p)


def link_target(p: Path) -> str:
    try:
        return os.readlink(p)
    except OSError:
        return os.path.realpath(p)


def marker_source(p: Path) -> str | None:
    try:
        return json.loads((p / MARKER).read_text()).get("source")
    except (OSError, ValueError, AttributeError):
        return None


def remove_link(p: Path) -> None:
    # Never rmtree a link or junction: that would delete the skill itself.
    try:
        os.unlink(p)
    except (IsADirectoryError, PermissionError, OSError):
        os.rmdir(p)


def make_junction(src: Path, link: Path) -> bool:
    try:
        import _winapi
        _winapi.CreateJunction(str(src), str(link))
        return True
    except Exception:
        pass
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(src)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0 and is_link_like(link)


def make_copy(src: Path, dest: Path) -> None:
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "out", "media"))
    (dest / MARKER).write_text(json.dumps({"source": str(src), "installed": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                           "note": "copy made by install.py; re-run it to refresh"}, indent=1) + "\n")


def targets(home: Path | None, agents: bool, claude: bool, openclaw: bool) -> list[Path]:
    h = home or Path.home()
    out = []
    if agents:
        out.append(h / ".agents" / "skills")
    if claude:
        cfg = os.environ.get("CLAUDE_CONFIG_DIR") if home is None else None
        out.append((Path(cfg) if cfg else h / ".claude") / "skills")
    if openclaw:
        out.append(h / ".openclaw" / "skills")
    return out


def next_steps(say) -> None:
    hermes_cfg = (r"%LOCALAPPDATA%\hermes\config.yaml (native install; or $HERMES_HOME), or ~/.hermes/config.yaml in WSL2"
                  if IS_WINDOWS else "~/.hermes/config.yaml")
    agents_dir = (Path.home() / ".agents" / "skills").as_posix() if IS_WINDOWS else "~/.agents/skills"
    say(f"""
Hermes Agent (not changed by this script): add the shared directory to {hermes_cfg}
  skills:
    external_dirs:
      - {agents_dir}
Hermes may edit skills in external dirs in place; consider skills.write_approval: true.
""")
    if IS_WINDOWS:
        say(f"""Next, the render container (needs Docker Desktop running, WSL2 backend):
  & "{SRC / 'scripts' / 'render-in-container.ps1'}" --check
  & "{SRC / 'scripts' / 'render-in-container.ps1'}" --build     # builds manim-video:local (about 6 min)""")
    else:
        say(f"""Next, the render container (the default render route; needs Docker with the compose plugin):
  {SRC}/scripts/setup_env.sh          # builds the image manim-video:local (about 6 min, no sudo)
  {SRC}/scripts/check_env.sh          # read-only check; add --gpu, --tts
Host route (fallback without Docker, Linux/macOS; needs Cairo/Pango headers and LaTeX):
  {SRC}/scripts/setup_env.sh --host --no-image""")


def main(argv: list[str], home: Path | None = None, quiet: bool = False) -> int:
    opts = {"--openclaw": False, "--no-claude": False, "--no-agents": False, "--copy": False,
            "--force": False, "--uninstall": False, "--dry-run": False}
    for a in argv:
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a not in opts:
            print(f"install.py: unknown option {a}", file=sys.stderr)
            return 2
        opts[a] = True
    say = (lambda *a, **k: None) if quiet else print
    warn = (lambda *a, **k: None) if quiet else (lambda m: print(m, file=sys.stderr))
    if not (SRC / "SKILL.md").is_file():
        warn(f"install.py: {SRC / 'SKILL.md'} not found")
        return 1
    dry, force = opts["--dry-run"], opts["--force"]

    def run(desc: str, fn, *a) -> None:
        if dry:
            say(f"  (dry run) {desc}")
        else:
            fn(*a)

    rc = 0
    src_n = _norm(SRC)
    for d in targets(home, not opts["--no-agents"], not opts["--no-claude"], opts["--openclaw"]):
        link = d / NAME
        exists = os.path.lexists(link)
        linky = exists and is_link_like(link)
        ours_link = linky and _norm(link) == src_n
        msrc = marker_source(link) if exists and not linky else None
        ours_copy = msrc is not None and _norm(msrc) == src_n

        if opts["--uninstall"]:
            if ours_link:
                say(f"remove  {link}")
                run(f"remove link {link}", remove_link, link)
            elif ours_copy:
                say(f"remove  {link} (copy made by install.py)")
                run(f"delete copy {link}", shutil.rmtree, link)
            elif exists:
                say(f"keep    {link} (not a link to this repo; left alone)")
            else:
                say(f"absent  {link}")
            continue

        if ours_link:
            say(f"ok      {link} -> {SRC} (already linked)")
            if not opts["--copy"]:
                continue
            say(f"relink  {link} (switching to a copy)")
            run(f"remove link {link}", remove_link, link)
        elif linky:
            if not force:
                warn(f"SKIP    {link} points to {link_target(link)}; use --force to replace it")
                rc = 1
                continue
            say(f"relink  {link} (was -> {link_target(link)})")
            run(f"remove link {link}", remove_link, link)
        elif ours_copy or (msrc is not None and force):
            say(f"refresh {link} (copy made by install.py)")
            run(f"delete copy {link}", shutil.rmtree, link)
        elif msrc is not None:
            warn(f"SKIP    {link} is a copy of {msrc}; use --force to replace it")
            rc = 1
            continue
        elif exists:
            warn(f"SKIP    {link} exists and is not a link made by this script; not touching it")
            rc = 1
            continue

        if not d.is_dir():
            say(f"mkdir   {d}")
            run(f"mkdir {d}", d.mkdir, 0o777, True, True)
        if dry:
            say(f"  (dry run) link {link} -> {SRC}" + (" (copy)" if opts["--copy"] else ""))
            continue
        if opts["--copy"]:
            make_copy(SRC, link)
            say(f"copy    {link} <- {SRC} (re-run install after pulling to refresh it)")
            continue
        try:
            os.symlink(SRC, link, target_is_directory=True)
            say(f"link    {link} -> {SRC}")
            continue
        except OSError as exc:
            if not IS_WINDOWS:
                warn(f"FAIL    {link}: cannot create a symlink ({exc})")
                rc = 1
                continue
        if make_junction(SRC, link):
            say(f"junction {link} -> {SRC} (symlinks need Developer Mode or an elevated shell)")
            continue
        make_copy(SRC, link)
        say(f"copy    {link} <- {SRC} (no symlink or junction rights; re-run install after pulling)")

    if not opts["--uninstall"]:
        next_steps(say)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
