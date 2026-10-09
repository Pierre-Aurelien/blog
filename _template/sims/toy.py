"""Toy: the spread of the mean of n standard normal draws.

Writes results.json["toy"]: the measured standard deviation of the mean for
each n in NS, the 1/sqrt(n) prediction, and how many draws halve the spread
from N_REF. Replace with the post's own toy.
"""

import sys
from pathlib import Path

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "_quarto.yml").exists())
sys.path.insert(0, str(ROOT / "shared"))
from simtools import save_results  # noqa: E402

SEED = 20261009
REPS = 20_000
NS = [1, 4, 16, 64]
N_REF = 16


def spread_of_mean(n: int, rng: np.random.Generator) -> float:
    means = rng.standard_normal((REPS, n)).mean(axis=1)
    return float(means.std(ddof=1))


def main() -> None:
    rng = np.random.default_rng(SEED)
    sd = {str(n): spread_of_mean(n, rng) for n in NS}
    theory = {str(n): 1 / np.sqrt(n) for n in NS}
    n_half = N_REF * 4  # 1/sqrt(4 n) = (1/2) (1/sqrt(n))
    save_results("toy", {
        "reps": REPS,
        "ns": NS,
        "n_ref": N_REF,
        "sd": sd,
        "theory": theory,
        "n_half": n_half,
        "ratio_ref_half": sd[str(N_REF)] / sd[str(n_half)],
        "max_rel_dev": max(abs(sd[k] / theory[k] - 1) for k in sd),
    })


if __name__ == "__main__":
    main()
