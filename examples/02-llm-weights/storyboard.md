# Storyboard: Inside a large language model, weights and neurons

- **Request:** "show a diagram animation of a modern llm weight and neuron setup"
- **Learning goal:** "An LLM turns each token into a vector that flows up a stack of 32 blocks;
  in each block attention lets tokens share information and an MLP of neurons transforms each
  token, and every connection is a learned weight, stored in matrices that add up to billions
  of numbers."
- **Audience and depth:** newcomer with high-school maths, intuitive (skill default; user not reachable).
- **Narration:** silent (skill default; user not reachable).
- **Target length:** about 140 s (broad topic: four chapters, see the scope rule in SKILL.md).
- **Reference model for real numbers:** Llama 3 8B (d_model 4,096; 32 blocks; 32 query heads,
  8 KV heads; MLP width 14,336, gated; vocabulary 128,256; 8.03 B parameters:
  MLP 5.64 B, attention 1.34 B, embedding + output tables 1.05 B).
- **Left out on purpose:** normalisation layers (RMSNorm), positional encoding (RoPE), the
  softmax temperature and sampling, the KV cache, how training sets the weights (backprop),
  mixture-of-experts, the details of multi-head and grouped-query attention, the tokenizer
  algorithm. The gated (SwiGLU) MLP is drawn as a plain neuron with a footnote, and its third
  matrix appears in the weight count.

## Colour legend

| Concept | Colour | Used for |
|---|---|---|
| positive number | BLUE `#58C4DD` | vector cells, weight edges, matrix cells, weight labels |
| negative number | ORANGE `#FF862F` | same (fill opacity = magnitude; edge width = magnitude) |
| attention | PURPLE `#9A72AC` | attention band, arcs, q/k chips, W_Q..W_O, "attention" words |
| MLP / neurons | TEAL `#5CD0B3` | MLP boxes, neuron outlines, activation curve, W_up/W_gate/W_down |
| prediction | GREEN `#83C167` | next-token word and probability bars |
| look here now / neuron firing | YELLOW `#F7D96F` | highlights, edge flashes, neuron fill while active |
| scaffolding, secondary text | GREY_B | lanes (residual stream), braces, axes, footnotes |

Numbers are always `DecimalNumber`/`MathTex`; words are always `Text` (Noto Sans).

## Beats

One idea per beat. Each beat answers a question raised by the one before.

| # | Time (s) | The one idea | Visual metaphor and what appears / leaves | On-screen text (short) | Narration |
|---|---|---|---|---|---|
| 1 | 0-8 | Hook: an LLM continues text | "The cat sat on the" -> [LLM] -> "?" becomes "mat" | title; "it predicts the next token"; "What happens inside the box?" | - |
| 2 | 8-14 | Text becomes tokens | box and arrows leave; the words drop into 5 token chips at the bottom | "text is cut into tokens" | - |
| 3 | 14-24 | Each token becomes a vector | embedding table (8x5 grid) in the right panel; each token's row lights up, copies, turns into a 5-cell column above its chip; table leaves | "a row becomes a vector / 4,096 numbers (5 drawn)" | - |
| 4 | 24-29 | The residual stream | a grey lane rises from each vector | "each vector flows upward / one lane per token" | - |
| 5 | 29-37 | A block = attention + MLP | purple band across all lanes (flash sweeps across), then a teal MLP box on each lane; brace "block 1" | "attention: across tokens / MLP: one token at a time" | - |
| 6 | 37-42 | 32 blocks stacked | block copies upward as "block 32" with a vertical ellipsis | "32 blocks in an 8B model / same layout, own numbers" | - |
| 7 | 42-50 | Each block adds an update | vectors rise through block 1 then block 32, recolouring as bands flash | "each block adds an update / to every token's vector" | - |
| 8 | 50-58 | Prediction | arrow from the last token's top vector to bars "mat", "floor", "bed" | "the last vector scores / every possible next token" | - |
| 9 | 58-70 | Attention moves information between tokens | new diagram: 5 tokens + vectors; arcs from earlier tokens into "the", width = share, % labels; dots travel along arcs; "the" vector changes | "'the' pulls in information from earlier tokens / every token does this, looking only backwards" | - |
| 10 | 70-84 | How the shares are chosen | arcs leave; q chip on "the", k chip on every token; dashed q-k lines; scores, then scores become the same %; four small matrices W_Q W_K W_V W_O with role words | "query · key = match score"; "scores become shares that add up to 100%"; "query, key, value: each made by a weight matrix / 32 heads in parallel" | - |
| 11 | 84-108 | One MLP neuron | "the" vector grows (numbers); neuron; 5 weighted edges with weight numbers; flash -> sum 1.60; activation curve (GELU) -> out 1.51, neuron glows; a different input -> sum -1.60 -> out about 0, quiet; back to firing; plot leaves; output edges write an update vector | "each connection is a weight: one learned number"; "multiply each input by its weight, then add up"; "then a bend: negative sums give about 0"; "it fires when the input matches its weights"; "input weights: the pattern it detects / output weights: what it writes back"; footnote "Llama-style MLPs use a gated version (SwiGLU)" | - |
| 12 | 108-124 | Many neurons = a weight matrix | 5-cell input, 6 neurons, 30 edges; neuron 1's edges fold into row 1 of a grid, then all rows (W_up); a highlight sweeps row by row as neurons light; W_down grid, column 1 = neuron 1's output weights; real sizes | "row k = neuron k's input weights"; "matrix × vector: every neuron at once"; "real size: 14,336 neurons per block" / footnote "Llama-style: a 3rd 'gate' matrix" | - |
| 13 | 124-137 | Parameters at scale | one block's 7 matrices drawn to scale (area = count), braces "attention 42 M", "MLP 176 M"; then a stacked bar for the whole model: MLP 5.6 B, attention 1.3 B, embedding tables 1.1 B | "one block ≈ 218 million weights"; "≈ 8.0 billion weights / all set by training" | - |
| 14 | 137-145 | Recap | four lines, each with its icon (vector, arc, neuron, grid) | 4 short lines | - |

## Layout sketch

- Title band (y 2.75 to 3.4): one short chapter title, centred, font 40.
- Stack chapter (beats 2-8): token chips at the bottom (y -3.05) on lanes x = -5.3 .. 0.3;
  blocks are bands across the lanes; right panel (x 1.6 to 6.4) holds the embedding table,
  block labels, the output bars and the captions (bottom right, at most 25 characters per line).
- Attention chapter: 5 tokens spread across the full width (x = -4.4 .. 4.4), arcs above,
  matrices top-left, captions centred in the footer.
- MLP chapter: input vector left, neuron centre-left, activation plot (later: output vector)
  on the right, captions centred in the footer.
- Scale and recap: centred.

## Open questions for the user (if any)

- None asked (unattended run); narration defaulted to silent.

## Changes in this run (container-route test, on top of the example's storyboard)

- Same beats, content and length (150.0 s). Titles and captions now fade out before the new text
  fades in (no overlapping text mid-swap); digit and "?"->"mat" swaps likewise.
- Layout zones made exact and measured by GeometryGuard: stack chapter = lane diagram centred in
  x -7.11..1.8, panel x 1.8..7.11 (embedding table and prediction bars centred in it); hook row,
  attention row, neuron figure (input and update vectors mirrored about the neuron at the centre),
  MLP-matrix figure, scale charts and recap centred on the frame; every figure keeps 7 % margins.
- Beat 12: W_up rows appear neuron by neuron after that neuron's edges flash (no edge-to-row morph).
