"""Inside a large language model: tokens become vectors that flow up a stack of blocks; in each
block attention lets tokens share information and an MLP of neurons transforms each token; every
connection is a learned weight, stored in matrices that add up to billions of numbers.

Real numbers are those of Llama 3 8B (d_model 4,096, 32 blocks, MLP width 14,336, 8.03 B params).

Render: "$SKILL_DIR/scripts/render.sh" preview scene.py Explainer
"""

import math

from manim import *

try:  # layout checker; on PYTHONPATH when rendered with render.sh
    from manim_qa import LayoutGuard
except ImportError:  # keeps the file renderable without the skill
    print("LAYOUT WARNING manim_qa not importable: layout checks are OFF", flush=True)

    class LayoutGuard:
        pass

# --- style (references/style-guide.md) -----------------------------------------------
BG = "#0F1117"
config.background_color = BG
config.max_files_cached = 1000   # keep every partial movie so frames.py --beats sees them all
Text.set_default(font="Noto Sans")
MarkupText.set_default(font="Noto Sans")

# --- colour legend: one colour per concept, used everywhere ---------------------------
C_POS = BLUE       # a positive number (vector entry or weight)
C_NEG = ORANGE     # a negative number
C_ATTN = PURPLE    # attention (shapes)
C_ATTN_T = PURPLE_A  # attention, for text and maths (PURPLE is too dark for thin glyphs)
C_MLP = TEAL       # MLP and its neurons
C_OUT = GREEN      # the prediction
C_HI = YELLOW      # look here now; a firing neuron
C_MUTED = GREY_B   # scaffolding, secondary text

TITLE_SIZE = 40
LABEL = 30
SMALL = 26
CAP = 28
NUM = 28

# --- layout constants -----------------------------------------------------------------
WORDS = ["The", "cat", "sat", "on", "the"]
LANE_X = [-5.3, -3.9, -2.5, -1.1, 0.3]           # stack chapter: one lane per token
STACK_MID_X = (LANE_X[0] + LANE_X[-1]) / 2
Y_CHIP, Y_VEC0, Y_VEC1, Y_VEC2 = -3.05, -2.15, 0.0, 2.15
Y_ATT = (-1.3, 0.8)
Y_MLP = (-0.8, 1.3)
PANEL_LEFT = 1.8                                  # right-hand panel: x 1.6 .. 6.4

ATT_X = [-4.4, -2.2, 0.0, 2.2, 4.4]              # attention chapter
ATT_VEC_Y = -0.6
SCORES = [-0.8, 0.6, 1.0, 1.1, -0.1]              # query . key for "the" against each token

X_IN = [0.8, -0.5, 0.3, 0.9, -0.2]                # "the" vector entering the MLP
X_QUIET = [-0.7, 0.6, -0.2, -0.9, 0.1]            # an input that does not match
W_IN = [0.9, -0.6, 0.1, 0.7, 0.4]                 # the neuron's input weights
W_OUT = [0.5, -0.3, 0.8, 0.2, -0.6]               # the neuron's output weights


def gelu(s):
    return 0.5 * s * (1 + math.erf(s / math.sqrt(2)))


def softmax_pct(scores):
    e = [math.exp(s) for s in scores]
    total = sum(e)
    return [round(100 * v / total) for v in e]


def dot(a, b):
    return float(sum(x * y for x, y in zip(a, b)))


# --- building blocks ------------------------------------------------------------------
def T(s, size=CAP, color=WHITE, **kw):
    return Text(s, font_size=size, color=color, **kw)


def sign_color(v):
    return C_POS if v >= 0 else C_NEG


def cell(v, w, h, max_op=0.85):
    return Rectangle(width=w, height=h, stroke_color=C_MUTED, stroke_width=1.5,
                     fill_color=sign_color(v), fill_opacity=0.08 + max_op * min(abs(v), 1.0))


def vector(vals, w=0.36, h=0.18, max_op=0.85):
    return VGroup(*[cell(v, w, h, max_op) for v in vals]).arrange(DOWN, buff=0)


def number(v, nd=1, size=NUM, color=WHITE):
    return DecimalNumber(v, num_decimal_places=nd, font_size=size, color=color)


def numbered_vector(vals, w=0.9, h=0.6, nd=1):
    cells = vector(vals, w, h, max_op=0.5)
    nums = VGroup(*[number(v, nd, 30).move_to(c) for v, c in zip(vals, cells)])
    return VGroup(cells, nums)


def chip(word, pos, size=28):
    box = RoundedRectangle(corner_radius=0.12, width=1.1, height=0.55, stroke_color=C_MUTED,
                           stroke_width=2, fill_color=WHITE, fill_opacity=0.06)
    return VGroup(box, Text(word, font_size=size).move_to(box)).move_to(pos)


def edge_to(p, centre, radius, w, max_w=7):
    """Line from point p to the rim of a circle at centre; colour = sign, width = |w|."""
    d = centre - p
    end = centre - radius * d / np.linalg.norm(d)
    return Line(p, end, color=sign_color(w), stroke_width=1 + max_w * min(abs(w), 1),
                stroke_opacity=0.35 + 0.6 * min(abs(w), 1))


def edge_from(centre, radius, p, w, max_w=7):
    d = p - centre
    start = centre + radius * d / np.linalg.norm(d)
    return Line(start, p, color=sign_color(w), stroke_width=1 + max_w * min(abs(w), 1),
                stroke_opacity=0.35 + 0.6 * min(abs(w), 1))


def grid(mat, w, h):
    return VGroup(*[VGroup(*[cell(v, w, h) for v in row]).arrange(RIGHT, buff=0) for row in mat]
                  ).arrange(DOWN, buff=0)


