"""Helpers for a post's sims/ folder: save results, read them in the prose,
and check that the prose quotes nothing that sims/ did not compute.

In a simulation script (posts/<slug>/sims/<name>.py):

    from simtools import save_results
    save_results("toy", {"sd": 0.25, ...})        # merged into sims/results.json

In the post (the Jupyter kernel runs in the post's folder):

    import sys; sys.path.insert(0, "../../shared")
    from simtools import load_results, fmt
    R = load_results()
    ... `{python} fmt(R['toy']['sd'], 3)` ...

In sims/check_numbers.py:

    sys.exit(check_post(POST_DIR, allowed={...}))
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RESULTS_ENV = "BLOG_RESULTS"  # where save_results writes; check_post points it at a scratch file
MINUS, THIN = "−", " "


# --- writing and reading results -------------------------------------------------

def _results_path(default_dir: Path) -> Path:
    env = os.environ.get(RESULTS_ENV)
    return Path(env) if env else default_dir / "results.json"


def save_results(key: str, data, sims_dir: Path | str | None = None) -> Path:
    """Merge `data` under `key` into sims/results.json (sorted, stable diff)."""
    if sims_dir is None:
        sims_dir = Path(sys.argv[0]).resolve().parent
    path = _results_path(Path(sims_dir))
    results = json.loads(path.read_text()) if path.exists() else {}
    results[key] = _plain(data)
    path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    return path


def load_results(path: Path | str = "sims/results.json") -> dict:
    return json.loads(Path(path).read_text())


def _plain(x):
    """numpy scalars and arrays to JSON-friendly Python values."""
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


# --- formatting, identical to blog.fmt in shared/widgets.js -----------------------

class Quoted(str):
    """A formatted number. Inlined with `{python} ...`, Quarto takes its Markdown
    repr verbatim; the plain repr would come back quoted and escaped, and would
    lose the thin space."""

    def _repr_markdown_(self) -> str:
        return str(self)


def fmt(x: float, digits: int = 2) -> Quoted:
    """Fixed decimals, a real minus sign, thin spaces between thousands."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return Quoted("n/a")
    if math.isinf(x):
        return Quoted((MINUS if x < 0 else "") + "∞")
    s = f"{abs(x):,.{digits}f}".replace(",", THIN)
    negative = x < 0 and any(c not in "0." + THIN for c in s)
    return Quoted((MINUS if negative else "") + s)


def pct(x: float, digits: int = 1) -> Quoted:
    return Quoted(fmt(100 * x, digits) + "%")


def num(x: int) -> Quoted:
    return fmt(round(x), 0)


# --- checking a post ---------------------------------------------------------------

