"""Evaluation metrics for resume--JD matching.

Three families, each answering a different question about a scoring method:

  * Correlation  -- does the predicted score track the human relevance grade?
                    (Spearman rho, Pearson r, pooled over all pairs)
  * Ranking      -- treated as retrieval: for each resume, rank the jobs.
                    (NDCG@k and MRR, computed per query then averaged)
  * Calibration  -- what score does each relevance grade actually receive?
                    (mean predicted score per grade -- exposes the SBERT
                    cosine-compression problem where unrelated pairs still
                    score ~30-40%)

Uncertainty is reported as 95% bootstrap confidence intervals, and two methods
are compared with a paired Wilcoxon signed-rank test on per-query NDCG. All
randomness is seeded so results are reproducible.
"""

from collections import defaultdict

import numpy as np
from scipy.stats import pearsonr, spearmanr, wilcoxon
from sklearn.metrics import ndcg_score


def _stat_p(res):
    """Pull (statistic, p-value) from a scipy result across scipy versions."""
    try:
        return float(res.statistic), float(res.pvalue)
    except AttributeError:
        return float(res[0]), float(res[1])


def group_by(pairs, key):
    """Group a list of pair-dicts by the value of `key` (preserves insertion order)."""
    groups = defaultdict(list)
    for p in pairs:
        groups[p[key]].append(p)
    return groups



def spearman(y_true, y_pred):
    return _stat_p(spearmanr(y_true, y_pred))


def pearson(y_true, y_pred):
    return _stat_p(pearsonr(y_true, y_pred))



def per_query_ndcg(pairs, method, group_key="resume_id", k=3):
    """NDCG@k for each query (default: each resume ranks the jobs).

    Returns {query_id: ndcg}. Queries with fewer than two candidates, or with
    no relevant candidate (all grades 0), are skipped -- NDCG is undefined there.
    """
    out = {}
    for qid, items in group_by(pairs, group_key).items():
        rels = [it["relevance"] for it in items]
        if len(items) < 2 or max(rels) == 0:
            continue
        true = np.array([rels], dtype=float)
        pred = np.array([[it[method] for it in items]], dtype=float)
        out[qid] = float(ndcg_score(true, pred, k=min(k, len(items))))
    return out


def per_query_mrr(pairs, method, group_key="resume_id", relevant_threshold=2):
    """Mean reciprocal rank of the first strongly-relevant job per resume.

    Returns {query_id: reciprocal_rank}. A query with no item at or above
    `relevant_threshold` is skipped.
    """
    out = {}
    for qid, items in group_by(pairs, group_key).items():
        ranked = sorted(items, key=lambda it: it[method], reverse=True)
        rank = next(
            (i + 1 for i, it in enumerate(ranked) if it["relevance"] >= relevant_threshold),
            None,
        )
        if rank is not None:
            out[qid] = 1.0 / rank
    return out



def calibration(pairs, method):
    """Mean +/- std of the predicted score within each relevance grade."""
    out = {}
    for grade, items in sorted(group_by(pairs, "relevance").items()):
        vals = np.array([it[method] for it in items], dtype=float)
        out[grade] = (float(vals.mean()), float(vals.std()), len(vals))
    return out


def target_score(relevance, max_grade):
    """The ideal calibrated score for a relevance grade: 0 -> 0, max -> 100."""
    return relevance / max_grade * 100.0


def calibration_error(pairs, method, max_grade=None):
    """Mean absolute error between predicted scores and the ideal per-grade score.

    Lower is better-calibrated. A perfectly calibrated method puts grade 0 at 0,
    the top grade at 100, and intermediate grades evenly between.
    """
    if max_grade is None:
        max_grade = max(p["relevance"] for p in pairs)
    if max_grade == 0:
        return float("nan")
    errs = [abs(p[method] - target_score(p["relevance"], max_grade)) for p in pairs]
    return sum(errs) / len(errs)



def bootstrap_ci(values, n=2000, seed=42, alpha=0.05):
    """Percentile bootstrap CI for the mean of a list of per-query values."""
    values = [v for v in values if v is not None and not np.isnan(v)]
    if not values:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = rng.choice(arr, size=(n, arr.size), replace=True).mean(axis=1)
    return (
        float(np.percentile(means, 100 * alpha / 2)),
        float(np.percentile(means, 100 * (1 - alpha / 2))),
    )


def bootstrap_corr_ci(y_true, y_pred, coef_fn, n=2000, seed=42, alpha=0.05):
    """Percentile bootstrap CI for a correlation coefficient (resamples pairs).

    `coef_fn(a, b)` must return just the coefficient (e.g. lambda a, b: spearman(a, b)[0]).
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    rng = np.random.default_rng(seed)
    idx = np.arange(yt.size)
    vals = []
    for _ in range(n):
        s = rng.choice(idx, size=idx.size, replace=True)
        if np.unique(yt[s]).size < 2 or np.unique(yp[s]).size < 2:
            continue
        c = coef_fn(yt[s], yp[s])
        if not np.isnan(c):
            vals.append(c)
    if not vals:
        return (float("nan"), float("nan"))
    return (
        float(np.percentile(vals, 100 * alpha / 2)),
        float(np.percentile(vals, 100 * (1 - alpha / 2))),
    )


def align(dict_a, dict_b):
    """Two per-query dicts -> two lists over their shared queries, in a stable order."""
    keys = [k for k in dict_a if k in dict_b]
    return [dict_a[k] for k in keys], [dict_b[k] for k in keys]


def paired_wilcoxon(per_query_a, per_query_b):
    """Paired Wilcoxon signed-rank p-value over shared queries, or None if N/A.

    Tests H0: the two methods' per-query NDCG come from the same distribution.
    """
    a, b = align(per_query_a, per_query_b)
    if len(a) < 1:
        return None
    diffs = np.asarray(a) - np.asarray(b)
    if np.all(diffs == 0):
        return 1.0
    try:
        return _stat_p(wilcoxon(a, b))[1]
    except ValueError:
        return None
