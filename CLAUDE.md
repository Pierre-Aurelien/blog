# CLAUDE.md

A Quarto blog of first-principles tutorials on scientific papers, published at https://pierre-aurelien.github.io/blog/ from the `gh-pages` branch by `.github/workflows/publish.yml`. To write a new post, follow the `new-paper-post` skill (`.claude/skills/new-paper-post/SKILL.md`).

## Style brief

Each post is a first-principles tutorial on one paper, for a technically strong reader who is new to the subfield.

**Structure.** Every post opens with a kicker line, a title, a one-sentence subtitle, a scope box, and five key messages. Each section has a numbered heading (§n) and a "The question" line, and closes with a Takeaway. Each section builds a minimal toy before it touches the real system: the toy comes first, and the paper's system arrives as a change to the toy, with the point where the analogy breaks stated.

**Formal results.** Definitions, propositions and proofs are boxed. Proofs, derivations, code and long asides are folded, so that the main line stays short: a reader who opens no fold still follows the argument.

**Exercises.** Each major section has at least one "Check yourself" quiz, with a numeric answer that a simulation in `sims/` checks.

**Thinking principles.** Number them in the order they first appear in the post, state each one where it does its work, and collect them in a final "Thinking principles" section and in `principles.md`.

**Interactive toys.** Canvas or SVG, with sliders, presets and a live readout. The readout states numbers, not adjectives: "measured spread 0.126, prediction 0.125", never "close to the prediction". Each figure has a caption that says what to look at.

**Voice.**

- Prose over bullets.
- Direct and precise; no hype.
- Every claim about the paper is cited to a table, figure or page: `[@key, Table 2]`, `[@key, p. 7]`, `[@key, Fig. S3]`.
- Disagreements with the paper are stated plainly, with the evidence.
- Figures that cannot be verified are marked "to verify", in a caution callout titled "To verify", and listed in the pull request.

**Corrections.** A revised post opens, before the scope box, with a fold titled "What this revision corrects" whose hint gives the date of the revision, and sets `date-modified` in its front matter (the kicker then shows it).

## Repo conventions

**Layout.**

| path | what it holds |
|:---|:---|
| `posts/<YYYY-MM>-<slug>/` | one post: `index.qmd`, `sims/`, `figures/`, `widgets.js`. Created from `_template/`. |
| `_template/` | an empty post that uses every component once; copy it, never render it. |
| `theme/tokens.scss` | palette, fonts, light and dark modes. |
| `theme/components.scss` | boxes, callouts, theorems, folds, questions, takeaways, principles, figures, listing. |
| `theme/title-block.html` | the kicker, title and subtitle at the top of a post. |
| `_extensions/blog/` | the shortcodes (`shortcodes.lua`), proofs as folds (`proofs.lua`), the component renderer (`components.lua`), fold and theme behaviour (`blog.js`). |
| `shared/widgets.js` | widget helpers: `blog.pal`, `blog.fit`, `blog.fmt`, `blog.slider`, `blog.presets`, `blog.readout`, `blog.redraw`, `blog.ready`, `blog.rng`. |
| `shared/simtools.py` | `save_results`, `load_results`, `fmt`/`pct`/`num` (formatting identical to `blog.fmt`), and `check_post` behind each `sims/check_numbers.py`. |
| `shared/refs.bib` | every post's references. |
| `tools/check_render.sh`, `tools/check_page.py` | the render check and the screenshot check of the definition of done. |
| `legacy/` | the September 2026 posts as self-contained HTML, served unchanged and listed through `legacy/listing.yml`. Do not edit or port them. |
| `principles.md` | the running list of thinking principles; `principles.qmd` renders it. |

**Components.** Use components only through these shortcodes, callouts and theorem environments. Write no raw HTML in a post, except inside a figure's widget container.

