#!/usr/bin/env python3
"""Unit tests for the cross-platform wrapper (scripts/render_in_container.py) and installer
(install.py) that need no Docker: Windows path forms for docker bind mounts, argument parsing,
the image source hash (must equal the shell pipeline the image label was made with), and the
installer's link/junction/copy logic in a temporary HOME.

Run: python3 tests/test_wrapper.py      (stdlib unittest; Linux, macOS or Windows)
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "manim-video"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ric = load("render_in_container", SKILL / "scripts" / "render_in_container.py")
inst = load("install_skill", ROOT / "install.py")


class WindowsPaths(unittest.TestCase):
    CASES = [
        (r"C:\Users\me\jobs\demo", "C:/Users/me/jobs/demo"),
        (r"c:\Users\me\jobs\demo\\", "C:/Users/me/jobs/demo"),
        ("C:/Users/me/jobs/demo", "C:/Users/me/jobs/demo"),
        (r"D:\\", "D:/"),
        ("D:", "D:/"),
        (r"C:\Users\Jane Doe\My Videos\job 1", "C:/Users/Jane Doe/My Videos/job 1"),
        (r"\\?\C:\Users\me\very\long\path", "C:/Users/me/very/long/path"),
        ("/c/Users/me/jobs/demo", "C:/Users/me/jobs/demo"),            # MSYS / Git Bash
        ("/cygdrive/e/work/job", "E:/work/job"),                       # Cygwin
        (r"C:\Users\me\\\jobs\\demo", "C:/Users/me/jobs/demo"),
        (r"C:\Users\me\café\job", "C:/Users/me/café/job"),
    ]
    REFUSED = [
        r"\\wsl$\Ubuntu\home\me\job",
        r"\\wsl.localhost\Ubuntu-24.04\home\me\job",
        r"\\fileserver\share\job",
        r"\\?\UNC\fileserver\share\job",
        r"jobs\demo",
        "/home/me/job",
    ]

    def test_converted(self):
        for src, want in self.CASES:
            with self.subTest(src=src):
                self.assertEqual(ric.to_docker_path(src, windows=True), want)

    def test_refused(self):
        for src in self.REFUSED:
            with self.subTest(src=src):
                with self.assertRaises(ric.PathError):
                    ric.to_docker_path(src, windows=True)

    def test_posix_unchanged(self):
        for p in ("/home/me/job", "/mnt/c/Users/me/job", "/Users/me/My Job"):
            self.assertEqual(ric.to_docker_path(p, windows=False), p)


class Args(unittest.TestCase):
    def test_render(self):
        o = ric.parse_args(["jobs/x", "--quality", "final", "--workers", "4", "--no-build"])
        self.assertEqual((o["job"], o["quality"], o["workers"], o["no_build"], o["action"]),
                         ("jobs/x", "final", "4", True, "render"))

    def test_frames_passthrough(self):
        o = ric.parse_args(["jobs/x", "--frames", "--at", "1.5,3", "--count", "4"])
        self.assertEqual(o["action"], "frames")
        self.assertEqual(o["frame_args"], ["--at", "1.5,3", "--count", "4"])

    def test_errors(self):
        for bad in (["j", "--quality", "4k"], ["j", "--still", "x"], ["j", "k"], ["j", "--bogus"],
                    ["j", "--workers", "many"]):
            with self.subTest(args=bad):
                with self.assertRaises(ric.Exit) as cm:
                    ric.parse_args(bad)
                self.assertEqual(cm.exception.code, 2)


class SourceHash(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "needs a POSIX shell with sha256sum")
    def test_matches_shell_pipeline(self):
        files = ["docker/Dockerfile", "docker/requirements.lock", "docker/manim_job.py"]
        files += sorted((p.name for p in (SKILL / "scripts").glob("*.py") if p.name != "render_in_container.py"),
                        key=str.encode)
        cmd = "cat " + " ".join(f"'{f}'" if f.startswith("docker/") else f"'scripts/{f}'" for f in files) \
              + " | sha256sum | cut -c1-16"
        out = subprocess.run(["sh", "-c", cmd], cwd=SKILL, capture_output=True, text=True,
                             env=dict(os.environ, LC_ALL="C")).stdout.strip()
        self.assertEqual(ric.source_sha(), out)

    def test_wrapper_not_in_image_context(self):
        lines = (SKILL / ".dockerignore").read_text().splitlines()
        self.assertIn("scripts/render_in_container.py", lines)
        self.assertGreater(lines.index("scripts/render_in_container.py"), lines.index("!scripts/*.py"))


class Installer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_install(self, *args):
        return inst.main(list(args), home=self.home, quiet=True)

    def test_link_and_uninstall(self):
        self.assertEqual(self.run_install(), 0)
        for d in (".agents/skills", ".claude/skills"):
            link = self.home / d / "manim-video"
            self.assertTrue((link / "SKILL.md").is_file(), d)
            self.assertTrue(inst.is_link_like(link), d)
            self.assertEqual(Path(os.path.realpath(link)), SKILL.resolve())
        self.assertEqual(self.run_install(), 0)                      # idempotent
        self.assertEqual(self.run_install("--uninstall"), 0)
        for d in (".agents/skills", ".claude/skills"):
            self.assertFalse(os.path.lexists(self.home / d / "manim-video"))
        self.assertTrue(SKILL.joinpath("SKILL.md").is_file())       # the source is untouched

    def test_copy_mode(self):
        self.assertEqual(self.run_install("--copy", "--no-claude"), 0)
        dest = self.home / ".agents/skills/manim-video"
        self.assertFalse(inst.is_link_like(dest))
        self.assertTrue((dest / "SKILL.md").is_file())
        self.assertTrue((dest / inst.MARKER).is_file())
        self.assertFalse((dest / "scripts" / "__pycache__").exists())
        self.assertEqual(self.run_install("--copy", "--no-claude"), 0)   # refreshes its own copy
        self.assertEqual(self.run_install("--uninstall", "--no-claude"), 0)
        self.assertFalse(dest.exists())

    def test_never_touches_foreign_dir(self):
        foreign = self.home / ".claude/skills/manim-video"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("someone else's")
        self.assertEqual(self.run_install("--no-agents"), 1)
        self.assertEqual((foreign / "SKILL.md").read_text(), "someone else's")
        self.assertEqual(self.run_install("--no-agents", "--force"), 1)  # --force never replaces a real dir
        self.assertEqual(self.run_install("--uninstall", "--no-agents"), 0)
        self.assertTrue((foreign / "SKILL.md").is_file())

    def test_dry_run_changes_nothing(self):
        self.assertEqual(self.run_install("--dry-run"), 0)
        self.assertFalse((self.home / ".agents").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
