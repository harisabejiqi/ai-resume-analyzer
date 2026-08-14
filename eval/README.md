# Evaluation harness — TF-IDF vs SBERT

This directory turns the resume↔job-description matcher into something an
examiner can scrutinise: a **labeled gold set** plus a harness that scores it
with both matching methods and reports metrics with confidence intervals and a
significance test. It evaluates the *production* code in `app/services`, so the
numbers describe what the app actually deploys.

## Run it

From the repository root:

```bash
pip install -r requirements.txt        # adds scipy + matplotlib
python -m eval.run_eval                # writes eval/results/comparison.{md,csv} + plots
python -m eval.run_eval --no-plots     # skip the figures
```

First run downloads the SBERT model (~90 MB), then caches it. If
`sentence-transformers` can't load, the harness still runs the lexical methods
and prints a warning.

## What it measures

Three metric families (see `metrics.py` for the rationale of each):

| Family | Metric | Question it answers |
|---|---|---|
| Correlation | Spearman ρ, Pearson r | Does the predicted score track the human grade? |
| Ranking | NDCG@3, MRR (per resume) | As a retrieval task, are the right jobs ranked first? |
| Calibration | mean score per grade | Does grade-0 actually score ≈0, or does SBERT compress everything into 30–60%? |

Every figure comes with a **95% bootstrap CI**, and `sbert` is compared to the
lexical baselines with a **paired Wilcoxon signed-rank test** on per-query NDCG.

Methods evaluated:
- `tfidf` — the production `calculate_tfidf_match_score` (fits IDF on just the
  two documents, so IDF is degenerate — effectively TF cosine).
- `tfidf_corpus` — a "proper" lexical baseline with IDF fit over the whole
  corpus. The gap between the two is itself a finding worth a paragraph.
- `sbert` — the production `embeddings.semantic_similarity` (MiniLM cosine).

## The dataset

Documents live as plain text, labels as a CSV, so nothing is duplicated:

```
data/
  resumes/<resume_id>.txt
  jobs/<job_id>.txt
  labels.csv          # resume_id,job_id,relevance   (one row per pair)
```

`relevance` is an ordinal grade:

- **2** — strong fit (same field)
- **1** — partial fit (adjacent field with real overlap, e.g. backend ↔ data science)
- **0** — no fit (unrelated)

### Why this labeling scheme is defensible

The gold set is a **field × field matrix**. Most labels are objective by
construction ("backend résumé vs nurse posting = 0" is not a judgment call),
which is what makes a small hand-labeled set more trustworthy than a noisy
scrape. The **grade-1 (partial-fit) cells are the discriminating cases** — that
is where a semantic method should beat a lexical one, because the overlap is in
*meaning*, not shared words. That contrast is your headline result.

The current set is a **6×6 matrix** (backend, data science, frontend, DevOps,
accounting, nursing) = 36 labeled pairs: 6 strong fits (grade 2), 7 partial
fits (grade 1), 23 no-fits (grade 0). Note that with one clear strong-fit job
per résumé, the ranking task is saturated (all methods hit NDCG@3 = 1.0) — the
discriminating signal is in correlation and calibration, not ranking.

### Expanding it further

1. Add more fields, or a second résumé per field with a *less* prototypical
   writing style — that would un-saturate the ranking metrics. Drop new `.txt`
   files in `resumes/` and `jobs/` and add their pairs to `labels.csv`.
   Good additional fields: marketing, teaching, law.
2. Keep the matrix design: one strong-fit job per résumé, a couple of
   partial-fit neighbours, the rest no-fit.
3. **Own the labels.** For academic integrity, you (and ideally a second
   annotator) assign the grades — record who labeled and report inter-annotator
   agreement (e.g. Cohen's κ) in the thesis if you use two annotators.
4. Document provenance in the thesis: where each document came from (written by
   you, public Kaggle Resume Dataset, anonymised real CVs with consent) and any
   licensing.

### Reproducibility

All randomness (bootstrap, jitter) is seeded via `--seed` (default 42), so reruns
are identical. Pin the dependency versions in `requirements.txt` before the final
run and record them in the thesis.

## Outputs (→ thesis figures)

`eval/results/` after a run:
- `comparison.md` / `comparison.csv` — the headline + calibration tables.
- `calibration.png` — mean predicted score per grade, per method (the SBERT
  compression story).
- `scatter.png` — predicted score vs human grade.
- `ndcg.png` — NDCG@3 per method with 95% CI error bars.

## Easy extensions

- **BM25** as a third lexical baseline (`pip install rank-bm25`) — add it to
  `build_methods()`.
- **Per-job queries** as well as per-résumé (pass `group_key="job_id"` to the
  ranking metrics) — ranking candidates for a posting is the recruiter framing.
- An **ablation** of the weighted-score formula in `scorer.py` (skills-only vs
  +education vs +experience vs +relevance) reuses this same harness structure.
