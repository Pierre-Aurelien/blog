---
name: new-paper-post
description: Write a new first-principles tutorial post on one scientific paper for this blog. Reads the paper and its supplement, proposes an outline and waits for approval, builds the simulations before the prose, adds the components and widgets, runs the definition-of-done checks, and opens a pull request. Use when asked for a "new paper post" or a new tutorial on a paper.
---

# New paper post

Read `CLAUDE.md` first: its style brief, repo conventions and definition of done apply to every step below.

Two rules hold throughout:

- **Every number comes from `sims/`.** Every number quoted in the prose or in a quiz answer is computed by a script in the post's `sims/` folder and inlined from a Python cell, usually through `results.json` (`` `{python} fmt(R['key']['value'], 3)` ``). Never type a computed number by hand, and record the paper's own reported numbers in a script too.
- **Confidentiality.** Posts are public, even when the repo is private. Write no employer-internal details, unpublished data, or facts known only from colleagues. When in doubt, mark the passage with `<!-- CONFIDENTIAL? -->` and list it in the pull request description.

## 1. Read the whole paper

Read the main text, every figure and table, the methods, and the whole supplement. Then:

- Reconstruct the paper's counts from its reported percentages and denominators: for each reported percentage, find the denominator it applies to and the integer count it implies, and check that the counts add up across tables, text and abstract.
- List every inconsistency you find, each with its location (table, figure, page) and what disagrees with what. A percentage that matches no integer count, a denominator that changes between sections, or a number in the abstract that differs from its table all count.
- Note which claims can be verified from the paper and supplement, and which cannot ("to verify").

Report all of this to the user before going on.

## 2. Propose an outline, then stop

Propose about 8 to 12 sections. For each one give:

- its "The question" line;
- the toy that answers it: the smallest system, with its parameters, and what the reader will see change;
- its takeaway, in one or two sentences.

Also give the five key messages, the scope (what the post covers and leaves out), the thinking principles you expect, and where you expect to disagree with the paper.

**Stop here and wait for the user's approval of the outline.** Do not create files before it is approved; revise the outline as asked.

## 3. Create the post

```sh
git checkout main && git pull
git checkout -b <slug>
cp -R _template posts/<YYYY-MM>-<slug>
```

Set the front matter: `title`, the one-sentence `subtitle`, `kicker` ("Tutorial · Subfield"), `date`, `categories`. Add the paper and every other source to `shared/refs.bib`.

## 4. Simulations first

Write the scripts in `sims/` before any prose, one per toy or analysis, each with fixed seeds and writing its numbers with `save_results("<key>", {...})`. Include a script that records the paper's reported numbers and the counts reconstructed in step 1. Delete the template's `toy.py` unless it is used.

Run every script, commit `results.json`, and run `python posts/<slug>/sims/check_numbers.py`. Only then write the prose, around the numbers the scripts produced. If a number surprises you, find out why before writing about it.

## 5. Components and widgets

Build each section from the components in `CLAUDE.md`:

- the question line, the toy, then the real system, then a takeaway;
- definitions, propositions and proofs in boxes, with proofs, derivations, code and long asides folded;
- at least one "Check yourself" quiz per major section, with an answer that `sims/` computes;
- thinking principles numbered in order of first appearance, restated in a final "Thinking principles" section and added to `principles.md`;
- interactive figures in `widgets.js`, using the helpers in `shared/widgets.js`, with sliders, presets and a readout that states numbers, and a caption that says what to look at;
- a "References" table saying what each source is used for, then `::: {#refs}`.

A new box type, widget helper or figure style goes into `theme/` or `shared/` in this same pull request, not into the post.

## 6. Check and open the pull request

Run the definition of done from `CLAUDE.md` and fix whatever fails:

```sh
tools/check_render.sh posts/<slug>/index.qmd
.venv/bin/python posts/<slug>/sims/check_numbers.py
.venv/bin/python tools/check_page.py posts/<slug>
```

Look at the screenshots in `screenshots/posts_<slug>/` yourself, in both modes and at phone width. Update `principles.md`. Re-render the post so that `_freeze/` is current, commit, push the branch, and open a pull request whose description lists:

- the sections, each with its question;
- the simulations, each with what it computes;
- every "to verify" item;
- every confidentiality flag (`<!-- CONFIDENTIAL? -->`), or "none";
- the inconsistencies found in the paper in step 1.