class Explainer(LayoutGuard, Scene):
    def construct(self):
        self.title = None
        self.cap = None
        rng = np.random.default_rng(11)
        self.table_vals = np.clip(rng.normal(0, 0.55, size=(8, 5)), -1, 1)
        self.rows_for = [1, 5, 3, 6, 2]
        self.vals0 = [self.table_vals[r] for r in self.rows_for]

        self.beat_hook()
        self.beat_tokens()
        self.beat_embedding()
        self.beat_stream()
        self.beat_block()
        self.beat_stack()
        self.beat_flow()
        self.beat_output()
        self.beat_attention()
        self.beat_query_key()
        self.beat_neuron()
        self.beat_matrix()
        self.beat_scale()
        self.beat_recap()

    # --- helpers ----------------------------------------------------------------------
    def swap_title(self, text):
        new = Text(text, font_size=TITLE_SIZE).to_edge(UP, buff=0.6)
        # keep the titles themselves (not just their ids): a freed title's id can be reused by a
        # new mobject, which clear_stage would then wrongly keep on stage
        self.__dict__.setdefault("titles", []).append(new)
        anims = [FadeIn(new, shift=0.15 * DOWN)]
        if self.title is not None:
            anims.append(FadeOut(self.title, shift=0.15 * UP))
        self.title = new
        return anims

    def swap_caption(self, *lines, panel=False):
        anims = []
        if self.cap is not None:
            anims.append(FadeOut(self.cap))
            self.cap = None
        if lines:
            g = VGroup(*lines)
            if panel:
                g.arrange(DOWN, buff=0.15, aligned_edge=LEFT).to_edge(DOWN, buff=0.6)
                g.shift((PANEL_LEFT - g.get_left()[0]) * RIGHT)
            else:
                g.arrange(DOWN, buff=0.15).to_edge(DOWN, buff=0.6)
            anims.append(FadeIn(g, shift=0.1 * UP))
            self.cap = g
        return anims

    def clear_stage(self, keep=()):
        keep_ids = {id(m) for m in list(keep) + self.__dict__.get("titles", [])}
        gone = [m for m in self.mobjects if id(m) not in keep_ids]
        self.cap = None if self.cap in gone else self.cap
        return [FadeOut(m) for m in gone]

    # --- beat 1 -----------------------------------------------------------------------
    def beat_hook(self):
        """A concrete picture: text goes in, the next word comes out."""
        words = VGroup(*[Text(w, font_size=40) for w in WORDS]).arrange(RIGHT, buff=0.22,
                                                                         aligned_edge=DOWN)
        box = RoundedRectangle(corner_radius=0.2, width=2.4, height=1.3, stroke_color=C_MUTED,
                               stroke_width=3, fill_color=GREY_E, fill_opacity=1)
        llm = VGroup(box, Text("LLM", font_size=40).move_to(box))
        q = Text("?", font_size=44, color=C_OUT)
        VGroup(words, llm, q).arrange(RIGHT, buff=1.3).move_to(0.3 * UP)
        a1 = Arrow(words.get_right(), llm.get_left(), buff=0.2, color=C_MUTED)
        a2 = Arrow(llm.get_right(), q.get_left(), buff=0.2, color=C_MUTED)
        mat = Text("mat", font_size=40, color=C_OUT).move_to(q).align_to(q, LEFT)

        self.play(*self.swap_title("Inside a large language model"))
        self.play(LaggedStart(*[FadeIn(w, shift=0.15 * UP) for w in words], lag_ratio=0.15),
                  run_time=1.2)
        self.play(GrowArrow(a1), FadeIn(llm), run_time=1)
        self.play(GrowArrow(a2), FadeIn(q), run_time=0.8)
        self.play(FadeTransform(q, mat), *self.swap_caption(T("it predicts the next token")))
        self.wait(1.5)
        self.play(Indicate(box, color=C_HI, scale_factor=1.05),
                  *self.swap_caption(T("What happens inside the box?")))
        self.wait(0.8)
        self.hook = (words, VGroup(llm, a1, a2, mat))

    # --- beat 2 -----------------------------------------------------------------------
    def beat_tokens(self):
        """Text becomes tokens."""
        words, rest = self.hook
        chips = [chip(w, [x, Y_CHIP, 0]) for w, x in zip(WORDS, LANE_X)]
        self.play(FadeOut(rest), *self.swap_title("Text becomes tokens"), *self.swap_caption(),
                  run_time=0.8)
        self.play(*[ReplacementTransform(w, c[1]) for w, c in zip(words, chips)],
                  *[Create(c[0]) for c in chips], run_time=1.5)
        self.play(*self.swap_caption(T("text is cut into tokens"),
                                     T("(words or word pieces)", SMALL, C_MUTED), panel=True))
        self.wait(1.2)
        self.chips = VGroup(*chips)

    # --- beat 3 -----------------------------------------------------------------------
    def beat_embedding(self):
        """Each token looks up its row in the embedding table: a vector."""
        table = grid(self.table_vals, 0.42, 0.3).move_to([4.0, 0.3, 0])
        t_lbl = T("embedding table", 28).next_to(table, UP, buff=0.25)
        t_sub = T("128,256 rows: one per token", SMALL, C_MUTED).next_to(table, DOWN, buff=0.2)
        self.play(*self.swap_title("Each token becomes a vector"), *self.swap_caption(),
                  LaggedStart(*[FadeIn(r) for r in table], lag_ratio=0.1), FadeIn(t_lbl),
                  FadeIn(t_sub), run_time=1.5)
        self.wait(0.5)
        self.vecs = []
        for i, (x, r) in enumerate(zip(LANE_X, self.rows_for)):
            target = vector(self.table_vals[r]).move_to([x, Y_VEC0, 0]).set_z_index(1)
            hl = SurroundingRectangle(table[r], color=C_HI, buff=0.03)
            src = table[r].copy().set_z_index(1)
            first = i == 0
            self.play(Create(hl), Indicate(self.chips[i], color=C_HI),
                      run_time=0.7 if first else 0.4)
            self.play(Transform(src, target), FadeOut(hl), run_time=1.4 if first else 0.8)
            self.vecs.append(src)
            if first:
                self.play(*self.swap_caption(T("a row becomes a vector"),
                                             T("4,096 numbers (5 drawn)", SMALL, C_MUTED),
                                             panel=True))
        self.wait(1)
        self.play(FadeOut(VGroup(table, t_lbl, t_sub)), run_time=0.8)

    # --- beat 4 -----------------------------------------------------------------------
    def beat_stream(self):
        """Each token's vector rides its own lane upward: the residual stream."""
        lanes = VGroup(*[Line([x, Y_VEC0 + 0.45, 0], [x, Y_VEC2 - 0.45, 0], color=C_MUTED,
                              stroke_width=3, stroke_opacity=0.5) for x in LANE_X])
        lanes.set_z_index(-2)
        self.play(*self.swap_title("The residual stream"),
                  LaggedStart(*[Create(l) for l in lanes], lag_ratio=0.15),
                  *self.swap_caption(T("each vector flows upward"),
                                     T("one lane per token", SMALL, C_MUTED), panel=True),
                  run_time=1.6)
        self.wait(1.2)
        self.lanes = lanes

    # --- beat 5 -----------------------------------------------------------------------
    def make_block(self, k, label):
        ya, ym = Y_ATT[k], Y_MLP[k]
        width = LANE_X[-1] - LANE_X[0] + 1.1
        band = RoundedRectangle(corner_radius=0.1, width=width, height=0.4, stroke_color=C_ATTN,
                                stroke_width=2, fill_color=C_ATTN, fill_opacity=0.3
                                ).move_to([STACK_MID_X, ya, 0])
        boxes = VGroup(*[RoundedRectangle(corner_radius=0.08, width=0.9, height=0.4,
                                          stroke_color=C_MLP, stroke_width=2, fill_color=C_MLP,
                                          fill_opacity=0.3).move_to([x, ym, 0]) for x in LANE_X])
        a_lbl = Text("attention", font_size=SMALL, color=C_ATTN_T).next_to(band, RIGHT, buff=0.25)
        m_lbl = Text("MLP", font_size=SMALL, color=C_MLP).next_to(boxes, RIGHT, buff=0.35)
        m_lbl.align_to(a_lbl, LEFT)
        brace = Brace(VGroup(band, boxes, a_lbl, m_lbl), RIGHT, buff=0.15, color=C_MUTED)
        b_lbl = Text(label, font_size=SMALL, color=C_MUTED).next_to(brace, RIGHT, buff=0.15)
        return VGroup(band, boxes, a_lbl, m_lbl, brace, b_lbl)

    def beat_block(self):
        """A block has two parts: attention works across tokens, the MLP on each token."""
        blk = self.make_block(0, "block 1")
        band, boxes, a_lbl, m_lbl, brace, b_lbl = blk
        l1 = Text("attention: across tokens", font_size=CAP, t2c={"attention:": C_ATTN_T})
        l2 = Text("MLP: one token at a time", font_size=CAP, t2c={"MLP:": C_MLP})
        cap = VGroup(l1, l2).arrange(DOWN, buff=0.15, aligned_edge=LEFT).to_edge(DOWN, buff=0.6)
        cap.shift((PANEL_LEFT - cap.get_left()[0]) * RIGHT)

        self.play(*self.swap_title("Inside each block"), *self.swap_caption(),
                  FadeIn(band), FadeIn(a_lbl), FadeIn(l1), run_time=1.2)
        sweep = Line(band.get_left(), band.get_right()).set_stroke(C_HI, width=6)
        self.play(ShowPassingFlash(sweep, time_width=0.5), run_time=1.2)
        self.wait(0.5)
        self.play(LaggedStart(*[FadeIn(b, shift=0.1 * UP) for b in boxes], lag_ratio=0.15),
                  FadeIn(m_lbl), FadeIn(l2), run_time=1.2)
        self.play(LaggedStart(*[Indicate(b, color=C_HI, scale_factor=1.1) for b in boxes],
                              lag_ratio=0.15), run_time=1.2)
        self.play(GrowFromCenter(brace), FadeIn(b_lbl), run_time=0.8)
        self.wait(1.2)
        self.add(cap)  # the lines were faded in one by one; make the group the stage object
        self.cap = cap
        self.blk1 = blk

    # --- beat 6 -----------------------------------------------------------------------
    def beat_stack(self):
        """The model is a stack of 32 such blocks."""
        blk2 = self.make_block(1, "block 32")
        dots = MathTex(r"\vdots", color=C_MUTED).move_to(
            [self.blk1[2].get_center()[0], (Y_MLP[0] + Y_ATT[1]) / 2, 0])
        self.play(*self.swap_title("A stack of 32 blocks"),
                  TransformFromCopy(VGroup(*self.blk1[:5]), VGroup(*blk2[:5])),
                  FadeIn(blk2[5], shift=0.3 * UP), run_time=1.5)
        self.play(FadeIn(dots),
                  *self.swap_caption(T("32 blocks in an 8B model"),
                                     T("same layout, own numbers", SMALL, C_MUTED), panel=True))
        self.wait(1.2)
        self.blk2 = blk2
        self.dots = dots

    # --- beat 7 -----------------------------------------------------------------------
    def beat_flow(self):
        """Vectors rise through the blocks; each block adds an update."""
        rng = np.random.default_rng(5)
        vals1 = [np.clip(v + rng.normal(0, 0.45, 5), -1, 1) for v in self.vals0]
        vals2 = [np.clip(v + rng.normal(0, 0.45, 5), -1, 1) for v in vals1]
        self.play(*self.swap_title("Each block updates the vectors"),
                  *self.swap_caption(T("each block adds an update"),
                                     T("to every token's vector", SMALL, C_MUTED), panel=True))
        for vals, y, blk in ((vals1, Y_VEC1, self.blk1), (vals2, Y_VEC2, self.blk2)):
            targets = [vector(v).move_to([x, y, 0]).set_z_index(1) for v, x in zip(vals, LANE_X)]
            self.play(*[Transform(v, t) for v, t in zip(self.vecs, targets)],
                      Succession(Indicate(blk[0], color=C_HI, scale_factor=1.0),
                                 Indicate(blk[1], color=C_HI, scale_factor=1.0)),
                      run_time=2.4)
            self.wait(0.4)
        self.wait(0.8)
        self.vals2 = vals2

    # --- beat 8 -----------------------------------------------------------------------
    def beat_output(self):
        """The last token's final vector scores every possible next token."""
        top = self.vecs[4]
        names = ["mat", "floor", "bed"]
        lengths = [2.3, 1.1, 0.5]
        rows = VGroup()
        for i, (n, L) in enumerate(zip(names, lengths)):
            y = Y_VEC2 + 0.45 - 0.4 * i          # keeps "bed" clear of the block-32 brace below
            word = Text(n, font_size=CAP, color=C_OUT if i == 0 else WHITE)
            word.move_to([3.5, y, 0]).align_to([3.5, 0, 0], RIGHT)
            bar = Rectangle(width=L, height=0.28, stroke_width=0, fill_color=C_OUT,
                            fill_opacity=0.85 if i == 0 else 0.45)
            bar.move_to([3.65, y, 0]).align_to([3.65, 0, 0], LEFT)
            rows.add(VGroup(word, bar))
        brace = Brace(rows, LEFT, buff=0.12, color=C_MUTED)
        arrow = Arrow(top.get_right(), brace.get_tip(), buff=0.12, color=C_OUT)
        self.play(*self.swap_title("Predicting the next token"), GrowArrow(arrow),
                  GrowFromCenter(brace), run_time=1)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(r[0]), GrowFromEdge(r[1], LEFT))
                                for r in rows], lag_ratio=0.3),
                  *self.swap_caption(T("the last vector scores"),
                                     T("every possible next token", SMALL, C_MUTED), panel=True),
                  run_time=1.6)
        self.play(Indicate(rows[0], color=C_HI), run_time=1)
        self.wait(1.5)
        self.out_rows = rows

    # --- beat 9 -----------------------------------------------------------------------
    def beat_attention(self):
        """Attention: 'the' pulls information from earlier tokens, more from some than others."""
        self.play(*self.swap_title("Zoom in: attention"),
                  Circumscribe(self.blk1[0], color=C_HI), run_time=1.4)
        self.play(*self.clear_stage(), run_time=0.8)

        chips = VGroup(*[chip(w, [x, ATT_VEC_Y - 1.25, 0]) for w, x in zip(WORDS, ATT_X)])
        vecs = VGroup(*[vector(v, 0.5, 0.3).move_to([x, ATT_VEC_Y, 0])
                        for v, x in zip(self.vals0, ATT_X)])
        self.play(LaggedStart(*[FadeIn(VGroup(c, v), shift=0.2 * UP) for c, v in zip(chips, vecs)],
                              lag_ratio=0.12), run_time=1.4)

        pct = softmax_pct(SCORES)
        top_y = vecs[0].get_top()[1] + 0.08
        end = np.array([ATT_X[4], top_y, 0])
        arcs = VGroup(*[ArcBetweenPoints(np.array([x, top_y, 0]), end, angle=-PI / 3,
                                         color=C_ATTN, stroke_width=1 + 0.22 * p)
                        for x, p in zip(ATT_X[:4], pct[:4])])
        pct_lbls = VGroup(*[MathTex(rf"{p}\%", font_size=34, color=C_ATTN_T) for p in pct])
        for i, lbl in enumerate(pct_lbls):
            dx = -0.62 if i < 4 else 0.7
            lbl.move_to([ATT_X[i] + dx, top_y + 0.27, 0])
        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.2),
                  *self.swap_caption(Text("“the” pulls in information (values) from earlier tokens",
                                          font_size=CAP)),
                  run_time=1.6)
        self.play(LaggedStart(*[FadeIn(l, scale=0.8) for l in pct_lbls], lag_ratio=0.15),
                  run_time=1.2)
        self.wait(0.6)
        dots_ = [Dot(a.get_start(), radius=0.09, color=PURPLE_A) for a in arcs]
        self.play(LaggedStart(*[MoveAlongPath(d, a) for d, a in zip(dots_, arcs)], lag_ratio=0.15),
                  run_time=1.8)
        new_the = vector(X_IN, 0.5, 0.3).move_to(vecs[4])
        self.play(*[FadeOut(d) for d in dots_], Transform(vecs[4], new_the),
                  Indicate(chips[4], color=C_HI), run_time=1)
        self.play(*self.swap_caption(
            Text("“the” pulls in information (values) from earlier tokens", font_size=CAP),
            T("every token does this, looking only backwards", SMALL, C_MUTED)))
        self.wait(1.5)
        self.att = dict(chips=chips, vecs=vecs, arcs=arcs, pct=pct_lbls, top_y=top_y)

    # --- beat 10 ----------------------------------------------------------------------
    def beat_query_key(self):
        """How much to look is a match score: query . key, turned into shares."""
        a = self.att
        top_y = a["top_y"]

        def qk_chip(sym, pos, strong=False):
            box = RoundedRectangle(corner_radius=0.08, width=0.45, height=0.45,
                                   stroke_color=C_ATTN, stroke_width=2.5, fill_color=C_ATTN,
                                   fill_opacity=0.6 if strong else 0.15)
            return VGroup(box, MathTex(sym, font_size=32).move_to(box)).move_to(pos)

        keys = VGroup(*[qk_chip("k", [x, top_y + 0.3, 0]) for x in ATT_X])
        query = qk_chip("q", [ATT_X[4], top_y + 1.45, 0], strong=True)
        cap1 = Text("“the” sends a query; every token shows a key", font_size=CAP,
                    t2c={"query": C_ATTN_T, "key": C_ATTN_T})
        self.play(*self.swap_title("Who to look at: query and key"),
                  FadeOut(a["arcs"]), FadeOut(a["pct"]), run_time=1)
        self.play(FadeIn(query, scale=0.7), *self.swap_caption(cap1), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(k, scale=0.7) for k in keys], lag_ratio=0.12), run_time=1.2)
        self.wait(1)

        ghosts = VGroup(*[query.copy().set_opacity(0.85) for _ in keys])
        scores = VGroup(*[number(s, 1, 34) for s in SCORES])
        for i, s in enumerate(scores):
            dx = -0.68 if i < 4 else 0.72
            s.move_to([ATT_X[i] + dx, top_y + 0.3, 0])
        cap2 = Text("query · key = match score", font_size=CAP,
                    t2c={"query": C_ATTN_T, "key": C_ATTN_T})
        self.add(ghosts)
        self.remove(query)
        self.add(query)  # keep the real query on top of its copies
        self.play(LaggedStart(*[g.animate.next_to(k, UP, buff=0.1) for g, k in zip(ghosts, keys)],
                              lag_ratio=0.15),
                  *self.swap_caption(cap2), run_time=1.6)
        self.play(LaggedStart(*[FadeIn(s, shift=0.1 * UP) for s in scores], lag_ratio=0.12),
                  run_time=1.2)
        self.wait(1)

        pct = softmax_pct(SCORES)
        pct_lbls = VGroup(*[MathTex(rf"{p}\%", font_size=34, color=C_ATTN_T).move_to(s)
                            for p, s in zip(pct, scores)])
        self.play(*[FadeTransform(s, p) for s, p in zip(scores, pct_lbls)], FadeOut(ghosts),
                  *self.swap_caption(T("scores become shares that add up to 100%")),
                  run_time=1.2)
        self.wait(1.5)

        rng = np.random.default_rng(8)
        mats = VGroup()
        for name, role in (("Q", "query"), ("K", "key"), ("V", "value"), ("O", "output")):
            g = grid(np.clip(rng.normal(0, 0.6, (4, 4)), -1, 1), 0.2, 0.2)
            lbl = MathTex(rf"W_{name}", font_size=38, color=C_ATTN_T).next_to(g, DOWN, buff=0.12)
            r = T(role, 24, C_MUTED).next_to(lbl, DOWN, buff=0.08)
            mats.add(VGroup(g, lbl, r))
        mats.arrange(RIGHT, buff=0.6, aligned_edge=UP).move_to([-2.6, 1.85, 0])
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * DOWN) for m in mats], lag_ratio=0.2),
                  *self.swap_caption(
                      Text("query, key, value: each made by a weight matrix", font_size=CAP,
                           t2c={"weight matrix": C_ATTN_T}),
                      T("32 heads do this in parallel", SMALL, C_MUTED)),
                  run_time=1.6)
        self.wait(2)
        self.the_vec = a["vecs"][4]

    # --- beat 11 ----------------------------------------------------------------------
    def beat_neuron(self):
        """One MLP neuron: weighted sum, a bend, then it writes a pattern back."""
        the_vec = self.the_vec
        xin = numbered_vector(X_IN).move_to([-5.0, 0, 0])
        x_lbl = T("“the” vector", SMALL, C_MUTED).next_to(xin, DOWN, buff=0.25)
        self.add(the_vec)  # split it out of its (chip, vector) group so it can stay
        self.play(*self.swap_title("Zoom in: one MLP neuron"),
                  *self.clear_stage(keep=[the_vec]), run_time=0.8)
        self.play(ReplacementTransform(the_vec, xin[0]), run_time=1.2)
        self.play(FadeIn(xin[1]), FadeIn(x_lbl), run_time=0.6)

        N = np.array([-0.8, 0.0, 0.0])
        R = 0.45
        s = ValueTracker(0.0)
        neuron = Circle(radius=R, stroke_color=C_MLP, stroke_width=5, fill_color=C_HI,
                        fill_opacity=0).move_to(N)
        n_lbl = T("neuron", LABEL, C_MLP).next_to(neuron, UP, buff=0.2)
        edges = VGroup(*[edge_to(c.get_right(), N, R, w) for c, w in zip(xin[0], W_IN)])
        edges.set_z_index(-1)
        w_lbls = VGroup()
        for e, w in zip(edges, W_IN):
            n = number(w, 1, 30, sign_color(w))
            n.add_background_rectangle(color=BG, opacity=1, buff=0.04)
            w_lbls.add(n.move_to(e.point_from_proportion(0.33)))
        self.play(Create(neuron), FadeIn(n_lbl), run_time=0.8)
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(l) for l in w_lbls], lag_ratio=0.12),
                  *self.swap_caption(T("each connection is a weight: one learned number")),
                  run_time=1.6)
        self.wait(1.5)

        sum_num = number(0, 2, 34)
        out_num = number(0, 2, 34, C_HI)
        sum_row = VGroup(T("sum", SMALL, C_MUTED), sum_num).arrange(RIGHT, buff=0.2)
        out_row = VGroup(T("out", SMALL, C_MUTED), out_num).arrange(RIGHT, buff=0.2)
        readout = VGroup(sum_row, out_row).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        readout.next_to(neuron, DOWN, buff=0.4)
        sum_num.add_updater(lambda m: m.set_value(s.get_value()))
        out_num.add_updater(lambda m: m.set_value(gelu(s.get_value())))
        neuron.add_updater(lambda m: m.set_fill(
            C_HI, opacity=0.85 * float(np.clip(gelu(s.get_value()) / 1.6, 0, 1))))
        self.play(FadeIn(sum_row), run_time=0.5)
        flashes = [ShowPassingFlash(e.copy().set_stroke(C_HI, width=6, opacity=1), time_width=0.5)
                   for e in edges]
        s_fire = dot(X_IN, W_IN)
        self.play(LaggedStart(*flashes, lag_ratio=0.1), s.animate.set_value(s_fire),
                  *self.swap_caption(T("multiply each input by its weight, then add up")),
                  run_time=2)
        self.wait(1)

        axes = Axes(x_range=[-3, 3, 1], y_range=[-0.5, 2.5, 1], x_length=3.6, y_length=2.4,
                    tips=False, axis_config={"color": C_MUTED, "stroke_width": 2}
                    ).move_to([3.6, 0.1, 0])
        curve = axes.plot(gelu, x_range=[-3, 2.5], color=C_MLP, stroke_width=4)
        a_title = T("activation", SMALL, C_MLP).next_to(axes, UP, buff=0.2).align_to(axes, LEFT)
        x_name = T("sum", 24, C_MUTED).next_to(axes.x_axis.get_right(), RIGHT, buff=0.12)
        y_name = T("out", 24, C_MUTED).next_to(axes.y_axis.get_top(), RIGHT, buff=0.12)
        foot = T("Llama-style MLPs: gated (SwiGLU)", 24, C_MUTED)
        foot.next_to(axes, DOWN, buff=0.35)

        def marker():
            v = s.get_value()
            p0, p1 = axes.c2p(v, 0), axes.c2p(v, gelu(v))
            return VGroup(Line(p0, p1 + 1e-4 * UP, color=C_HI, stroke_width=2, stroke_opacity=0.7),
                          Dot(p0, radius=0.06, color=C_MUTED), Dot(p1, radius=0.09, color=C_HI))

        mark = always_redraw(marker)
        plot = VGroup(axes, curve, a_title, x_name, y_name)
        self.play(Create(axes), Create(curve), FadeIn(a_title), FadeIn(x_name), FadeIn(y_name),
                  FadeIn(foot), run_time=1.5)
        mark0 = marker()
        self.play(FadeIn(mark0), FadeIn(out_row),
                  *self.swap_caption(T("then a bend: the activation function")), run_time=1)
        self.remove(mark0)
        self.add(mark)
        self.wait(1.5)

        def set_input(vals):
            old = xin[1]
            new = VGroup(*[number(v, 1, 30).move_to(c) for v, c in zip(vals, xin[0])])
            anims = [c.animate.set_fill(sign_color(v), opacity=0.08 + 0.5 * min(abs(v), 1))
                     for c, v in zip(xin[0], vals)]
            anims += [FadeOut(old), FadeIn(new)]
            xin.submobjects[1] = new
            return anims

        s_quiet = dot(X_QUIET, W_IN)
        self.play(*set_input(X_QUIET), *self.swap_caption(T("a different input...")), run_time=1)
        self.play(s.animate.set_value(s_quiet),
                  *self.swap_caption(T("negative sum: out ≈ 0, the neuron stays quiet")),
                  run_time=1.6)
        self.wait(1.5)
        self.play(*set_input(X_IN), run_time=1)
        self.play(s.animate.set_value(s_fire),
                  *self.swap_caption(T("it fires when the input matches its weights")),
                  run_time=1.5)
        self.wait(1.5)

        mark.clear_updaters()
        self.play(FadeOut(plot), FadeOut(mark), FadeOut(foot), run_time=0.8)
        out_vals = [gelu(s_fire) * d for d in W_OUT]
        yout = numbered_vector(out_vals, nd=2).move_to([3.4, 0, 0])
        y_lbl = T("update to “the”", SMALL, C_MUTED).next_to(yout, DOWN, buff=0.25)
        edges_out = VGroup(*[edge_from(N, R, c.get_left(), d) for c, d in zip(yout[0], W_OUT)])
        edges_out.set_z_index(-1)
        d_lbls = VGroup()
        for e, d in zip(edges_out, W_OUT):
            n = number(d, 1, 30, sign_color(d))
            n.add_background_rectangle(color=BG, opacity=1, buff=0.04)
            d_lbls.add(n.move_to(e.point_from_proportion(0.67)))
        self.play(LaggedStart(*[Create(e) for e in edges_out], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(l) for l in d_lbls], lag_ratio=0.12),
                  *self.swap_caption(T("its output weights write a pattern back")),
                  run_time=1.6)
        self.play(FadeIn(yout), FadeIn(y_lbl), run_time=1)
        self.wait(1.2)
        cap_a = Text("input weights: the pattern it detects", font_size=CAP,
                     t2c={"input weights:": C_MLP})
        cap_b = Text("output weights: what it writes back", font_size=CAP,
                     t2c={"output weights:": C_MLP})
        self.play(*self.swap_caption(cap_a, cap_b), run_time=1)
        self.wait(2)
        for m in (sum_num, out_num, neuron):
            m.clear_updaters()

    # --- beat 12 ----------------------------------------------------------------------
    def beat_matrix(self):
        """Many neurons: their input weights stack into a matrix (and output weights into another)."""
        rng = np.random.default_rng(21)
        W = np.array([W_IN,                          # sum 1.60: fires
                      [0.5, -0.3, 0.6, 0.2, -0.4],   # sum 0.99: fires a little
                      [-0.6, 0.4, 0.2, -0.5, 0.3],   # sum -1.13: quiet
                      [0.3, 0.2, -0.7, 0.6, 0.5],    # sum 0.37: faint
                      [0.9, 0.1, 0.4, 0.8, -0.6],    # sum 1.63: fires
                      [-0.2, 0.7, -0.4, -0.3, 0.6]]) # sum -1.02: quiet
        Wd = np.clip(rng.normal(0, 0.6, (5, 6)), -1, 1)
        Wd[:, 0] = W_OUT

        self.play(*self.swap_title("Many neurons = a weight matrix"), *self.clear_stage(),
                  run_time=0.8)
        xv = vector(X_IN, 0.6, 0.5).move_to([-5.2, 0, 0])
        ny = [1.5 - 0.6 * k for k in range(6)]
        neurons = VGroup(*[Circle(radius=0.22, stroke_color=C_MLP, stroke_width=3,
                                  fill_color=C_HI, fill_opacity=0).move_to([-2.4, y, 0])
                           for y in ny])
        edges = VGroup(*[VGroup(*[edge_to(c.get_right(), n.get_center(), 0.22, W[k][j], max_w=4)
                                  for j, c in enumerate(xv)]) for k, n in enumerate(neurons)])
        edges.set_z_index(-1)
        self.play(FadeIn(xv), LaggedStart(*[FadeIn(n, scale=0.6) for n in neurons], lag_ratio=0.1),
                  run_time=1)
        self.play(LaggedStart(*[Create(g) for g in edges], lag_ratio=0.15),
                  *self.swap_caption(T("an MLP has many neurons, each with its own weights")),
                  run_time=1.8)
        self.wait(1)

        up = grid(W, 0.5, 0.6).move_to([1.25, 0, 0])
        up_lbl = MathTex(r"W_{\text{up}}", font_size=40, color=C_MLP).next_to(up, UP, buff=0.2)
        self.play(*[g.animate.set_stroke(opacity=0.12) for g in edges[1:]],
                  Indicate(neurons[0], color=C_HI), run_time=0.8)
        self.play(TransformFromCopy(edges[0], up[0]),
                  *self.swap_caption(T("row 1 = neuron 1's input weights")), run_time=1.4)
        self.wait(0.8)
        self.play(LaggedStart(*[TransformFromCopy(edges[k], up[k]) for k in range(1, 6)],
                              lag_ratio=0.15),
                  *[edges[k].animate.set_stroke(opacity=0.5) for k in range(1, 6)],
                  FadeIn(up_lbl), *self.swap_caption(T("one row per neuron: a matrix")),
                  run_time=2)
        self.wait(1)

        xrow = vector(X_IN, 0.5, 0.3).arrange(RIGHT, buff=0).next_to(up, DOWN, buff=0.3)
        x_tag = MathTex("x", font_size=36).next_to(xrow, LEFT, buff=0.2)
        self.play(TransformFromCopy(xv, xrow), FadeIn(x_tag), run_time=1.2)
        hl = SurroundingRectangle(up[0], color=C_HI, buff=0.04)
        self.play(Create(hl), *self.swap_caption(T("matrix × vector: every neuron's sum at once")),
                  run_time=0.6)
        for k in range(6):
            act = float(np.clip(gelu(dot(W[k], X_IN)) / 1.6, 0, 1))
            move = [hl.animate.move_to(up[k])] if k else []
            self.play(*move, neurons[k].animate.set_fill(C_HI, opacity=0.85 * act), run_time=0.45)
        self.play(FadeOut(hl), *self.swap_caption(T("some neurons fire, others stay quiet")),
                  run_time=0.6)
        self.wait(1)
        self.play(FadeOut(xrow), FadeOut(x_tag), run_time=0.6)

        down = grid(Wd, 0.4, 0.5).move_to([4.9, 0, 0])
        down_lbl = MathTex(r"W_{\text{down}}", font_size=40, color=C_MLP
                           ).next_to(down, UP, buff=0.2)
        down_lbl.align_to(up_lbl, DOWN)
        col = SurroundingRectangle(VGroup(*[row[0] for row in down]), color=C_HI, buff=0.04)
        self.play(FadeIn(down, shift=0.2 * LEFT), FadeIn(down_lbl),
                  *self.swap_caption(T("output weights form a second matrix")), run_time=1.2)
        self.play(Create(col), *self.swap_caption(T("column 1 = neuron 1's output weights")),
                  run_time=0.8)
        self.wait(1.2)
        up_size = T("14,336 × 4,096", SMALL, C_MUTED).next_to(up, DOWN, buff=0.25)
        down_size = T("4,096 × 14,336", SMALL, C_MUTED).next_to(down, DOWN, buff=0.25)
        down_size.align_to(up_size, UP)
        self.play(FadeOut(col), FadeIn(up_size), FadeIn(down_size),
                  *self.swap_caption(T("real size: 14,336 neurons in every block"),
                                     T("(Llama-style MLPs add a third, gate matrix)", 24, C_MUTED)),
                  run_time=1.2)
        self.wait(2)

    # --- beat 13 ----------------------------------------------------------------------
    def beat_scale(self):
        """Count the weights: one block to scale, then the whole model."""
        u = 0.85  # scene units per 4,096 rows or columns
        specs = [("Q", u, u, C_ATTN), ("K", u, u / 4, C_ATTN), ("V", u, u / 4, C_ATTN),
                 ("O", u, u, C_ATTN), (r"\text{gate}", u, 3.5 * u, C_MLP),
                 (r"\text{up}", u, 3.5 * u, C_MLP), (r"\text{down}", 3.5 * u, u, C_MLP)]
        rects = VGroup(*[Rectangle(width=w, height=h, stroke_color=c, stroke_width=2,
                                   fill_color=c, fill_opacity=0.35) for _, w, h, c in specs])
        rects.arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        rects[4:].shift(0.4 * RIGHT)
        rects.move_to([0, 0, 0]).align_to([0, -0.9, 0], DOWN)
        lbls = VGroup(*[MathTex(rf"W_{{{n}}}", font_size=36,
                                color=C_ATTN_T if c == C_ATTN else c).next_to(r, DOWN, buff=0.15)
                        for (n, _, _, c), r in zip(specs, rects)])
        for l in lbls:
            l.align_to(lbls[0], UP)
        att_brace = Brace(VGroup(rects[:4], lbls[:4]), DOWN, color=C_MUTED)
        mlp_brace = Brace(VGroup(rects[4:], lbls[4:]), DOWN, color=C_MUTED)
        att_txt = Text("attention: 42 M", font_size=CAP, t2c={"attention:": C_ATTN_T}
                       ).next_to(att_brace, DOWN, buff=0.12)
        mlp_txt = Text("MLP: 176 M", font_size=CAP, t2c={"MLP:": C_MLP}
                       ).next_to(mlp_brace, DOWN, buff=0.12)

        self.play(*self.swap_title("Counting the weights (Llama 3 8B)"), *self.clear_stage(),
                  run_time=0.8)
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(r, DOWN), FadeIn(l))
                                for r, l in zip(rects, lbls)], lag_ratio=0.15), run_time=2.2)
        self.play(GrowFromCenter(att_brace), FadeIn(att_txt), GrowFromCenter(mlp_brace),
                  FadeIn(mlp_txt),
                  *self.swap_caption(T("one block ≈ 218 million weights"),
                                     T("(drawn to scale: area = number of weights)", SMALL, C_MUTED)),
                  run_time=1.2)
        self.wait(2)

        total_w = 11.0
        parts = [("MLP", 5.64, C_MLP), ("attention", 1.34, C_ATTN), ("embedding tables", 1.05, C_MUTED)]
        tot = sum(p[1] for p in parts)
        segs = VGroup(*[Rectangle(width=total_w * v / tot, height=0.7, stroke_color=c,
                                  stroke_width=2, fill_color=c, fill_opacity=0.4)
                        for _, v, c in parts]).arrange(RIGHT, buff=0).move_to([0, 0.1, 0])
        seg_lbls = VGroup(
            Text("MLP  5.6 B", font_size=CAP).move_to(segs[0]),
            Text("attention  1.3 B", font_size=CAP, color=C_ATTN_T).next_to(segs[1], UP, buff=0.2),
            Text("embedding tables  1.1 B", font_size=CAP, color=C_MUTED
                 ).next_to(segs[2], DOWN, buff=0.2).align_to(segs, RIGHT),
        )
        big = Text("≈ 8.0 billion weights", font_size=48).move_to([0, 1.8, 0])
        self.play(*self.clear_stage(), run_time=0.8)
        self.play(FadeIn(big, shift=0.2 * DOWN), run_time=1)
        self.play(LaggedStart(*[GrowFromEdge(sg, LEFT) for sg in segs], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(l) for l in seg_lbls], lag_ratio=0.3),
                  *self.swap_caption(T("32 blocks + the embedding tables"),
                                     T("all set by training, none written by hand", SMALL, C_MUTED)),
                  run_time=2)
        self.wait(2)

    # --- beat 14 ----------------------------------------------------------------------
    def beat_recap(self):
        """Tie the pieces together."""
        icon_vec = vector([0.8, -0.5, 0.3, 0.9, -0.2], 0.22, 0.12)
        icon_arc = VGroup(Dot(LEFT * 0.35, radius=0.06, color=C_ATTN),
                          Dot(RIGHT * 0.35, radius=0.06, color=C_ATTN),
                          ArcBetweenPoints(LEFT * 0.35, RIGHT * 0.35, angle=-PI / 2,
                                           color=C_ATTN, stroke_width=4))
        n_c = Circle(radius=0.16, stroke_color=C_MLP, stroke_width=3, fill_color=C_HI,
                     fill_opacity=0.6)
        icon_neuron = VGroup(*[Line(np.array([-0.45, y, 0]), n_c.get_left(), color=C_POS,
                                    stroke_width=2) for y in (-0.2, 0, 0.2)], n_c)
        icon_grid = grid(np.array([[0.8, -0.4, 0.2], [-0.6, 0.9, 0.3], [0.1, -0.7, 0.5]]), 0.17, 0.17)
        rows = [
            (icon_vec, Text("tokens become vectors on a residual stream", font_size=32)),
            (icon_arc, Text("attention: tokens share information", font_size=32,
                            t2c={"attention:": C_ATTN_T})),
            (icon_neuron, Text("MLP neurons: detect a pattern, write one back", font_size=32,
                               t2c={"MLP neurons:": C_MLP})),
            (icon_grid, Text("weights: matrices of learned numbers, 8 B", font_size=32)),
        ]
        lines = VGroup()
        for icon, txt in rows:
            icon_box = VGroup(icon).scale_to_fit_height(min(icon.height, 0.6))
            slot = Rectangle(width=1.0, height=0.7, stroke_width=0).add(icon_box.move_to(ORIGIN))
            lines.add(VGroup(slot, txt).arrange(RIGHT, buff=0.3))
        lines.arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([0, -0.1, 0])
        self.play(*self.swap_title("Recap"), *self.clear_stage(), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(l, shift=0.2 * RIGHT) for l in lines], lag_ratio=0.5),
                  run_time=3)
        self.wait(2.5)
        self.play(*self.clear_stage(), FadeOut(self.title), run_time=1)
        self.title = None