| component | write | look |
|:---|:---|:---|
| kicker, title, subtitle | front matter `kicker:`, `title:`, `subtitle:`; `date` (and `date-modified`) are appended to the kicker | |
| scope box | `::: {.callout-note title="Scope"}` | teal, solid |
| five key messages | `::: {.callout-important title="Five key messages"}` with a numbered list | orange, solid |
| intuition | `::: {.callout-tip}` (title defaults to "Intuition") | teal, dashed |
| definition | `::: {#def-name}` with `## Name` as its first line | teal, solid, tinted |
| theorem, proposition, lemma, corollary | `::: {#thm-name}`, `{#prp-name}`, `{#lem-name}`, `{#cor-name}` | wine, solid |
| proof | `::: {.proof hint="the idea in one line"}`, directly after the result | folded, attached to the box above |
| pitfall | `::: {.callout-warning title="..."}` (default "Pitfall") | wine, dashed |
| worked example | `::: {#exm-name}` | orange, solid, tinted |
| caution, "to verify" | `::: {.callout-caution title="To verify"}` | orange, dashed |
| method | `::: {#alg-name}` (rendered "Method n") | ink, solid |
| the question | `{{< question "..." >}}` right under the section heading | italic, labelled |
| takeaway | `{{< takeaway >}} ... {{< /takeaway >}}` (`label="..."` renames it) | orange rule |
| check yourself | `{{< quiz q="..." a="..." >}}` | teal, dashed, folded answer |
| thinking principle | `{{< principle n="3" >}} ... {{< /principle >}}` | numbered wine circle |
| fold | `{{< fold title="..." hint="..." >}} ... {{< /fold >}}` | dashed, title and muted hint |
| interactive figure | `::: {#fig-name}` holding one ```` ```{=html} ```` block with `<div class="fig">` (`.controls`, a `canvas` or `svg`, a `.readout`), then the caption as the last paragraph | panel |

Shortcode arguments are one line of Markdown: maths, citations, cross-references and inline `{python}` values all work inside them. Put block shortcodes on their own lines with blank lines around them. Unbalanced pairs are reported as `(W) blog:` warnings. The "Unfold all / Fold all" bar is added automatically to any post with folds, just before §1. Sections are `##` headings with an id (`## A minimal toy {#sec-toy}`); `## References {.unnumbered}` stays unnumbered.

**Numbers come from code.** Every number quoted in the prose or in a quiz answer comes from code in `sims/`. Either inline it from a Python cell (`` `{python} f"{x:.2f}"` ``), or have `sims/` write it to `results.json` and read it from there: the template's setup cell loads `R = load_results()`, and the prose writes `` `{python} fmt(R['toy']['sd'], 3)` ``. Never type a computed number by hand. Numbers reported by the paper are recorded in a script too (for instance `sims/paper_counts.py`), so that they are quoted from `results.json` like everything else. Use `fmt`, `pct` and `num`: they give a real minus sign and thin-space thousands, matching the widgets.

**Freezing.** `freeze: auto`, and `_freeze/` is committed, so a full-site render (including CI) only re-runs posts whose `index.qmd` changed. Rendering a single file always re-executes it: after re-running `sims/`, run `quarto render posts/<slug>/index.qmd` and commit the updated `_freeze/`.

**Widgets.** If a post folder has a `widgets.js`, it is loaded automatically, after `shared/widgets.js`. Wrap it in `blog.ready(...)`, read colours with `blog.pal()` at draw time (never hard-code a colour, so dark mode works), and draw through `blog.redraw(...)`, which also redraws on resize, theme change and fold opening. Prefix element ids with the figure's name (`toy-n`, `toy-canvas`). SVG labels use the classes `t-t`, `t-o`, `t-w`, `t-m` and strokes `ln`, `ln-t`, `ln-o`, `ln-w`, `ln-m`.

**Reusable pieces** go to `theme/` or `shared/` in the same pull request that introduces them: a new box type, a widget helper, a figure style. A post never carries its own CSS.

**References.** Each post's references go in `shared/refs.bib` (keys `<firstauthor><year><word>`), plus a short hand-written "References" table at the end of the post that says what each source is used for, followed by the `::: {#refs}` bibliography.

**Confidentiality.** Posts are public, even when the repo is private. Write no employer-internal details, unpublished data, or facts known only from colleagues. When in doubt, mark the passage with an HTML comment `<!-- CONFIDENTIAL? -->` and say so in the pull request description.

**Commands.**

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt   # once
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto preview                                    # live site
tools/check_render.sh                             # render, fail on bad cross-refs or citations
.venv/bin/python posts/<slug>/sims/check_numbers.py
.venv/bin/python tools/check_page.py posts/<slug>
```

## Definition of done

Before saying a post is finished:

1. `tools/check_render.sh` succeeds: `quarto render` runs with no warnings about missing cross-references or citations, and no `(W) blog:` warnings.
2. Every script in `sims/` runs from a clean checkout, and `python posts/<slug>/sims/check_numbers.py` passes: it re-runs every script, fails if their output no longer reproduces `results.json`, and fails if the prose or a quiz answer contains a number typed by hand.
3. `python tools/check_page.py posts/<slug>` passes. It takes Playwright screenshots of the post in light mode, in dark mode, and at 390 px width in both, with every fold open, and checks that:
   - the page does not scroll horizontally at phone width;
   - no SVG text overflows its SVG;
   - every widget draws, and responds to its sliders and presets.
   Look at the screenshots in `screenshots/` as well: the checks catch breakage, not ugliness.
4. `principles.md` is updated with the post's principles.
5. A pull request is open. Its description lists the sections, the simulations, any "to verify" items and any confidentiality flags.