def _compare(a, b, path="", rtol=1e-6, atol=1e-12):
    """Yield a message for every value of `a` that `b` does not reproduce."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                yield f"{path}/{k}: in results.json but not produced by the scripts"
            elif k not in a:
                yield f"{path}/{k}: produced by the scripts but missing from results.json"
            else:
                yield from _compare(a[k], b[k], f"{path}/{k}", rtol, atol)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from _compare(x, y, f"{path}[{i}]", rtol, atol)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not math.isclose(a, b, rel_tol=rtol, abs_tol=atol):
            yield f"{path}: results.json has {a!r}, the scripts now give {b!r}"
    elif a != b:
        yield f"{path}: results.json has {a!r}, the scripts now give {b!r}"


# Prose is what a reader sees: drop code, maths, comments, links and labels.
_STRIP = [
    (re.compile(r"\A---\n.*?\n---\n", re.S), " "),          # YAML front matter
    (re.compile(r"^(```|~~~).*?^\1\s*$", re.S | re.M), " "),  # fenced code, raw HTML blocks
    (re.compile(r"<!--.*?-->", re.S), " "),                  # comments
    (re.compile(r"`[^`\n]*`"), " "),                          # inline code, incl. {python} values
    (re.compile(r"\$\$.*?\$\$", re.S), " "),                 # display maths
    (re.compile(r"(?<![\\$])\$[^$\n]+\$"), " "),              # inline maths
    (re.compile(r"\]\([^)]*\)"), "]"),                        # link targets
    (re.compile(r"https?://\S+"), " "),                      # bare URLs
    (re.compile(r"[@#][\w:.-]+"), " "),                      # citations, cross-refs, ids
    (re.compile(r"\{[.#][^}]*\}"), " "),                      # attributes {#sec-x .unnumbered}
    (re.compile(r"\b(?:n|label|title|hint|q|a)=(?=\")"), " "),  # shortcode keys
]
_NUMBER = re.compile(r"(?<![\w.−-])[−-]?\d[\d, ]*(?:\.\d+)?\s?%?")
_REFERENCE = re.compile(
    r"(?:^|(?<=[\s(\[,;]))(?:§|Table|Tables|Tab\.|Figure|Figures|Fig\.|Figs\.|Eq\.|Equation|Section|Sections|page|pages|p\.|pp\.|"
    r"Supplementary|Supplement|Appendix|Proposition|Theorem|Lemma|Definition|Example|Method|Step|"
    r"principle|Principle|arXiv:?|vol\.|no\.)\s*[\w.]*$"
)


def hand_typed_numbers(qmd_text: str, allowed: dict[str, str] | None = None):
    """Numbers in the prose that were typed by hand rather than inlined from code.

    Allowed without comment: integers 0 to 10, years 1900 to 2099, and numbers
    that follow a reference word (§, Table, Figure, p., ...). Anything else must
    be listed in `allowed` with a reason, or inlined from sims/.
    """
    allowed = allowed or {}
    text = qmd_text
    for pattern, repl in _STRIP:
        text = pattern.sub(repl, text)
    found = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in _NUMBER.finditer(line):
            token = m.group(0).strip()
            bare = token.replace(" ", "").replace(",", "").rstrip("%").strip()
            if token in allowed or bare in allowed:
                continue
            if _REFERENCE.search(line[: m.start()].rstrip()[-24:] if m.start() else ""):
                continue
            try:
                value = float(bare.replace("−", "-"))
            except ValueError:
                continue
            is_int = re.fullmatch(r"[−-]?\d+", bare) is not None and "%" not in token
            if is_int and (0 <= value <= 10 or 1900 <= value <= 2099):
                continue
            found.append((token, line.strip()[:100]))
    return found


def check_post(post_dir: Path | str, allowed: dict[str, str] | None = None, rtol: float = 1e-6) -> int:
    """Re-run every script in sims/ and check the post's numbers. Returns an exit code.

    1. Each sims/*.py (except check_numbers.py) runs in a fresh process, writing
       to a scratch results file; the result must reproduce sims/results.json.
    2. index.qmd must contain no hand-typed numbers outside `allowed`.
    """
    post = Path(post_dir).resolve()
    sims = post / "sims"
    problems: list[str] = []

    committed_path = sims / "results.json"
    committed = json.loads(committed_path.read_text()) if committed_path.exists() else {}
    scripts = sorted(p for p in sims.glob("*.py") if p.name != "check_numbers.py")
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "results.json"
        env = dict(os.environ, **{RESULTS_ENV: str(scratch)})
        for script in scripts:
            run = subprocess.run([sys.executable, script.name], cwd=sims, env=env,
                                 capture_output=True, text=True)
            status = "ok" if run.returncode == 0 else f"FAILED (exit {run.returncode})"
            print(f"  ran sims/{script.name}: {status}")
            if run.returncode != 0:
                problems.append(f"sims/{script.name} failed:\n{run.stderr.strip()}")
        fresh = json.loads(scratch.read_text()) if scratch.exists() else {}
    problems += [f"results.json{msg}" for msg in _compare(committed, fresh, rtol=rtol)]

    qmd = post / "index.qmd"
    for token, context in hand_typed_numbers(qmd.read_text(), allowed):
        problems.append(f"index.qmd: hand-typed number {token!r} in: {context}")

    if problems:
        print(f"\n{len(problems)} problem(s) in {post.name}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"{post.name}: {len(scripts)} script(s) reproduce results.json; no hand-typed numbers.")
    return 0
