"""Git, visually: a commit is a snapshot that points to its parent, a branch is a movable label,
merge joins histories with a two-parent commit, rebase replays commits as new copies, a person
resolves conflicts, and teams reach a protected main only through reviewed pull requests.

Render: "$SKILL_DIR/scripts/render-in-container.sh" JOB_DIR   (job.json: {"scene": "Explainer"})
"""

from manim import *

try:  # layout checker; on PYTHONPATH when rendered with render.sh
    from manim_qa import LayoutGuard
except ImportError:  # keeps the file renderable without the skill
    print("LAYOUT-GUARD unavailable: manim_qa not importable; layout checks are off", flush=True)

    class LayoutGuard:
        pass

try:  # measured geometry checker (render image)
    from geometry_qa import GeometryGuard, centered_in, concentric, symmetric, within_margin
except ImportError:
    print("GEOMETRY-GUARD unavailable: geometry_qa not importable; geometry checks are off", flush=True)

    class GeometryGuard:
        def geo_track(self, **_):
            return self

        def geo_rule(self, *_):
            return self

    def _rule(*_, **__):
        return None
    centered_in = concentric = symmetric = within_margin = _rule

# --- style (references/style-guide.md) -----------------------------------------------
config.background_color = "#0F1117"
config.max_files_cached = 1000            # >100 animations: keep every partial for frames.py --beats
Text.set_default(font="Noto Sans")        # the Docker image's default font is a serif
MarkupText.set_default(font="Noto Sans")
MONO = "Noto Mono"
BG = "#0F1117"
CARD_BG = "#1A1E28"

# --- colour legend (storyboard.md): one colour per concept ---------------------------
C_MAIN = BLUE       # main branch: tag, commits on main, "ours", the rename
C_FEAT = ORANGE     # feature branch: tag, its commits and their copies, "theirs", the caching
C_HEAD = WHITE      # HEAD tag (outlined)
C_FOCUS = YELLOW    # look here now: unsaved edits, arrows being pointed out
C_BAD = RED         # conflict, rejected (always paired with a word)
C_GOOD = GREEN      # resolved, approved (always paired with a word)
C_MUTED = GREY_B    # captions' secondary text, scaffolding
C_EDGE = GREY_B     # parent arrows

MARGIN_X = 1.15          # side margin, about 8 % of the 14.22-unit frame width
EDGE = np.array([MARGIN_X, 0.65, 0.0])   # title and command chip: 8 % from the sides and top
TITLE_SIZE = 40
CAPTION_SIZE = 30
LABEL_SIZE = 28
SMALL_SIZE = 24
CODE_SIZE = 26

# --- commit graph geometry ------------------------------------------------------------
MAIN_Y, FEAT_Y = 0.75, -1.05
R = 0.38            # commit radius
TAG_H = 0.42
TAG_STEP = 0.5      # distance between stacked tags
X = {"c1": -5.25, "c2": -3.75, "c3": -2.25, "f1": -0.75, "f2": 0.75, "c4": 2.25,
     "m": 3.75, "f1r": 3.3, "f2r": 4.8, "f1s": 3.75, "f2s": 5.25}   # final line: -5.25 .. 5.25


def v(x, y):
    return np.array([x, y, 0.0])


def span(text, color):
    return f'<span fgcolor="{ManimColor(color).to_hex()}">{text}</span>'


def code_text(markup, color=WHITE):
    return MarkupText(markup, font=MONO, font_size=CODE_SIZE, color=color)


def commit_node(cid, x, y, color, radius=R, font_size=24):
    circ = Circle(radius=radius, color=color, stroke_width=4).set_fill(color, opacity=0.25)
    group = VGroup(circ)
    if cid:
        group.add(Text(cid, font=MONO, font_size=font_size, color=WHITE))
    return group.move_to([x, y, 0])


def arrow_between(a, b, radius=R, color=C_EDGE, width=3, tip=0.16):
    """Arrow from point a to point b, stopping at the rim of circles of `radius`."""
    return Arrow(a, b, buff=radius + 0.05, color=color, stroke_width=width, tip_length=tip,
                 max_tip_length_to_length_ratio=0.35, max_stroke_width_to_length_ratio=8)


def parent_arrow(child, parent, color=C_EDGE):
    """Git stores a pointer from each commit to its parent: the arrow points backwards."""
    return arrow_between(child.get_center(), parent.get_center(), color=color)


def branch_tag(name, color, font_size=26):
    label = Text(name, font_size=font_size, color=BG, weight=BOLD)
    plate = RoundedRectangle(corner_radius=0.1, width=label.width + 0.32, height=TAG_H,
                             stroke_width=0).set_fill(color, opacity=1)
    label.move_to(plate)
    return VGroup(plate, label)


def head_tag():
    label = Text("HEAD", font_size=SMALL_SIZE, color=C_HEAD, weight=BOLD)
    plate = RoundedRectangle(corner_radius=0.1, width=label.width + 0.32, height=TAG_H,
                             stroke_color=C_HEAD, stroke_width=2).set_fill(BG, opacity=1)
    label.move_to(plate)
    return VGroup(plate, label)


def slot(node, side, k=0):
    """Centre of the k-th tag stacked above (side=UP) or below (side=DOWN) a commit."""
    return node.get_center() + side * (R + 0.14 + TAG_H / 2 + k * TAG_STEP)


