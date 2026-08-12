"""Calibration of the raw semantic relevance score.

The semantic matcher (embeddings.py) returns a cosine similarity scaled to
0-100. Raw sentence-transformer cosines are *not* calibrated probabilities:
for this model two unrelated professional documents still sit around 15-20,
and even a strong match rarely exceeds ~75. So a raw "47% match" badly
understates a genuinely good fit, and a raw "18%" overstates an unrelated one.

This module applies a fitted **logistic (Platt-style) mapping** that stretches
the score onto an interpretable 0-100 scale where unrelated pairs sit near 0
and strong matches near 100. The mapping is *strictly monotonic*, so it leaves
the ranking of any set of candidates unchanged (Spearman / NDCG / MRR are
invariant) — it only changes the absolute, human-facing number.

Parameters are fit offline against the labeled gold set by `eval/calibrate.py`
and stored in `calibration_params.json`. If that file is absent or unreadable,
calibration is the identity, so the app still works (uncalibrated) out of the box.
"""

import json
import math
import os

_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "calibration_params.json")
_IDENTITY = {"method": "identity"}


def _load_params():
    try:
        with open(_PARAMS_PATH, encoding="utf-8") as f:
            params = json.load(f)
        if params.get("method") in ("identity", "logistic", "affine"):
            return params
    except (FileNotFoundError, ValueError, OSError):
        pass
    return _IDENTITY



_params = _load_params()


def is_fitted():
    """True if a non-identity calibration has been fit and loaded."""
    return _params.get("method") != "identity"


def _logistic(z):
    """Numerically stable logistic; avoids overflow for large |z|."""
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def calibrate(score_0_100):
    """Map a raw semantic score (0-100) to a calibrated score (0-100).

    Identity when no parameters are loaded. The transform is monotonic, so it
    never reorders candidates — see the module docstring.
    """
    p = _params
    method = p.get("method")

    if method == "logistic":
        x = score_0_100 / 100.0
        return round(100.0 * _logistic(p["k"] * (x - p["x0"])), 2)

    if method == "affine":
        x = score_0_100 / 100.0
        v = (x - p["lo"]) / (p["hi"] - p["lo"])
        return round(100.0 * min(1.0, max(0.0, v)), 2)

    return score_0_100  
