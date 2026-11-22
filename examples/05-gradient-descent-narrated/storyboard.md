# Storyboard: How a tiny network learns (gradient descent and backpropagation)

- **Request:** "Explain gradient descent and backpropagation on a tiny neural network."
- **Learning goal:** "Training repeats four moves: run the network forward, measure the loss,
  run backwards multiplying local rates (the chain rule) to get every weight's slope, then step
  each weight against its slope; here one step takes the loss from 4 to 0.71."
- **Audience and depth:** newcomer with high-school maths (knows what a slope is), intuitive.
- **Narration:** Kokoro, voice af_heart, through manim-voiceover (`KokoroService`).
- **Target length:** about 160 s (two topics; under the 3-minute cap).
- **Left out on purpose:** activation functions (the network is linear so every local rate is
  a plain number), biases, more than one training example, batches, momentum and other
  optimisers, vectors and matrices, how to choose the learning rate (overshoot is not shown).

## The numbers (checked in Python before coding)

Network: `h = w1 * x`, `ŷ = w2 * h`, loss `L = (ŷ - y)^2`. Input `x = 2`, target `y = 3`,
start `w1 = 1`, `w2 = 0.5`, learning rate `η = 0.05`.

| Quantity | Value |
|---|---|
| forward | h = 2, ŷ = 1, L = (1 - 3)^2 = 4 |
| ∂L/∂ŷ = 2(ŷ - y) | -4 |
| ∂L/∂w2 = ∂L/∂ŷ · h | -4 · 2 = -8 |
| ∂L/∂h = ∂L/∂ŷ · w2 | -4 · 0.5 = -2 |
| ∂L/∂w1 = ∂L/∂h · x | -2 · 2 = -4 |
| nudge w1 by +0.01 | h +0.02, ŷ +0.01, L -0.0399 (≈ -0.04, so slope ≈ -4) |
| update | w1 = 1 - 0.05·(-4) = 1.2, w2 = 0.5 - 0.05·(-8) = 0.9 |
| forward again | h = 2.4, ŷ = 2.16, L = 0.84^2 = 0.7056 ≈ 0.71 |
| one more step | L ≈ 0.0005 |
| 1D valley (w1 frozen at 1) | L(w2) = (2 w2 - 3)^2, slope 4(2 w2 - 3); at w2 = 0.5: L = 4, slope -8 (same as backprop) |
| 1D descent, η = 0.05 | w2: 0.5 → 0.9 → 1.14 → 1.284 → 1.370 → 1.422 (minimum at 1.5) |

## Colour legend

| Concept | Colour | Used for |
|---|---|---|
| signals (x, h, ŷ) | BLUE | node values, x, h, ŷ in equations, prediction dot on the number line |
| weights (w1, w2) | TEAL | edge labels, w1 and w2 in equations, the horizontal axis of the valley |
| target y | GREEN | target label and dot on the number line |
| loss L | RED | loss node, loss curve, the squared-error square, L in equations |
| gradients / slopes / local rates | ORANGE | tangent line, ∂ values, ×rate labels, backward pulses |
| "look here now" | YELLOW | the moving point on the valley, nudge amounts, forward pulses |
| learning rate η, scaffolding | WHITE / GREY_B | η, axes, edges |

## Beats

