# sims/

Every number the post quotes, in the prose or in a quiz answer, is computed here. Nothing is typed by hand.

- One script per toy or per analysis, named for what it computes (`toy.py`, `paper_counts.py`). Each one is deterministic (fixed seeds), runs from a clean checkout with the packages in `requirements.txt`, and writes its numbers with `save_results("<key>", {...})` into `results.json`.
- `results.json` is committed. The post reads it in its setup cell (`R = load_results()`) and inlines values with `` `{python} fmt(R['toy']['sd'], 3)` ``. Use `fmt`, `pct` and `num` from `shared/simtools.py` so the prose formats numbers the way the widgets do.
- Numbers reported by the paper are data too: record them in a script (for instance `paper_counts.py`, which also reconstructs counts from percentages and denominators), so that they are quoted from `results.json` like everything else.
- `check_numbers.py` re-runs every script into a scratch file, fails if the output no longer reproduces `results.json`, and fails if `index.qmd` contains a number that was typed by hand. Typed numbers that are not computed (a year, "Table 2") are allowed automatically; anything else that must stay typed goes in its `ALLOWED` table with a reason.

Run everything from the repository root:

```sh
for s in posts/<slug>/sims/*.py; do [ "$(basename "$s")" = check_numbers.py ] || (cd "$(dirname "$s")" && python "$(basename "$s")"); done
python posts/<slug>/sims/check_numbers.py
quarto render posts/<slug>/index.qmd   # a single-file render always re-executes, so the page picks up new numbers
```
