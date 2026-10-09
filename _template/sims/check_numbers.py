"""Re-run every simulation in this folder and check the numbers the post quotes.

    python posts/<slug>/sims/check_numbers.py

Fails if a script errors, if the scripts no longer reproduce results.json, or
if index.qmd contains a number typed by hand. See shared/simtools.py.
"""

import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "_quarto.yml").exists())
sys.path.insert(0, str(ROOT / "shared"))
from simtools import check_post  # noqa: E402

# Numbers that may stay typed in the prose, each with its reason. Keep this short:
# a number that was computed belongs in sims/ and is inlined from results.json.
ALLOWED: dict[str, str] = {
    # "1983": "publication year in a citation",
}

if __name__ == "__main__":
    sys.exit(check_post(Path(__file__).resolve().parents[1], allowed=ALLOWED))
