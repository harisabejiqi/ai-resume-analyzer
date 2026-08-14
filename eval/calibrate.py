"""Fit and evaluate calibration of the SBERT relevance score.

    python -m eval.calibrate            # fit, evaluate (LOO-CV), write params + report
    python -m eval.calibrate --no-write # evaluate only, don't overwrite shipped params

Fits a logistic (Platt-style) mapping  s -> 100 * sigmoid(k * (s/100 - x0))  from
the raw SBERT score to the gold relevance grade, so unrelated pairs land near 0
and strong matches near 100. Because the mapping is strictly monotonic, the
ranking of candidates is unchanged -- the harness verifies this by showing
identical NDCG/Spearman before and after.

Honesty: the per-grade table fit on all pairs is in-sample. We therefore also
report a **leave-one-out cross-validated** calibration error -- each pair is
scored by parameters fit without it -- so the reported improvement isn't just
the model memorising the gold set.
"""

import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from scipy.optimize import curve_fit

from app.services import embeddings
from eval import metrics
from eval.run_eval import DEFAULT_DATA, DEFAULT_OUT, load_pairs

PARAMS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "services", "calibration_params.json",
)


def _logistic(x, x0, k):
    z = np.clip(-k * (x - x0), -700.0, 700.0)
    return 1.0 / (1.0 + np.exp(z))


def fit_logistic(raw_scores, relevances, max_grade):
    """Fit (x0, k) mapping raw score (0-100) -> grade fraction in [0, 1]."""
    x = np.asarray(raw_scores, dtype=float) / 100.0
    y = np.asarray(relevances, dtype=float) / max_grade
    popt, _ = curve_fit(_logistic, x, y, p0=[float(x.mean()), 10.0], maxfev=20000)
    return {"method": "logistic", "x0": float(popt[0]), "k": float(popt[1])}


def apply_logistic(raw_score, params):
    return 100.0 * float(_logistic(raw_score / 100.0, params["x0"], params["k"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--no-write", action="store_true",
                    help="evaluate only; do not overwrite the shipped params file")
    args = ap.parse_args()

    if not embeddings.is_available():
        raise SystemExit("SBERT model unavailable -- cannot fit calibration.")

    os.makedirs(args.out, exist_ok=True)
    pairs = load_pairs(args.data_dir)
    max_grade = max(p["relevance"] for p in pairs)

    for p in pairs:
        p["sbert"] = float(embeddings.semantic_similarity(p["resume_text"], p["job_text"]))

    params = fit_logistic([p["sbert"] for p in pairs],
                          [p["relevance"] for p in pairs], max_grade)
    for p in pairs:
        p["sbert_cal"] = apply_logistic(p["sbert"], params)

    for i, p in enumerate(pairs):
        rest = pairs[:i] + pairs[i + 1:]
        loo = fit_logistic([q["sbert"] for q in rest],
                           [q["relevance"] for q in rest], max_grade)
        p["sbert_cal_loo"] = apply_logistic(p["sbert"], loo)

    cal_err_raw = metrics.calibration_error(pairs, "sbert", max_grade)
    cal_err_fit = metrics.calibration_error(pairs, "sbert_cal", max_grade)
    cal_err_loo = metrics.calibration_error(pairs, "sbert_cal_loo", max_grade)

    y = [p["relevance"] for p in pairs]
    ndcg_raw = sum(metrics.per_query_ndcg(pairs, "sbert").values())
    ndcg_cal = sum(metrics.per_query_ndcg(pairs, "sbert_cal").values())
    rho_raw = metrics.spearman(y, [p["sbert"] for p in pairs])[0]
    rho_cal = metrics.spearman(y, [p["sbert_cal"] for p in pairs])[0]

    report = _render(pairs, params, max_grade,
                     cal_err_raw, cal_err_fit, cal_err_loo,
                     ndcg_raw, ndcg_cal, rho_raw, rho_cal)
    print("\n" + report)

    report_path = os.path.join(args.out, "calibration_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote {report_path}")

    if args.no_write:
        print("--no-write: shipped calibration_params.json left unchanged.")
    else:
        with open(PARAMS_PATH, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        print(f"Wrote {PARAMS_PATH}  (restart the Flask app to apply)")

    _plot(pairs, params, max_grade, args.out)


def _render(pairs, params, max_grade, err_raw, err_fit, err_loo,
            ndcg_raw, ndcg_cal, rho_raw, rho_cal):
    grades = sorted({p["relevance"] for p in pairs})
    cal_raw = metrics.calibration(pairs, "sbert")
    cal_new = metrics.calibration(pairs, "sbert_cal")

    out = ["# Calibration of the SBERT relevance score\n"]
    out.append(f"Fitted logistic mapping: `100 * sigmoid(k * (s/100 - x0))` "
               f"with **x0 = {params['x0']:.3f}**, **k = {params['k']:.2f}** "
               f"(s = raw score). Strictly monotonic.\n")

    out.append("## Mean predicted score per relevance grade\n")
    out.append("| Grade | ideal | raw SBERT | calibrated |")
    out.append("|---|---|---|---|")
    for g in grades:
        ideal = metrics.target_score(g, max_grade)
        out.append(f"| {g} | {ideal:.0f} | {cal_raw[g][0]:.1f} ± {cal_raw[g][1]:.1f} "
                   f"| {cal_new[g][0]:.1f} ± {cal_new[g][1]:.1f} |")
    out.append("")

    out.append("## Calibration error (mean abs. deviation from ideal, lower=better)\n")
    out.append(f"- raw SBERT:                 **{err_raw:.1f}**")
    out.append(f"- calibrated (fit on all):   **{err_fit:.1f}**  *(in-sample)*")
    out.append(f"- calibrated (leave-one-out): **{err_loo:.1f}**  *(honest, cross-validated)*\n")

    out.append("## Ranking is unchanged (the mapping is monotonic)\n")
    out.append(f"- Spearman rho:  raw {rho_raw:.3f}  ->  calibrated {rho_cal:.3f}")
    out.append(f"- Sum of per-query NDCG@3:  raw {ndcg_raw:.3f}  ->  calibrated {ndcg_cal:.3f}\n")
    out.append("> Identical by construction: a strictly increasing transform cannot "
               "reorder candidates, so all rank-based metrics are invariant. Only the "
               "absolute, human-facing score changes.\n")
    return "\n".join(out)


def _plot(pairs, params, max_grade, outdir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed -- skipping calibration plot.")
        return

    fig, ax = plt.subplots(figsize=(7, 4.5))
    xs = np.linspace(0, 100, 200)
    ys = [apply_logistic(x, params) for x in xs]
    ax.plot(xs, ys, color="C0", label="fitted logistic")
    ax.plot([0, 100], [0, 100], "--", color="grey", alpha=0.6, label="identity (raw)")

    colors = {g: f"C{g + 1}" for g in sorted({p['relevance'] for p in pairs})}
    for p in pairs:
        ax.scatter(p["sbert"], apply_logistic(p["sbert"], params),
                   color=colors[p["relevance"]], s=40, zorder=3)
    for g, c in colors.items():
        ax.scatter([], [], color=c, label=f"grade {g}")
        ax.axhline(metrics.target_score(g, max_grade), color=c, alpha=0.25, ls=":")

    ax.set_xlabel("Raw SBERT score")
    ax.set_ylabel("Calibrated score")
    ax.set_title("Calibration mapping (dotted lines = ideal per-grade target)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(outdir, "calibration_mapping.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
