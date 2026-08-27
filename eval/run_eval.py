"""Run the TF-IDF vs SBERT comparison and write the results table + plots.

    python -m eval.run_eval                 # uses eval/data, writes eval/results
    python -m eval.run_eval --no-plots      # skip matplotlib figures
    python -m eval.run_eval --data-dir path --out path

The harness evaluates the *production* scoring code imported from app.services,
so the thesis reports on what the app actually deploys -- not a reimplementation.
"""

import argparse
import csv
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from scipy.optimize import curve_fit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services import chunking, embeddings
from app.services.scorer import calculate_tfidf_match_score
from eval import metrics

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "data")
DEFAULT_OUT = os.path.join(HERE, "results")



def _read_docs(folder):
    docs = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith(".txt"):
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                docs[name[:-4]] = f.read().strip()
    return docs


def load_pairs(data_dir):
    """Load resumes, jobs, and the labels.csv into a flat list of pair-dicts."""
    resumes = _read_docs(os.path.join(data_dir, "resumes"))
    jobs = _read_docs(os.path.join(data_dir, "jobs"))
    pairs = []
    with open(os.path.join(data_dir, "labels.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rid, jid = row["resume_id"].strip(), row["job_id"].strip()
            if rid not in resumes:
                raise SystemExit(f"labels.csv references missing resume '{rid}'")
            if jid not in jobs:
                raise SystemExit(f"labels.csv references missing job '{jid}'")
            pairs.append({
                "resume_id": rid,
                "job_id": jid,
                "relevance": int(row["relevance"]),
                "resume_text": resumes[rid],
                "job_text": jobs[jid],
            })
    if not pairs:
        raise SystemExit("No labeled pairs found in labels.csv.")
    return pairs



def _make_corpus_tfidf(pairs):
    """A 'proper' lexical baseline: TF-IDF with IDF fit over the whole corpus.

    The production `calculate_tfidf_match_score` fits on just the two documents,
    making IDF degenerate (effectively TF cosine). Reporting both exposes that
    gap as a finding rather than hiding it.
    """
    order, index = [], {}
    for p in pairs:
        for kind, _id, txt in (
            ("r", p["resume_id"], p["resume_text"]),
            ("j", p["job_id"], p["job_text"]),
        ):
            if (kind, _id) not in index:
                index[(kind, _id)] = len(order)
                order.append(txt)
    matrix = TfidfVectorizer(stop_words="english").fit_transform(order)

    def score(p):
        ri, ji = index[("r", p["resume_id"])], index[("j", p["job_id"])]
        return float(cosine_similarity(matrix[ri], matrix[ji])[0][0]) * 100

    return score


def build_methods(pairs):
    """Map of method name -> function(pair) -> score in [0, 100]."""
    methods = {
        "tfidf": lambda p: calculate_tfidf_match_score(p["resume_text"], p["job_text"]),
        "tfidf_corpus": _make_corpus_tfidf(pairs),
    }
    if embeddings.is_available():
        methods["sbert"] = lambda p: embeddings.semantic_similarity(
            p["resume_text"], p["job_text"]
        )
        methods["sbert_chunk"] = lambda p: chunking.chunked_similarity(
            p["resume_text"], p["job_text"]
        )

        from app.services import calibration
        base = calibration.fitted_for() or "sbert"
        if calibration.is_fitted() and base in methods:
            scorer_fn = methods[base]
            methods[base + "_cal_shipped"] = lambda p, f=scorer_fn: calibration.calibrate(f(p))
        elif calibration.is_fitted():
            print(f"NOTE: shipped calibration was fit for '{base}', which is not among "
                  f"the evaluated methods -- skipping the shipped-calibration row.\n")
    else:
        print("WARNING: SBERT model unavailable (library/weights missing) -- "
              "skipping the semantic method.\n")
    return methods



def _logistic_pct(x, k, x0):
    return 100.0 / (1.0 + np.exp(-k * (np.asarray(x, dtype=float) / 100.0 - x0)))


def _loo_calibrated(pairs, name, max_grade=2):
    """Leave-one-out logistic calibration of `name`, as a list aligned to `pairs`.

    Each pair is scored by parameters fit on the *other* pairs, so the calibrated
    column is out-of-sample rather than fit on what it scores. Methods live on
    very different raw scales (corpus TF-IDF spans ~0-25, chunked SBERT ~20-60),
    so calibrating both onto the human-grade scale is what makes a blend of the
    two meaningful rather than a silent weighting by scale.
    """
    raw = np.array([p[name] for p in pairs], dtype=float)
    target = np.array(
        [metrics.target_score(p["relevance"], max_grade) for p in pairs], dtype=float
    )
    out = []
    for i in range(len(pairs)):
        mask = np.ones(len(pairs), dtype=bool)
        mask[i] = False
        try:
            popt, _ = curve_fit(
                _logistic_pct, raw[mask], target[mask], p0=[10.0, 0.4], maxfev=20000
            )
            out.append(float(_logistic_pct(raw[i], *popt)))
        except (RuntimeError, ValueError):
            out.append(float(raw[i]))
    return out


def add_ablation_methods(pairs, methods, weight=0.5):
    """Add calibrated + hybrid rows, in place, after the base methods are scored.

    `hybrid` is a convex blend of the calibrated corpus-TF-IDF and calibrated
    chunked-SBERT scores. Both inputs are on the calibrated 0-100 grade scale, so
    `weight` is a genuine lexical/semantic trade-off rather than an artefact of
    the two methods' raw ranges.
    """
    added = []
    for base in ("tfidf_corpus", "sbert_chunk"):
        if base in methods:
            for p, v in zip(pairs, _loo_calibrated(pairs, base)):
                p[base + "_cal"] = round(v, 2)
            added.append(base + "_cal")

    if {"tfidf_corpus_cal", "sbert_chunk_cal"} <= set(added):
        for p in pairs:
            p["hybrid"] = round(
                weight * p["tfidf_corpus_cal"] + (1 - weight) * p["sbert_chunk_cal"], 2
            )
        added.append("hybrid")

    for name in added:
        methods[name] = None
    return added


def score_pairs(pairs, methods):
    for name, fn in methods.items():
        if fn is None:
            continue
        for p in pairs:
            p[name] = float(fn(p))



def _fmt(value, lo, hi):
    if value != value:
        return "n/a"
    return f"{value:.3f} [{lo:.3f}, {hi:.3f}]"


def compute_report(pairs, methods, seed=42):
    y_true = [p["relevance"] for p in pairs]
    rows, per_query_ndcg = {}, {}
    for name in methods:
        y_pred = [p[name] for p in pairs]

        rho, rho_p = metrics.spearman(y_true, y_pred)
        r, r_p = metrics.pearson(y_true, y_pred)
        rho_ci = metrics.bootstrap_corr_ci(y_true, y_pred, lambda a, b: metrics.spearman(a, b)[0], seed=seed)
        r_ci = metrics.bootstrap_corr_ci(y_true, y_pred, lambda a, b: metrics.pearson(a, b)[0], seed=seed)

        ndcg = metrics.per_query_ndcg(pairs, name)
        mrr = metrics.per_query_mrr(pairs, name)
        per_query_ndcg[name] = ndcg
        ndcg_mean = sum(ndcg.values()) / len(ndcg) if ndcg else float("nan")
        mrr_mean = sum(mrr.values()) / len(mrr) if mrr else float("nan")

        rows[name] = {
            "spearman": (rho, rho_p, rho_ci),
            "pearson": (r, r_p, r_ci),
            "ndcg": (ndcg_mean, metrics.bootstrap_ci(list(ndcg.values()), seed=seed)),
            "mrr": (mrr_mean, metrics.bootstrap_ci(list(mrr.values()), seed=seed)),
            "calibration": metrics.calibration(pairs, name),
        }
    return rows, per_query_ndcg


def render_markdown(pairs, methods, rows, per_query_ndcg):
    n_pairs = len(pairs)
    n_queries = len({p["resume_id"] for p in pairs})
    grades = sorted({p["relevance"] for p in pairs})

    out = []
    out.append("# TF-IDF vs SBERT -- resume/JD matching evaluation\n")
    out.append(f"Gold set: **{n_pairs} labeled pairs**, {n_queries} resumes (queries), "
               f"relevance grades {grades}. 95% bootstrap CIs in brackets.\n")

    out.append("## Headline metrics\n")
    out.append("| Method | Spearman rho | Pearson r | NDCG@3 | MRR |")
    out.append("|---|---|---|---|---|")
    for name in methods:
        m = rows[name]
        out.append(
            f"| `{name}` "
            f"| {_fmt(m['spearman'][0], *m['spearman'][2])} "
            f"| {_fmt(m['pearson'][0], *m['pearson'][2])} "
            f"| {_fmt(m['ndcg'][0], *m['ndcg'][1])} "
            f"| {_fmt(m['mrr'][0], *m['mrr'][1])} |"
        )
    out.append("")

    out.append("## Calibration -- mean predicted score per relevance grade\n")
    out.append("Well-calibrated = grade 0 near 0, rising monotonically with grade.\n")
    header = "| Method | " + " | ".join(f"grade {g}" for g in grades) + " |"
    out.append(header)
    out.append("|" + "---|" * (len(grades) + 1))
    for name in methods:
        cal = rows[name]["calibration"]
        cells = []
        for g in grades:
            if g in cal:
                mean, std, _ = cal[g]
                cells.append(f"{mean:.1f} ± {std:.1f}")
            else:
                cells.append("--")
        out.append(f"| `{name}` | " + " | ".join(cells) + " |")
    out.append("")

    out.append("## Calibration error (mean |predicted - grade target|, lower is better)\n")
    out.append("| Method | calibration error |")
    out.append("|---|---|")
    for name in methods:
        out.append(f"| `{name}` | {metrics.calibration_error(pairs, name):.2f} |")
    out.append("")

    out.extend(_render_significance(methods, per_query_ndcg))

    return "\n".join(out)


_COMPARISONS = [
    ("tfidf_corpus", "tfidf", "does corpus-fit IDF beat the shipped two-document fit?"),
    ("sbert", "tfidf_corpus", "does whole-document semantic matching beat the lexical baseline?"),
    ("sbert_chunk", "sbert", "does section/requirement-level chunking beat whole-document?"),
    ("sbert_chunk", "tfidf_corpus", "does chunked semantic matching beat the lexical baseline?"),
    ("hybrid", "tfidf_corpus_cal", "does adding a semantic component beat calibrated lexical alone?"),
    ("hybrid", "sbert_chunk_cal", "does adding a lexical component beat calibrated chunked alone?"),
]


def _render_significance(methods, per_query_ndcg):
    """The paired-Wilcoxon table: every comparison the ablation is meant to settle.

    Reported on per-query NDCG@3, so the unit of analysis is a resume ranking the
    jobs. `n` is the number of queries the test actually used -- queries with no
    relevant job are undefined for NDCG and are excluded, so `n` can be below the
    gold set's query count.
    """
    usable = [(a, b, q) for a, b, q in _COMPARISONS if a in methods and b in methods]
    if not usable:
        return []

    n_queries = len(next(iter(per_query_ndcg.values()))) if per_query_ndcg else 0
    out = ["## Significance (paired Wilcoxon on per-query NDCG@3)\n"]
    out.append(f"Tested over {n_queries} queries. `*` marks p < 0.05. The test is "
               "two-sided, so read `dNDCG` for the direction: it is method A's mean "
               "NDCG@3 minus method B's, over the queries the test used.\n")
    out.append("| Comparison | dNDCG | p | | Question |")
    out.append("|---|---|---|---|---|")
    for a, b, question in usable:
        p = metrics.paired_wilcoxon(per_query_ndcg[a], per_query_ndcg[b])
        va, vb = metrics.align(per_query_ndcg[a], per_query_ndcg[b])
        delta = (sum(va) / len(va) - sum(vb) / len(vb)) if va else float("nan")
        p_str = "n/a" if p is None else f"{p:.4f}"
        star = "*" if p is not None and p < 0.05 else ""
        out.append(f"| `{a}` vs `{b}` | {delta:+.3f} | {p_str} | {star} | {question} |")
    out.append("")
    out.append("> A non-significant result is not evidence of no effect: at this gold-set "
               "size the test only resolves fairly large differences. Note also that the "
               "labels themselves drive these outcomes -- see eval/README.md on the grading "
               "rule before quoting any p-value.\n")
    return out


def write_csv(path, methods, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "spearman", "spearman_p", "pearson", "pearson_p", "ndcg@3", "mrr"])
        for name in methods:
            m = rows[name]
            w.writerow([
                name,
                f"{m['spearman'][0]:.4f}", f"{m['spearman'][1]:.4f}",
                f"{m['pearson'][0]:.4f}", f"{m['pearson'][1]:.4f}",
                f"{m['ndcg'][0]:.4f}", f"{m['mrr'][0]:.4f}",
            ])



def make_plots(pairs, methods, rows, outdir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed -- skipping plots "
              "(pip install matplotlib to enable).")
        return

    grades = sorted({p["relevance"] for p in pairs})
    names = list(methods)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    width = 0.8 / len(names)
    for i, name in enumerate(names):
        cal = rows[name]["calibration"]
        means = [cal[g][0] if g in cal else 0 for g in grades]
        errs = [cal[g][1] if g in cal else 0 for g in grades]
        x = [g + (i - (len(names) - 1) / 2) * width for g in grades]
        ax.bar(x, means, width=width, yerr=errs, capsize=3, label=name)
    ax.set_xticks(grades)
    ax.set_xlabel("Human relevance grade")
    ax.set_ylabel("Mean predicted score (0-100)")
    ax.set_title("Calibration: predicted score by relevance grade")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "calibration.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    rng = __import__("numpy").random.default_rng(0)
    for name in names:
        jitter = rng.uniform(-0.12, 0.12, size=len(pairs))
        ax.scatter([p["relevance"] for p in pairs] + jitter,
                   [p[name] for p in pairs], alpha=0.7, label=name)
    ax.set_xticks(grades)
    ax.set_xlabel("Human relevance grade (jittered)")
    ax.set_ylabel("Predicted score (0-100)")
    ax.set_title("Predicted score vs human relevance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "scatter.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    means = [rows[n]["ndcg"][0] for n in names]
    los = [rows[n]["ndcg"][0] - rows[n]["ndcg"][1][0] for n in names]
    his = [rows[n]["ndcg"][1][1] - rows[n]["ndcg"][0] for n in names]
    ax.bar(range(len(names)), means, yerr=[los, his], capsize=4)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names)
    ax.set_ylabel("NDCG@3")
    ax.set_ylim(0, 1.05)
    ax.set_title("Ranking quality (NDCG@3) with 95% bootstrap CI")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "ndcg.png"), dpi=150)
    plt.close(fig)

    print(f"Plots written to {outdir}/ (calibration.png, scatter.png, ndcg.png)")



def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--hybrid-weight", type=float, default=0.5,
                    help="weight on calibrated corpus TF-IDF in the hybrid (0-1)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    pairs = load_pairs(args.data_dir)
    print(f"Loaded {len(pairs)} labeled pairs "
          f"({len({p['resume_id'] for p in pairs})} resumes x "
          f"{len({p['job_id'] for p in pairs})} jobs).")

    methods = build_methods(pairs)
    print("Scoring with:", ", ".join(methods), "...")
    score_pairs(pairs, methods)

    derived = add_ablation_methods(pairs, methods, weight=args.hybrid_weight)
    if derived:
        print("Ablation rows (LOO-calibrated):", ", ".join(derived))

    rows, per_query_ndcg = compute_report(pairs, methods, seed=args.seed)
    report = render_markdown(pairs, methods, rows, per_query_ndcg)

    md_path = os.path.join(args.out, "comparison.md")
    csv_path = os.path.join(args.out, "comparison.csv")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)
    write_csv(csv_path, methods, rows)

    print("\n" + report)
    print(f"\nWrote {md_path}\nWrote {csv_path}")

    if not args.no_plots:
        make_plots(pairs, methods, rows, args.out)


if __name__ == "__main__":
    main()
