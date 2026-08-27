# Evaluation harness: lexical vs semantic resume/JD matching

This directory turns the resume↔job-description matcher into something an
examiner can scrutinise: a **labeled gold set** plus a harness that scores it
with every matching method and reports metrics with confidence intervals and
significance tests. It evaluates the *production* code in `app/services`, so the
numbers describe what the app actually deploys.

## Run it

From the repository root:

```bash
pip install -r requirements.txt        # adds scipy + matplotlib
python -m eval.run_eval                # writes eval/results/comparison.{md,csv} + plots
python -m eval.run_eval --no-plots     # skip the figures
python -m eval.run_eval --out DIR      # write elsewhere (keeps a previous run intact)
python -m eval.run_extraction          # separate: field-extraction precision/recall/F1
```

First run downloads the SBERT model (~90 MB), then caches it. If
`sentence-transformers` can't load, the harness still runs the lexical methods
and prints a warning.

## The dataset

Documents live as plain text, labels as a CSV, so nothing is duplicated:

```
data/
  resumes/<resume_id>.txt
  jobs/<job_id>.txt
  labels.csv          # resume_id,job_id,relevance   (one row per pair)
```

**Current size: 27 resumes × 9 job descriptions = 243 labeled pairs**
(196 grade-0, 25 grade-1, 22 grade-2).

Job families: backend (generic, Java-specific, and senior variants), data
science, ML engineering, frontend, DevOps, accounting, nursing.

Every document was written for this thesis. None is a real CV and none contains
real personal data, so there are no consent or licensing constraints. Equally,
though, the results do not transfer automatically to real-world documents, which
are messier.

### The grading rule

`relevance` is an ordinal grade, applied to the candidate against the posting:

- **2, strong fit.** Realistically qualified for the role *now*.
- **1, partial fit.** Adjacent profile with substantial transferable evidence,
  but missing an important stated requirement.
- **0, no meaningful fit.** Superficial overlap only, or the wrong profession.

The critical discipline is that grade 1 does not mean "shares some technical
vocabulary". A backend engineer is not a partial fit for a data-science role
because both write Python, and a Jenkins user is not a partial fit for a platform
role that wants Terraform and Kubernetes in production. Grade 1 requires genuine
transferable evidence: a data analyst moving toward data science, a healthcare
assistant against a nursing post, a four-year Java engineer against a Python
backend role.

Grades are assigned from the documents alone, and never adjusted because a
particular method scores better with them. Label decisions must be signed off by
the author before publication; for a stronger claim, add a second annotator and
report Cohen's κ.

### Why the set is shaped this way

The gold set is deliberately *not* a clean one-CV-one-job matrix, because that
shape saturates the ranking metrics. An earlier 6×6 version gave every method
NDCG@3 = 1.000 and a Wilcoxon p of exactly 1.0, so nothing was measurable. The
current set adds four groups of harder cases.

Hard negatives are same-domain pairs where lexical matching should fail: Python
backend against a Java/Spring posting, a senior posting against a junior CV, a
data scientist against an ML engineering post. The paraphrase case
(`backend_04_paraphrase`) is a genuinely senior server-side CV written to avoid
the posting's vocabulary, which is the case that tests whether semantic matching
earns its place. Ambiguous profiles cover 8 CVs whose best grade is 1 with no
strong fit anywhere, 4 CVs with two grade-2 jobs, and one CV
(`generalist_it_support`) with no relevant job at all. Finally, two sparse CVs
(`sparse_backend_01`, `sparse_nurse_01`) are ~45-word resumes that list skills
without evidencing them; requirement-level pooling scores these much lower than a
detailed CV of an equally qualified candidate, and the effect is invisible unless
the gold set contains such documents (see the pooling discussion in
`app/services/chunking.py`).

Those groups matter for reading the output. NDCG is undefined for a query with no
relevant job, and MRR is undefined without a grade-2, so the report states how
many queries each metric actually used (currently 26 of 27 for NDCG). A metric
averaged over a subset is not the same claim as one averaged over all.

## What it measures

| Family | Metric | Question it answers |
|---|---|---|
| Correlation | Spearman ρ, Pearson r | Does the predicted score track the human grade? |
| Ranking | NDCG@3, MRR (per resume) | As a retrieval task, are the right jobs ranked first? |
| Calibration | mean score per grade, calibration error | Does grade-0 actually score ≈0, or does everything land in the middle? |

Every figure comes with a **95% bootstrap CI**, and methods are compared with a
**paired Wilcoxon signed-rank test** on per-query NDCG@3. The significance table
reports `dNDCG` alongside each p-value: the test is two-sided, so the sign is the
only thing that says which method won.