def doc_card():
    body = RoundedRectangle(corner_radius=0.12, width=1.9, height=2.1, stroke_color=WHITE,
                            stroke_width=3).set_fill(CARD_BG, opacity=1)
    name = Text("app.py", font=MONO, font_size=SMALL_SIZE, color=C_MUTED)
    name.move_to(body.get_top() + 0.32 * DOWN)
    lines = VGroup(*[Line(ORIGIN, w * RIGHT, stroke_width=6, color=C_MUTED) for w in (1.3, 0.9, 1.1)])
    lines.arrange(DOWN, buff=0.27, aligned_edge=LEFT)
    lines.next_to(name, DOWN, buff=0.32).align_to(body, LEFT).shift(0.3 * RIGHT)
    return VGroup(body, name, lines)


def code_card(header, markup, color, width=None):
    code = code_text(markup).set_z_index(2)
    box = RoundedRectangle(corner_radius=0.12, width=max(code.width + 0.6, width or 0), height=code.height + 0.5,
                           stroke_color=color, stroke_width=3).set_fill(CARD_BG, opacity=1)
    code.move_to(box)
    head = Text(header, font_size=SMALL_SIZE, color=color).next_to(box, UP, buff=0.15, aligned_edge=LEFT)
    return VGroup(head, box, code)


def check_mark(color=C_GOOD, size=0.34):
    mark = VMobject(stroke_color=color, stroke_width=7)
    mark.set_points_as_corners([np.array([-0.5, 0.02, 0]), np.array([-0.15, -0.38, 0]),
                                np.array([0.5, 0.42, 0])])
    return mark.scale_to_fit_height(size)


def cross_mark(color=C_BAD, size=0.45):
    return VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(color, width=8).scale_to_fit_height(size)


def padlock(color=C_MUTED):
    body = RoundedRectangle(corner_radius=0.05, width=0.36, height=0.28, stroke_width=0).set_fill(color, 1)
    shackle = Arc(radius=0.12, start_angle=0, angle=PI, stroke_width=4, color=color)
    shackle.next_to(body, UP, buff=0)
    return VGroup(shackle, body)


def flow_box(label, color, width=2.6, height=1.0):
    rect = RoundedRectangle(corner_radius=0.15, width=width, height=height, color=color,
                            stroke_width=3).set_fill(color, opacity=0.15)
    return VGroup(rect, Text(label, font_size=LABEL_SIZE).move_to(rect))