| # | Time (s) | The one idea | Visual: what appears / leaves | On-screen text | Narration |
|---|---|---|---|---|---|
| 1 | 0-9 | A network is a chain of multiplications by weights | Title, then nodes x, h, ŷ appear left to right, edges with w1 = 1, w2 = 0.5 | title; node symbols; w labels | "Here is about the smallest neural network you can train. One input, one hidden neuron, one output, and two weights." |
| 2 | 9-22 | Forward pass | x = 2 enters; a yellow pulse runs along each edge; h = 2 then ŷ = 1 fill in; formula line below | `h = w1 x = 2`, `ŷ = w2 h = 1` | "Each weight multiplies the signal passing through it." / "Feed in two. The hidden neuron gets one times two, which is two." / "The output gets one half times two, which is one." |
| 3 | 22-36 | The loss measures how wrong | Loss node L and target y = 3 appear; number line with ŷ = 1 and y = 3, gap 2, a red square of side 2 grows: area 4 | `y = 3`, `L = (ŷ - y)^2 = 4` | "But we wanted three." / "To measure how wrong the network is, take the gap between output and target, and square it." / "That is the loss: two squared, which is four." |
| 4 | 36-50 | Which way to move a weight? Look at the loss as a function of w2 | Network fades; axes (w2 vs L); w2 slides and the valley is traced; point stops at w2 = 0.5, L = 4 | axis labels | "Training means changing the weights to shrink the loss. But which way should each weight move?" / "Freeze w one, slide w two, and plot the loss. It traces a valley, and we are on its left wall." |
| 5 | 50-60 | The slope (gradient) says which way is downhill | Orange tangent at the point; `∂L/∂w2 = -8`; arrow "downhill" pointing right | `∂L/∂w2 = -8` | "The slope here is minus eight. A negative slope means the loss falls as w two grows, so downhill is to the right." |
| 6 | 60-75 | Gradient descent step | Update rule in the side panel; point moves 0.5 → 0.9, loss 4 → 1.44 | `w2 ← w2 - η ∂L/∂w2`, `η = 0.05` | "Gradient descent steps against the slope, scaled by a small learning rate, here zero point zero five." / "That moves w two from one half to zero point nine, and the loss drops from four to about one and a half." |
| 7 | 75-84 | Repeat: steps shrink as the valley flattens | Four more steps, each smaller; point settles near the bottom | - | "Repeat, and the steps shrink as the valley flattens, until we settle at the bottom." |
| 8 | 84-94 | Many weights need many slopes: the job of backprop | Valley fades, network returns at the start values (w1 = 1, w2 = 0.5, L = 4); both weights get an orange "?" | `∂L/∂w1 = ?`, `∂L/∂w2 = ?` | "A real network has millions of weights, and needs the slope for every one at once." / "Back to the start: how does w one, buried deep inside, affect the loss?" |
| 9 | 94-110 | A nudge travels down the chain | Yellow nudge amounts appear in order under w1, h, ŷ, L | `+0.01`, `+0.02`, `+0.01`, `-0.04` | "Nudge w one up by one hundredth." / "The hidden value rises by two hundredths." / "The output rises by one hundredth." / "And the loss falls by four hundredths." |
| 10 | 110-124 | Chain rule: local rates multiply | Orange curved arrows between the nudges with ×2, ×0.5, ×(-4); product formula at the bottom | `∂L/∂w1 = 2 · 0.5 · (-4) = -4` | "Each link scales the nudge by its own local rate." / "Times two, times one half, times minus four." / "Multiply the rates, and you get the slope for w one: minus four. That is the chain rule." |
| 11 | 124-148 | Backprop: run the chain rule backwards, reusing products | Nudges leave; orange pulses travel right to left; -4 under ŷ, -8 under w2, -2 under h, -4 under w1; bottom line shows each product | `∂L/∂ŷ = -4`, `∂L/∂w2 = -8`, `∂L/∂h = -2`, `∂L/∂w1 = -4` | "Backpropagation runs the chain rule backwards, starting at the loss." / "The loss changes at minus four per unit of output." / "Times h, which is two, gives the slope for w two: minus eight." / "Times w two, one half, passes minus two back to the hidden neuron." / "Times x, which is two, gives the slope for w one: minus four." / "One backward sweep, and every slope is known." |
| 12 | 148-160 | One gradient step on both weights | Update formulas at the bottom; w labels change to 1.2 and 0.9 | `w1 = 1 - 0.05·(-4) = 1.2`, `w2 = 0.5 - 0.05·(-8) = 0.9` | "Now one gradient descent step updates both weights at once." / "w one becomes one point two, and w two becomes zero point nine." |
| 13 | 160-172 | Forward again: the loss really dropped | Yellow pulse forward; h = 2.4, ŷ = 2.16, L = 0.71; number line returns: the red square shrinks from area 4 to 0.71 | `L: 4 → 0.71` | "Run it forward again. The output is now two point one six, much closer to three." / "The loss drops from four to about zero point seven." |
| 14 | 172-186 | Recap: the training loop | Stage clears; a loop of four boxes (forward, loss, backward, step) with a highlight going round; loss history 4 → 0.71 → 0.0005 | box labels; loss history | "That is training: a forward pass, a loss, a backward pass for the slopes, and a small step downhill." / "Repeat it, and the loss keeps falling: after one more step, it is almost zero." |

## Layout sketch

- Title band (y 2.7 to 3.4): the chapter title, small (36), top-left.
- Network chapter: nodes in one row at y = 1.4 (x at -5.1, -1.7, 1.7; loss box at 5.1); node
  symbols above the nodes, weight labels above the edge midpoints. Weight gradients sit just
  below the edge midpoints (y about 0.6); node gradients below the nodes one row lower
  (y about -0.4); the formula line sits in the footer band (y about -2.6). The number line with
  the squared-error square uses the lower half in beats 3 and 13, when no gradients are shown.
- Valley chapter: axes centre-left (x from -6 to 1.8), side panel on the right (x 2.5 to 6.4)
  for the slope, the update rule and η.
- Recap: a four-box loop in the centre, loss history underneath.

## Open questions for the user (if any)

- None (narration answered; other defaults used).

## As built (final)

- 38 voiceover blocks, one per sentence or clause (beat 10's list sentence got its own block so
  each ×rate appears as it is spoken). Final length 159 s (target about 160 s).
- Beat 5's "downhill" arrow sits inside the valley, parallel to the tangent.
