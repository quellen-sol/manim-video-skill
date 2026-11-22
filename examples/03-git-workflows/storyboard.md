# Storyboard: Git, visually

> Adopted from `examples/03-git-workflows/` at the owner's request (keep content and length,
> about 139 s). Changes in this run: beat 2 snapshots shrink into the commit instead of
> morphing; beats 4-5 highlight with a flash / box instead of Indicate / Circumscribe; beat 8
> copies hop with their old ids and swap ids with a fade; beat 9 HEAD goes around the right end
> of the graph on `git switch main`; beat 13 the green frame wraps the check mark.

- **Request:** "show an animation of git actions - commit, branching, merging, rebasing, conflict
  resolution strategies in an enterprise environment, etc"
- **Learning goal:** "A commit is a snapshot that points to its parent and a branch is just a
  movable label; merge joins two histories with a two-parent commit, rebase replays my commits as
  new copies on top; when both sides change the same line a person resolves it; and in a team,
  everything reaches a protected main through a reviewed pull request."
- **Audience and depth:** newcomer (knows files and saving, not git), intuitive (default).
- **Narration:** silent (default; the user could not be asked). Captions carry the words.
- **Target length:** planned about 175 s (6 chapters; broad prompt, see SKILL.md "Scope"); the
  built video runs 139 s, because silent captions needed fewer seconds per beat than the first
  estimate. Beat times below are the measured ones from the final preview.
- **Left out on purpose:** staging area / index details, remotes and fetch/pull mechanics,
  cherry-pick, interactive rebase, reset/revert, tags, submodules, three-way merge algorithm
  internals, `-s ours` vs `-X ours` distinction, signed commits, CODEOWNERS, merge queues.

## Colour legend

| Concept | Colour | Used for |
|---|---|---|
| main branch | BLUE `#58C4DD` | main tag, commits made on main, "ours" in the conflict, the rename `fetchUser` |
| feature branch | ORANGE `#FF862F` | feature tag, feature commits and their rebased copies, "theirs", the `, cache` change |
| HEAD (where you are) | WHITE outline tag | HEAD tag, stacked next to the checked-out branch's tag |
| look here now | YELLOW | unsaved change in the file card, parent arrows being pointed out |
| conflict / rejected | RED | conflicted file border, rejected push cross (always with a word) |
| resolved / approved | GREEN | check marks, "keeps both" (always with a word) |
| old, unreferenced commits | 25 % opacity ghost | originals left behind by rebase |
| scaffolding | GREY_B | parent arrows, captions' secondary text, pipeline boxes |

Commit = circle with a 3-character short id inside (real ids are 40 hex digits; shortened).
Parent arrows point from a commit to its parent (right to left), as git stores them.

## Beats

| # | Time (s) | The one idea | Visual metaphor and what appears / leaves | On-screen text (short) |
|---|---|---|---|---|
| 1 | 0-4 | Hook: a team's code history | Title card fades in and out | "Git, visually" / "how a team's code history grows" |
| 2 | 4-14 | A commit is a snapshot | File card `app.py`; a line turns yellow (an edit); a text-free copy of the card shrinks into the commit's slot, then the commit fades in. Repeat: second commit with an arrow to the first | ch "1 Commits"; `$ git commit`; "a commit saves a snapshot of your files" then "each commit points to its parent" |
| 3 | 14-22 | A branch is a label | `main` tag appears on the newest commit; third commit: the tag slides forward. File card leaves | "a branch is a label on a commit" then "commit again: the label moves along" |
| 4 | 22-29 | New branch = new label; HEAD | `HEAD` tag appears above `main`; `git switch -c feature`: `feature` tag on the same commit, HEAD moves to it | ch "2 Branches"; "HEAD marks the branch you are on" then "a new branch: a second label, same commit" |
| 5 | 29-34 | Only the checked-out branch moves | Two commits on the lower lane; feature + HEAD slide; main stays (indicated) | "only the branch you are on moves" |
| 6 | 34-38 | Divergence | A teammate's commit lands on main; main slides; fork is visible | "meanwhile a teammate's work lands on main" |
| 7 | 38-47 | Merge commit | `git switch main` (HEAD moves); `git merge feature`: commit M with two parent arrows (flash yellow); main + HEAD slide to M | ch "3 Merge"; "a merge commit has two parents" |
| 8 | 47-60 | Rebase replays copies | Rewind (M leaves, main back); `git switch feature`; `git rebase main`: copies of e5b and 9a0 hop together (same arc offset) onto the tip of main, still showing the old ids; arrows grow; tags follow; originals become ghosts while the ids fade to 2be and 6d7 | ch "4 Rebase"; "rewind: same start, another option"; "rebase replays your commits on top of main"; "new commits, new ids: the old ones are left behind" |
| 9 | 60-67 | Fast-forward, linear history | `git switch main` (HEAD goes around the right end of the graph, crossing no arrow), `git merge feature`: main tag just slides (no new commit); ghosts leave and the line straightens | "main just slides forward: a fast-forward"; "one straight line of history" |
| 10 | 67-71 | The golden rule | Warning caption (red) | "only rebase commits nobody else has yet" |
| 11 | 71-79 | Why conflicts happen | Stage cleared. Base card `getUser(id)` above; main's card `fetchUser(id)` (blue part) and feature's card `getUser(id, cache)` (orange part); arrows from base | ch "5 Conflicts"; "both branches changed the same line" |
| 12 | 79-84 | Git stops and marks it | `git merge feature`: the two cards merge into one red-bordered file with `<<<<<<< HEAD`, `=======`, `>>>>>>> feature`; labels ours (blue) / theirs (orange) | "Git can't choose: it marks the conflict" |
| 13 | 84-95 | Resolution strategies | Three rows on the right: keep ours (loses the caching), keep theirs (loses the rename), edit by hand `fetchUser(id, cache)` (keeps both, green check). Then `git add app.py && git commit` | "a person decides" then "then commit to finish the merge" |
| 14 | 95-99 | ours/theirs gotcha | Caption only | "careful: in a rebase, ours and theirs swap" |
| 15 | 99-111 | Protected main | Stage cleared. Mini main lane with a lock on `main`; a direct push is rejected (red cross + word) | ch "6 In a team"; `$ git push origin main`; "main is protected: no direct pushes" |
| 16 | 111-121 | Pull request flow | Four boxes: pull request, CI tests, code review, merge into main; a token travels, each gate gets a green check | "changes arrive through a reviewed pull request" |
| 17 | 121-131 | Merge policy | Three mini graphs: merge commit, squash, rebase & merge, one trait each | "the team picks one merge policy" |
| 18 | 131-139 | Recap | Five short lines, colour-keyed | (recap lines) |

## Layout sketch

- Title band (y 2.7 to 3.4): chapter title top-left ("1  Commits", number in grey); the git
  command as a small terminal chip top-right (mono, grey).
- Main stage (y -2.6 to 2.4): commit graph on two lanes, main at y = 0.75, feature at y = -1.05.
  Commits at x = -5.4, -3.9, -2.4 (main), -0.9, 0.6 (feature), 2.1 (teammate on main),
  3.6 (merge commit / first rebased copy), 5.1 (second copy). Branch tags above main-lane commits,
  below feature-lane commits; HEAD stacked one slot further out.
- Footer band (y -3.4 to -2.8): one caption line, centred.
- Chapter 5: code cards in the stage; chapter 6: mini graph, pipeline row, three mini graphs.

## Open questions for the user (if any)

- Narration or silent (could not ask; silent by default).
- Which merge policy their organisation uses (the video shows all three neutrally).