class Explainer(GeometryGuard, LayoutGuard, Scene):
    def construct(self):
        self.title = self.caption = self.cmd = None
        self.graph = VGroup()       # every commit, arrow and tag of chapters 1-4 (added as created)
        off = VGroup()
        self.geo_track(graph=self.graph, forked=off, history=off, merge_commit=off, cards=off,
                       options=off, protected=off, pipeline=off, policies=off, recap=off)
        self.geo_rule(
            centered_in("titlecard", "frame"),
            within_margin("title", 7), within_margin("chip", 7), within_margin("caption", 7),
            within_margin("card", 7),
            within_margin("graph", 7),                                    # chapters 1-4
            symmetric("forked", about=(0, 0), axis="x"),                  # two-lane graph after the rebase
            symmetric("history", about=(0, 0), axis="x"),                 # the straightened line
            symmetric("main_tag", about="merge_commit", axis="x"),        # tags stacked on their commit
            symmetric("head_tag", about="merge_commit", axis="x"),
            concentric("merge_ring", "merge_id"),                         # id centred in its commit
            symmetric("cards", about=(0, 0), axis="x"), within_margin("cards", 7),
            symmetric("options", about=(0, 0), axis="x"), within_margin("options", 7),
            symmetric("protected", about=(0, 0), axis="x"), within_margin("protected", 7),
            symmetric("pipeline", about=(0, 0), axis="x"), within_margin("pipeline", 7),
            symmetric("policies", about=(0, 0), axis="x"), within_margin("policies", 7),
            symmetric("recap", about=(0, 0), axis="x"),
        )
        self.beat_title_card()
        self.beat_commits()
        self.beat_branches()
        self.beat_merge()
        self.beat_rebase()
        self.beat_conflict_cause()
        self.beat_conflict_resolve()
        self.beat_protected_main()
        self.beat_pull_request()
        self.beat_merge_policies()
        self.beat_recap()

    # --- persistent bands: chapter title, command chip, caption --------------------------
    @staticmethod
    def swap(old, new, shift=ORIGIN):
        """Old text out, then new text in (never both half-visible at the same spot)."""
        if old is None and new is None:
            return []
        if old is None:
            return [FadeIn(new, shift=shift)]
        if new is None:
            return [FadeOut(old, shift=shift)]
        return [AnimationGroup(FadeOut(old, shift=shift), FadeIn(new, shift=shift), lag_ratio=1.0)]

    def title_to(self, num, name):
        parts = [Text(name, font_size=TITLE_SIZE)]
        if num:
            parts.insert(0, Text(num, font_size=TITLE_SIZE, color=C_MUTED))
        new = VGroup(*parts).arrange(RIGHT, buff=0.3).to_corner(UL, buff=EDGE)
        anims = self.swap(self.title, new, 0.15 * UP)
        self.title = new
        self.geo_track(title=new if new is not None else VGroup())
        return anims

    def caption_to(self, text, color=WHITE):
        new = Text(text, font_size=CAPTION_SIZE, color=color).to_edge(DOWN, buff=0.6) if text else None
        anims = self.swap(self.caption, new, 0.15 * UP)
        self.caption = new
        self.geo_track(caption=new if new is not None else VGroup())
        return anims

    def cmd_to(self, text):
        chip = None
        if text:
            t = Text("$ " + text, font=MONO, font_size=CODE_SIZE, color=C_MUTED)
            box = RoundedRectangle(corner_radius=0.1, width=t.width + 0.4, height=0.6,
                                   stroke_color=DARK_GREY, stroke_width=2).set_fill(CARD_BG, opacity=1)
            chip = VGroup(box, t.move_to(box)).to_corner(UR, buff=EDGE)
        anims = self.swap(self.cmd, chip)
        self.cmd = chip
        self.geo_track(chip=chip if chip is not None else VGroup())
        return anims

    @staticmethod
    def glide(mob, end, o1, o2, **kwargs):
        """Move mob's centre to `end` along a Bezier curve (control points start+o1, end+o2),
        so it can swing around tags and commits instead of sliding across them."""
        start = mob.get_center()
        path = CubicBezier(start, start + np.array(o1), np.array(end) + np.array(o2), np.array(end))
        return MoveAlongPath(mob, path, **kwargs)

    def snapshot(self, parts, node, run_time=1.3):
        """A text-free copy of the file card shrinks into the commit's slot, then the commit fades
        in (FadeTransform stretched the id over "app.py" mid-way)."""
        snap = parts.copy()
        self.play(snap.animate.scale(0.35).move_to(node), run_time=0.8)
        self.play(AnimationGroup(FadeOut(snap), FadeIn(node), lag_ratio=1.0), run_time=run_time - 0.8)

    def clear_stage(self, run_time=1.0):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)
        self.title = self.caption = self.cmd = None

    # --- beats -------------------------------------------------------------------------
    def beat_title_card(self):
        """Beat 1: hook."""
        t = Text("Git, visually", font_size=48)
        s = Text("how a team's code history grows", font_size=CAPTION_SIZE, color=C_MUTED)
        VGroup(t, s).arrange(DOWN, buff=0.35)
        self.play(FadeIn(t, shift=0.3 * UP), run_time=1.0)
        self.play(FadeIn(s, shift=0.2 * UP), run_time=0.8)
        self.geo_track(titlecard=VGroup(t, s))      # measured once both lines are up
        self.wait(1.5)
        self.play(FadeOut(t), FadeOut(s), run_time=0.8)

    def beat_commits(self):
        """Beats 2-3: a commit is a snapshot that points to its parent; a branch is a label."""
        card = doc_card().move_to([0, -1.35, 0])
        self.geo_track(card=card)
        lines = card[2]
        self.play(*self.title_to("1", "Commits"), FadeIn(card, shift=0.3 * UP), run_time=1.0)
        self.play(*self.caption_to("a commit saves a snapshot of your files"),
                  *self.cmd_to("git commit"), run_time=0.8)
        c1 = commit_node("a1f", X["c1"], MAIN_Y, C_MAIN)
        self.graph.add(c1)
        self.snapshot(VGroup(card[0], card[2]), c1)
        self.wait(1.0)

        # an edit (yellow = changed since the last snapshot), then the second snapshot
        l1 = lines[1]
        self.play(Transform(l1, Line(l1.get_start(), l1.get_start() + 1.3 * RIGHT,
                                     stroke_width=6, color=C_FOCUS)), run_time=0.8)
        c2 = commit_node("3c9", X["c2"], MAIN_Y, C_MAIN)
        self.graph.add(c2)
        self.snapshot(VGroup(card[0], card[2]), c2)
        self.play(l1.animate.set_color(C_MUTED), run_time=0.4)
        a21 = parent_arrow(c2, c1)
        self.graph.add(a21)
        self.play(GrowArrow(a21), *self.caption_to("each commit points to its parent"), run_time=1.0)
        self.play(ShowPassingFlash(Line(a21.get_start(), a21.get_end()).set_stroke(C_FOCUS, width=8),
                                   time_width=0.6), run_time=1.0)
        self.wait(1.0)

        main = branch_tag("main", C_MAIN).move_to(slot(c2, UP))
        self.graph.add(main)
        self.play(FadeIn(main, shift=0.3 * DOWN),
                  *self.caption_to("a branch is a label on a commit"), run_time=1.0)
        self.wait(1.2)

        new_line = Line(ORIGIN, 0.8 * RIGHT, stroke_width=6, color=C_FOCUS)
        new_line.next_to(lines, DOWN, buff=0.27, aligned_edge=LEFT)
        self.play(Create(new_line), run_time=0.8)
        c3 = commit_node("7d2", X["c3"], MAIN_Y, C_MAIN)
        self.graph.add(c3)
        self.snapshot(VGroup(card[0], card[2], new_line), c3)
        a32 = parent_arrow(c3, c2)
        self.graph.add(a32)
        self.play(GrowArrow(a32), new_line.animate.set_color(C_MUTED), run_time=0.6)
        self.play(main.animate.move_to(slot(c3, UP)),
                  *self.caption_to("commit again: the label moves along"), run_time=1.0)
        self.wait(1.2)
        self.play(FadeOut(card, shift=0.3 * DOWN), FadeOut(new_line, shift=0.3 * DOWN), run_time=0.8)
        self.c1, self.c2, self.c3, self.main = c1, c2, c3, main
        self.a21, self.a32 = a21, a32

    def beat_branches(self):
        """Beats 4-6: HEAD, a new branch is a new label, only the checked-out branch moves."""
        c3, main = self.c3, self.main
        head = head_tag().move_to(slot(c3, UP, 1))
        self.graph.add(head)
        self.play(*self.title_to("2", "Branches"), FadeIn(head, shift=0.3 * DOWN), *self.cmd_to(None),
                  *self.caption_to("HEAD marks the branch you are on"), run_time=1.0)
        self.wait(1.2)
        feat = branch_tag("feature", C_FEAT).move_to(slot(c3, DOWN))
        self.graph.add(feat)
        self.play(FadeIn(feat, shift=0.3 * UP), *self.cmd_to("git switch -c feature"),
                  *self.caption_to("a new branch: a second label, same commit"), run_time=1.0)
        self.wait(0.6)
        # swing right of the tags and arrive from below-right, never across the feature tag
        self.play(self.glide(head, slot(c3, DOWN, 1), v(1.5, 1.0), v(3.0, -0.5)), run_time=1.2)
        self.wait(0.6)

        f1 = commit_node("e5b", X["f1"], FEAT_Y, C_FEAT)
        af1 = parent_arrow(f1, c3)
        self.graph.add(f1, af1)
        # the tags travel below the lane, then the parent arrow is drawn (it would cross them)
        self.play(FadeIn(f1, scale=0.6), *self.cmd_to("git commit"),
                  self.glide(feat, slot(f1, DOWN), v(-0.5, 0), v(-1.5, -0.5)),
                  self.glide(head, slot(f1, DOWN, 1), v(-0.5, 0), v(-1.5, -0.5)),
                  *self.caption_to("only the branch you are on moves"), run_time=1.2)
        self.play(GrowArrow(af1), run_time=0.6)
        f2 = commit_node("9a0", X["f2"], FEAT_Y, C_FEAT)
        af2 = parent_arrow(f2, f1)
        self.graph.add(f2, af2)
        self.play(FadeIn(f2, scale=0.6), GrowArrow(af2), run_time=0.9)
        self.play(feat.animate.move_to(slot(f2, DOWN)), head.animate.move_to(slot(f2, DOWN, 1)), run_time=0.8)
        stay = SurroundingRectangle(main, color=C_FOCUS, buff=0.08, corner_radius=0.1)
        self.play(Create(stay), run_time=0.5)
        self.play(FadeOut(stay), run_time=0.5)
        self.wait(0.6)

        c4 = commit_node("c48", X["c4"], MAIN_Y, C_MAIN)
        a43 = parent_arrow(c4, c3)
        self.graph.add(c4, a43)
        self.play(FadeIn(c4, scale=0.6), GrowArrow(a43), *self.cmd_to(None),
                  *self.caption_to("meanwhile, a teammate's work lands on main"), run_time=1.0)
        self.play(main.animate.move_to(slot(c4, UP)), run_time=1.0)
        self.wait(0.8)
        self.play(Indicate(c4[0], color=C_FOCUS), Indicate(f2[0], color=C_FOCUS),
                  *self.caption_to("the two histories have diverged"), run_time=1.2)
        self.wait(1.2)
        self.head, self.feat = head, feat
        self.f1, self.f2, self.c4, self.af1, self.af2, self.a43 = f1, f2, c4, af1, af2, a43

    def beat_merge(self):
        """Beat 7: a merge commit has two parents."""
        c4, f2, main, head = self.c4, self.f2, self.main, self.head
        self.play(*self.title_to("3", "Merge"), *self.cmd_to("git switch main"),
                  self.glide(head, slot(c4, UP, 1), v(1.5, -1.5), v(3.5, 1.0)),
                  *self.caption_to("go to main, the branch that receives the work"), run_time=1.2)
        self.wait(1.2)
        m = commit_node("f13", X["m"], MAIN_Y, C_MAIN)
        am4 = parent_arrow(m, c4, C_FOCUS)
        amf = parent_arrow(m, f2, C_FOCUS)
        self.graph.add(m, am4, amf)
        self.play(FadeIn(m, scale=0.6), *self.cmd_to("git merge feature"),
                  *self.caption_to("a merge commit has two parents"), run_time=1.0)
        self.play(GrowArrow(am4), GrowArrow(amf), run_time=1.0)
        self.wait(1.0)
        self.play(main.animate.move_to(slot(m, UP)), head.animate.move_to(slot(m, UP, 1)),
                  am4.animate.set_color(C_EDGE), amf.animate.set_color(C_EDGE), run_time=1.0)
        self.geo_track(merge_commit=m, merge_ring=m[0], merge_id=m[1], main_tag=main, head_tag=head)
        self.play(*self.caption_to("both histories kept, joined by one commit"), run_time=0.8)
        self.wait(1.5)
        self.m, self.am4, self.amf = m, am4, amf

    def beat_rebase(self):
        """Beats 8-10: rebase replays copies; fast-forward; the golden rule."""
        c3, c4, f1, f2 = self.c3, self.c4, self.f1, self.f2
        main, feat, head = self.main, self.feat, self.head
        self.geo_track(merge_commit=VGroup(), merge_ring=VGroup(), merge_id=VGroup())
        self.play(*self.title_to("4", "Rebase"), *self.cmd_to(None),
                  *self.caption_to("rewind: rebase instead, for a straight history"),
                  FadeOut(self.m), FadeOut(self.am4), FadeOut(self.amf),
                  main.animate.move_to(slot(c4, UP)), head.animate.move_to(slot(c4, UP, 1)), run_time=1.2)
        self.wait(1.0)
        self.play(*self.cmd_to("git switch feature"),
                  self.glide(head, slot(f2, DOWN, 1), v(2.5, 1.0), v(3.5, -0.5)), run_time=1.2)
        self.wait(0.8)
        self.play(*self.cmd_to("git rebase main"),
                  *self.caption_to("rebase replays your commits on top of main"), run_time=0.8)
        f1r = commit_node("2be", X["f1r"], FEAT_Y, C_FEAT)
        af1r = parent_arrow(f1r, c4)
        f2r = commit_node("6d7", X["f2r"], FEAT_Y, C_FEAT)
        af2r = parent_arrow(f2r, f1r)
        self.graph.add(f1r, f2r, af1r, af2r)
        hop1, hop2 = f1.copy(), f2.copy()          # still showing the old ids e5b, 9a0
        self.add(hop1, hop2)
        # .animate(path_arc<0) bends upward here (over the lane, away from the tags below)
        self.play(hop1.animate(path_arc=-0.55 * PI).move_to(f1r),
                  hop2.animate(path_arc=-0.55 * PI).move_to(f2r), run_time=1.5)
        old_ids = VGroup(hop1[1], hop2[1])
        self.remove(hop1, hop2)
        self.add(f1r[0], f2r[0], old_ids)           # same pixels: circles now belong to the copies
        self.play(GrowArrow(af1r), GrowArrow(af2r), run_time=0.7)
        self.play(feat.animate.move_to(slot(f2r, DOWN)), head.animate.move_to(slot(f2r, DOWN, 1)), run_time=1.0)
        ghosts = VGroup(f1, f2, self.af1, self.af2)
        new_ids = VGroup(f1r[1], f2r[1])
        self.play(ghosts.animate.set_opacity(0.25),
                  AnimationGroup(FadeOut(old_ids), FadeIn(new_ids), lag_ratio=1.0),
                  *self.caption_to("new copies, new ids: the originals are left behind"), run_time=1.2)
        self.remove(f1r[0], f2r[0], new_ids)
        self.add(f1r, f2r)
        self.geo_track(forked=self.graph)       # the full two-lane graph: centred left-right
        self.wait(2.3)

        # fast-forward: main has nothing new, so its label just slides
        # git switch main: HEAD hops (out downwards, in from above main). After the rebase the
        # graph is one connected barrier, so a glide would cross an arrow, or sweep around the
        # graph's right end into the frame margin.
        self.play(*self.cmd_to("git switch main"), FadeOut(head, shift=0.3 * DOWN), run_time=0.7)
        head.move_to(slot(c4, UP, 1))
        self.play(FadeIn(head, shift=0.3 * DOWN), run_time=0.7)
        self.play(*self.cmd_to("git merge feature"), run_time=0.6)
        self.play(self.glide(main, slot(f2r, UP), v(2.0, 0), v(0, 1.2)),
                  self.glide(head, slot(f2r, UP, 1), v(2.0, 0), v(0, 1.2)),
                  *self.caption_to("main just slides forward: a fast-forward"), run_time=1.4)
        self.wait(1.5)

        # straighten: one line of history
        self.geo_track(forked=VGroup())
        f1r_t = f1r.copy().move_to([X["f1s"], MAIN_Y, 0])
        f2r_t = f2r.copy().move_to([X["f2s"], MAIN_Y, 0])
        self.play(FadeOut(ghosts), f1r.animate.move_to(f1r_t), f2r.animate.move_to(f2r_t),
                  Transform(af1r, parent_arrow(f1r_t, c4)),
                  Transform(af2r, parent_arrow(f2r_t, f1r_t)),
                  main.animate.move_to(slot(f2r_t, UP)), head.animate.move_to(slot(f2r_t, UP, 1)),
                  feat.animate.move_to(slot(f2r_t, DOWN)),
                  *self.caption_to("one straight line of history"), run_time=1.8)
        self.geo_track(history=VGroup(self.c1, self.c2, c3, c4, f1r, f2r,
                                      self.a21, self.a32, self.a43, af1r, af2r))
        self.wait(1.5)
        self.play(*self.cmd_to(None),
                  *self.caption_to("rule: never rebase commits others already have", C_BAD), run_time=0.8)
        self.wait(2.5)

    def beat_conflict_cause(self):
        """Beat 11: both branches changed the same line."""
        self.clear_stage()
        base = code_card("before branching", "getUser(id)", C_MUTED).move_to([0, 1.3, 0])
        def cards(w=None):
            return (code_card("main", span("fetchUser", C_MAIN) + "(id)", C_MAIN, w).move_to([-3.4, -0.9, 0]),
                    code_card("feature", "getUser(id" + span(", cache", C_FEAT) + ")", C_FEAT, w)
                    .move_to([3.4, -0.9, 0]))
        mcard, fcard = cards()
        mcard, fcard = cards(max(mcard[1].width, fcard[1].width))
        mnote = Text("renamed the function", font_size=SMALL_SIZE, color=C_MUTED).next_to(mcard, DOWN, buff=0.2)
        fnote = Text("added caching", font_size=SMALL_SIZE, color=C_MUTED).next_to(fcard, DOWN, buff=0.2)
        d1 = DashedLine(base[1].get_bottom(), mcard[0].get_top(), buff=0.15, color=C_EDGE)
        d2 = DashedLine(base[1].get_bottom(), fcard[0].get_top(), buff=0.15, color=C_EDGE)
        self.play(*self.title_to("5", "Conflicts"), FadeIn(base, shift=0.2 * DOWN),
                  *self.caption_to("one line of app.py, before branching"), run_time=1.0)
        self.wait(1.0)
        self.play(Create(d1), FadeIn(mcard, shift=0.2 * DOWN), FadeIn(mnote), run_time=1.0)
        self.play(Create(d2), FadeIn(fcard, shift=0.2 * DOWN), FadeIn(fnote), run_time=1.0)
        self.geo_track(cards=VGroup(base, mcard, fcard, mnote, fnote, d1, d2))
        self.play(*self.caption_to("both branches changed the same line"), run_time=0.8)
        self.wait(1.5)
        self.cards = (base, mcard, fcard, mnote, fnote, d1, d2)

    def beat_conflict_resolve(self):
        """Beats 12-14: Git marks the conflict; a person decides; ours/theirs swap in a rebase."""
        base, mcard, fcard, mnote, fnote, d1, d2 = self.cards
        l_open = Text("<<<<<<< HEAD", font=MONO, font_size=CODE_SIZE, color=C_MUTED)
        l_ours = code_text(span("fetchUser", C_MAIN) + "(id)")
        l_mid = Text("=======", font=MONO, font_size=CODE_SIZE, color=C_MUTED)
        l_theirs = code_text("getUser(id" + span(", cache", C_FEAT) + ")")
        l_close = Text(">>>>>>> feature", font=MONO, font_size=CODE_SIZE, color=C_MUTED)
        body = VGroup(l_open, l_ours, l_mid, l_theirs, l_close)
        for i, line in enumerate(body):
            line.move_to(i * 0.5 * DOWN, aligned_edge=LEFT)
        body.set_z_index(2)
        fbox = RoundedRectangle(corner_radius=0.12, width=body.width + 0.7, height=body.height + 0.6,
                                stroke_color=C_BAD, stroke_width=4).set_fill(CARD_BG, opacity=1)
        fbox.move_to(body)
        fhead = Text("app.py", font=MONO, font_size=CODE_SIZE, color=C_MUTED)
        fhead.next_to(fbox, UP, buff=0.15, aligned_edge=LEFT)
        ftag = branch_tag("CONFLICT", C_BAD, font_size=SMALL_SIZE).next_to(fhead, RIGHT, buff=0.3)
        ours = VGroup(Text("ours", font_size=LABEL_SIZE, color=C_MAIN),
                      Text("(main)", font_size=SMALL_SIZE, color=C_MUTED)).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
        theirs = VGroup(Text("theirs", font_size=LABEL_SIZE, color=C_FEAT),
                        Text("(feature)", font_size=SMALL_SIZE, color=C_MUTED)).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
        ours.next_to(fbox, RIGHT, buff=0.3).match_y(l_ours)
        theirs.next_to(fbox, RIGHT, buff=0.3).match_y(l_theirs)
        conflict = VGroup(fbox, body, fhead, ftag, ours, theirs)
        conflict.move_to([0, 0.3, 0])

        self.play(*self.cmd_to("git merge feature"),
                  *self.caption_to("Git can't choose: it marks the conflict"),
                  FadeOut(base), FadeOut(d1), FadeOut(d2), FadeOut(mnote), FadeOut(fnote),
                  FadeOut(mcard[0]), FadeOut(fcard[0]),
                  ReplacementTransform(mcard[2], l_ours), ReplacementTransform(fcard[2], l_theirs),
                  ReplacementTransform(VGroup(mcard[1], fcard[1]), fbox), run_time=1.5)
        self.play(FadeIn(VGroup(l_open, l_mid, l_close)), FadeIn(fhead), FadeIn(ftag, scale=0.8), run_time=1.0)
        self.play(FadeIn(ours, shift=0.2 * LEFT), FadeIn(theirs, shift=0.2 * LEFT), run_time=0.8)
        self.wait(2.0)

        # three ways out
        specs = [
            ("keep ours", C_MAIN, "loses the caching", C_MUTED, span("fetchUser", C_MAIN) + "(id)"),
            ("keep theirs", C_FEAT, "loses the rename", C_MUTED, "getUser(id" + span(", cache", C_FEAT) + ")"),
            ("edit by hand", WHITE, "keeps both", C_GOOD,
             span("fetchUser", C_MAIN) + "(id" + span(", cache", C_FEAT) + ")"),
        ]
        codes = [code_text(s[4]).set_z_index(2) for s in specs]
        code_w = max(c.width for c in codes) + 0.5
        rows = VGroup()
        for (label, lcol, verdict, vcol, _), code in zip(specs, codes):
            head = VGroup(Text(label, font_size=LABEL_SIZE, color=lcol),
                          Text(verdict, font_size=SMALL_SIZE, color=vcol)).arrange(RIGHT, buff=0.3)
            box = RoundedRectangle(corner_radius=0.1, width=code_w, height=code.height + 0.3,
                                   stroke_color=DARK_GREY, stroke_width=2).set_fill(CARD_BG, opacity=1)
            code.move_to(box).align_to(box, LEFT).shift(0.25 * RIGHT)
            rows.add(VGroup(head, VGroup(box, code)).arrange(DOWN, buff=0.15, aligned_edge=LEFT))
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        check = check_mark().next_to(rows[2][0], RIGHT, buff=0.2)
        frame = SurroundingRectangle(VGroup(rows[2], check), color=C_GOOD, buff=0.15, corner_radius=0.1)
        options = VGroup(rows, check, frame)
        # the conflicted file on the left, the options on the right: one pair, centred
        gap = 0.6
        total = conflict.width + gap + options.width
        x_left = -total / 2
        self.play(conflict.animate.set_x(x_left + conflict.width / 2),
                  *self.caption_to("a person decides how to resolve it"), run_time=1.0)
        options.shift((x_left + conflict.width + gap - options.get_left()[0]) * RIGHT)
        options.shift((fhead.get_top()[1] - rows.get_top()[1]) * UP)
        for row in rows:
            self.play(FadeIn(row, shift=0.2 * LEFT), run_time=0.9)
            self.wait(1.2)
        self.play(Create(frame), FadeIn(check, scale=0.5), run_time=0.8)
        self.geo_track(options=VGroup(conflict, *rows, check, frame))
        self.wait(0.6)
        self.geo_track(options=VGroup())        # the file shrinks next: the pair is no longer balanced

        # the file is fixed: commit to finish the merge
        resolved = code_text(specs[2][4]).set_z_index(2)
        rbox = RoundedRectangle(corner_radius=0.12, width=resolved.width + 0.7, height=resolved.height + 0.7,
                                stroke_color=C_GOOD, stroke_width=4).set_fill(CARD_BG, opacity=1)
        rbox.align_to(fbox, UP).align_to(fbox, LEFT)
        resolved.move_to(rbox)
        rtag = branch_tag("resolved", C_GOOD, font_size=SMALL_SIZE).move_to(ftag, aligned_edge=LEFT)
        self.play(*self.swap(body, resolved), Transform(fbox, rbox),
                  *self.swap(ftag, rtag),
                  # labels gone within the first third, before the box edge reaches them
                  FadeOut(ours, rate_func=lambda t: min(1.0, 3 * t)),
                  FadeOut(theirs, rate_func=lambda t: min(1.0, 3 * t)),
                  *self.cmd_to("git add app.py && git commit"),
                  *self.caption_to("then commit: that finishes the merge"), run_time=1.2)
        self.wait(1.5)
        self.play(*self.caption_to("careful: in a rebase, ours and theirs swap", C_FOCUS), run_time=0.8)
        self.wait(2.5)

    def beat_protected_main(self):
        """Beat 15: main is protected; a direct push is rejected."""
        self.clear_stage()
        y = 0.9
        # p1..p3 on main, my commit 1.6 right of p3 on the lower lane with its tag below: choose
        # p1's x so that the finished picture reaches equally far left and right of the centre
        tag_w = branch_tag("feature", C_FEAT).width
        a = (R - 4.6 - tag_w / 2) / 2
        xs = (a, a + 1.5, a + 3.0)
        x_mine = a + 4.6
        p1, p2, p3 = (commit_node(c, x, y, C_MAIN) for c, x in zip(("b07", "5e1", "d92"), xs))
        e21, e32 = parent_arrow(p2, p1), parent_arrow(p3, p2)
        mtag = branch_tag("main", C_MAIN).move_to(slot(p3, UP))
        lock = padlock().next_to(mtag, RIGHT, buff=0.15)
        self.play(*self.title_to("6", "In a team"),
                  LaggedStart(FadeIn(p1), AnimationGroup(GrowArrow(e21), FadeIn(p2)),
                              AnimationGroup(GrowArrow(e32), FadeIn(p3)), FadeIn(mtag), lag_ratio=0.35),
                  run_time=1.6)
        self.play(FadeIn(lock, scale=0.5), *self.caption_to("main is protected: no direct pushes"), run_time=1.0)
        self.wait(1.0)
        mine = commit_node("4fa", x_mine + 1.2, -1.2, C_FEAT)
        self.play(FadeIn(mine, scale=0.6), *self.cmd_to("git push origin main"), run_time=0.8)
        self.play(mine.animate.move_to([x_mine, y, 0]), run_time=0.9)
        cross = cross_mark().move_to([(p3.get_right()[0] + x_mine - R) / 2, y, 0])
        self.play(FadeIn(cross, scale=1.5),
                  *self.caption_to("rejected: changes must be reviewed first", C_BAD), run_time=0.6)
        self.wait(0.8)
        self.play(mine.animate.move_to([x_mine, -1.2, 0]), FadeOut(cross), run_time=0.9)
        ftag = branch_tag("feature", C_FEAT).move_to(slot(mine, DOWN))
        emine = parent_arrow(mine, p3)
        self.play(FadeIn(ftag, shift=0.2 * UP), GrowArrow(emine), *self.cmd_to("git push origin feature"),
                  *self.caption_to("instead: push a branch, open a pull request"), run_time=1.0)
        self.geo_track(protected=VGroup(p1, p2, p3, e21, e32, mtag, lock, mine, ftag, emine))
        self.wait(1.2)

    def beat_pull_request(self):
        """Beat 16: a pull request passes automated tests and a review before it reaches main."""
        keep = [self.title]
        self.play(*[FadeOut(m) for m in self.mobjects if m not in keep], run_time=0.8)
        self.caption = self.cmd = None
        boxes = VGroup(*[flow_box(t, c, width=2.45) for t, c in (("pull request", C_FEAT), ("CI tests", C_MUTED),
                                                                ("review", C_MUTED), ("main", C_MAIN))])
        boxes.arrange(RIGHT, buff=0.6)
        boxes.move_to([0, 0.2, 0])
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.08, color=C_EDGE, stroke_width=3)
                          for a, b in zip(boxes, boxes[1:])])
        subs = VGroup(*[Text(s, font_size=SMALL_SIZE, color=C_MUTED).next_to(b, DOWN, buff=0.25)
                        for s, b in zip(["feature → main", "build + tests", "a teammate approves",
                                         "protected"], boxes)])
        self.geo_track(pipeline=VGroup(boxes, arrows, subs))
        self.play(LaggedStart(*[AnimationGroup(FadeIn(b, shift=0.2 * RIGHT), FadeIn(s))
                                for b, s in zip(boxes, subs)], lag_ratio=0.3),
                  LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3),
                  *self.caption_to("changes arrive through a pull request"), run_time=1.8)
        self.wait(1.0)
        token = Dot(radius=0.16, color=C_FEAT).move_to(boxes[0].get_top() + 0.4 * UP)
        self.play(FadeIn(token, scale=0.5), run_time=0.5)
        self.play(*self.caption_to("tests and a reviewer must approve it"), run_time=0.6)
        for box in boxes[1:3]:
            self.play(token.animate.move_to(box.get_top() + 0.4 * UP), run_time=0.9)
            chk = check_mark()
            row = VGroup(box[1].copy(), chk).arrange(RIGHT, buff=0.15).move_to(box[0])
            self.play(box[0].animate.set_stroke(C_GOOD).set_fill(C_GOOD, opacity=0.15),
                      box[1].animate.move_to(row[0]), FadeIn(chk.move_to(row[1]), scale=0.5), run_time=0.6)
            self.wait(0.4)
        self.play(token.animate.move_to(boxes[3].get_top() + 0.4 * UP),
                  *self.caption_to("only then is it merged into main"), run_time=0.9)
        self.play(Flash(boxes[3].get_top() + 0.4 * UP, color=C_FOCUS), run_time=0.8)
        self.wait(1.2)

    def beat_merge_policies(self):
        """Beat 17: how a PR lands on main is a team policy."""
        keep = [self.title]
        self.play(*[FadeOut(m) for m in self.mobjects if m not in keep], run_time=0.8)
        self.caption = self.cmd = None
        r = 0.2
        ym, yf = 0.1, -0.8

        def node(cx, dx, y, color, ghost=False):
            n = commit_node(None, cx + dx, y, color, radius=r)
            return n.set_opacity(0.25) if ghost else n

        def link(a, b, ghost=False, dashed=False):
            if dashed:
                return DashedLine(a.get_center(), b.get_center(), buff=r + 0.05, color=C_EDGE, stroke_width=2)
            e = arrow_between(a.get_center(), b.get_center(), radius=r, width=2.5, tip=0.12)
            return e.set_opacity(0.25) if ghost else e

        def column(cx, kind):
            m1, m2 = node(cx, -1.5, ym, C_MAIN), node(cx, -0.75, ym, C_MAIN)
            parts = [m1, m2, link(m2, m1)]
            if kind == "merge":
                f1, f2 = node(cx, -0.35, yf, C_FEAT), node(cx, 0.4, yf, C_FEAT)
                tip = node(cx, 1.05, ym, C_MAIN)
                parts += [f1, f2, tip, link(f1, m2), link(f2, f1), link(tip, m2), link(tip, f2)]
            elif kind == "squash":
                f1, f2 = node(cx, -0.35, yf, C_FEAT, True), node(cx, 0.4, yf, C_FEAT, True)
                tip = node(cx, 0.45, ym, C_FEAT)
                parts += [f1, f2, link(f1, m2, True), link(f2, f1, True), tip, link(tip, m2),
                          link(f2, tip, dashed=True)]
            else:
                f1, f2 = node(cx, 0.1, ym, C_FEAT), node(cx, 0.95, ym, C_FEAT)
                tip = f2
                parts += [f1, f2, link(f1, m2), link(f2, f1)]
            tag = branch_tag("main", C_MAIN, font_size=SMALL_SIZE)
            tag.next_to(tip, UP, buff=0.15)
            return VGroup(*parts, tag)

        names = [("merge commit", "merge", "keeps the real history"),
                 ("squash", "squash", "one commit per PR"),
                 ("rebase & merge", "rebase", "linear history")]
        cols = VGroup()
        for title, kind, trait in names:
            graph = column(0, kind)
            graph.shift(-graph.get_center()[0] * RIGHT)              # centred under its title
            head = Text(title, font_size=LABEL_SIZE).move_to([0, 1.45, 0])
            foot = Text(trait, font_size=SMALL_SIZE, color=C_MUTED).move_to([0, -1.65, 0])
            cols.add(VGroup(head, graph, foot))
        # the outer columns reach the same distance from the centre (8 % side margins), the
        # middle one sits on it: a symmetric row
        reach = config.frame_width / 2 - MARGIN_X
        cols[0].shift((-reach + cols[0].width / 2) * RIGHT)
        cols[2].shift((reach - cols[2].width / 2) * RIGHT)
        for (_, kind, _), col in zip(names, cols):
            self.geo_track(**{f"policy_{kind}": col[1]})
            self.geo_rule(symmetric(f"policy_{kind}", about=(col[0].get_x(), 0), axis="x"))
        self.play(*self.caption_to("the team picks how pull requests land on main"), run_time=0.8)
        for col in cols:
            self.play(FadeIn(col[0], shift=0.2 * DOWN), FadeIn(col[1]), run_time=1.0)
            self.play(FadeIn(col[2], shift=0.2 * UP), run_time=0.6)
            self.wait(0.8)
        self.geo_track(policies=cols)
        self.wait(1.5)

    def beat_recap(self):
        """Beat 18: tie the pieces together."""
        self.clear_stage()
        def g(s):
            return span(s, C_MUTED)

        items = ["commit: " + g("a snapshot pointing to its parent"),
                 "branch: " + g("a movable label"),
                 "merge " + g("joins,") + " rebase " + g("replays"),
                 "conflict: " + g("a person decides"),
                 "main: " + g("only via reviewed pull requests")]
        recap = VGroup(*[MarkupText(s, font_size=36) for s in items])
        self.geo_track(recap=recap)
        for i, line in enumerate(recap):   # ascender tops align; bounding boxes differ by descenders
            line.align_to(i * 0.85 * DOWN, UP).align_to(ORIGIN, LEFT)
        recap.move_to([0, -0.1, 0])
        self.play(*self.title_to(None, "Recap"), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in recap], lag_ratio=0.5), run_time=3.5)
        self.wait(3.0)
        self.play(FadeOut(recap), FadeOut(self.title), run_time=1.0)