## Methods evaluated

| Method | What it is |
|---|---|
| `tfidf` | production `calculate_tfidf_match_score`; fits IDF on just the two documents, so IDF is degenerate (effectively TF cosine) |
| `tfidf_corpus` | lexical baseline with IDF fit over the whole corpus |
| `sbert` | production `embeddings.semantic_similarity`, whole-document MiniLM cosine |
| `sbert_cal` | `sbert` through the shipped logistic calibration |
| `sbert_chunk` | `chunking.chunked_similarity`; each JD requirement scored by its best-matching CV chunk, averaged |
| `tfidf_corpus_cal` | `tfidf_corpus`, logistic calibration refit leave-one-out |
| `sbert_chunk_cal` | `sbert_chunk`, logistic calibration refit leave-one-out |
| `hybrid` | convex blend of the two calibrated scores (`--hybrid-weight`, default 0.5) |

The `_cal` rows and `hybrid` are computed by `add_ablation_methods`, which refits
the logistic **leave-one-out**: each pair is calibrated by parameters fit on the
other 242, so the calibrated columns are out-of-sample. Calibrating both inputs
onto the grade scale is also what makes `hybrid` a real lexical/semantic
trade-off rather than a silent weighting by the methods' very different raw
ranges (corpus TF-IDF spans roughly 0–25, chunked SBERT roughly 20–60).

## Findings so far

`results/comparison.md` holds the current numbers; this section summarises them
(243 pairs, 27 queries).

Chunking significantly improves on whole-document SBERT (ΔNDCG +0.044,
p = 0.043), because whole-document embedding truncates at 256 word-pieces and
blurs the specific bullet that answers a requirement. Chunked SBERT is level with
the lexical baseline rather than ahead of it (ΔNDCG +0.001, p = 0.686), and
whole-document SBERT trails it (−0.044, p = 0.128), so chunking closes a gap
rather than opening a lead. Calibration is the largest single effect: calibration
error drops from 25.56 (`sbert_chunk`) to 9.00 (`sbert_chunk_cal`,
leave-one-out). Blending adds nothing measurable over the better calibrated
single method (`hybrid` vs `tfidf_corpus_cal`, p = 0.500).

Label quality moved the conclusions more than any algorithmic change tested.
Tightening the grade-1 definition reversed two results: chunking went from
p = 0.959 to p = 0.043, and an apparent significant advantage for corpus-fit IDF
over the shipped TF-IDF (p = 0.018) disappeared entirely (p = 0.500). Any claim
from this harness is therefore a claim about these labels. The evidence is
archived in `results_archive/`: same documents, labels the only difference.

One limitation remains open. No method tested ranks `backend_04_paraphrase` or
`backend_05_principal` (both grade-2) above `backend_03_junior` (grade-1). All of
them reward surface vocabulary, and none handles a candidate who describes
equivalent work in different words.

`sbert_chunk_cal` (leave-one-out) is the honest calibrated figure to cite.
`sbert_chunk_cal_shipped` is what the app actually serves, but its parameters
were fit on the same 243 pairs, so it is in-sample and reads slightly better.

## Reproducibility

All randomness (bootstrap, jitter) is seeded via `--seed` (default 42), so reruns
are identical. Pin dependency versions in `requirements.txt` before the final run
and record them in the thesis. Because the dataset drives the conclusions, treat
`data/` as frozen once results are cited; if it changes, every number and every
p-value must be regenerated together.

## Outputs (thesis figures)

`eval/results/` after a run:
- `comparison.md` / `comparison.csv`: headline, calibration, calibration-error
  and significance tables.
- `calibration.png`: mean predicted score per grade, per method.
- `scatter.png`: predicted score vs human grade.
- `ndcg.png`: NDCG@3 per method with 95% CI error bars.

`run_extraction.py` writes `results/extraction.md`. `calibrate.py` writes
`results/calibration_report.md` and the shipped
`app/services/calibration_params.json`.

## Extending it

1. More documents. Drop `.txt` files in `resumes/`/`jobs/` and add their pairs to
   `labels.csv`. Prioritise hard negatives and ambiguous profiles over more
   obvious matches, since obvious pairs saturate the metrics.
2. BM25 as a third lexical baseline (`pip install rank-bm25`), added to
   `build_methods()`.
3. A larger sentence encoder. The open limitation above may be a capacity issue;
   `all-MiniLM-L6-v2` is small and truncates at 256 word-pieces.
4. Per-job queries as well as per-résumé (pass `group_key="job_id"` to the
   ranking metrics), which is the recruiter framing of the task.
5. Chunk-pooling variants: mean-of-top-k rather than max per requirement, or
   weighting requirements by position in the posting.
