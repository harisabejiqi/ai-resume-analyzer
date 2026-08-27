# TF-IDF vs SBERT -- resume/JD matching evaluation

Gold set: **225 labeled pairs**, 25 resumes (queries), relevance grades [0, 1, 2]. 95% bootstrap CIs in brackets.

## Headline metrics

| Method | Spearman rho | Pearson r | NDCG@3 | MRR |
|---|---|---|---|---|
| `tfidf` | 0.671 [0.591, 0.738] | 0.746 [0.688, 0.798] | 0.945 [0.902, 0.978] | 1.000 [1.000, 1.000] |
| `tfidf_corpus` | 0.699 [0.622, 0.763] | 0.776 [0.726, 0.827] | 0.988 [0.973, 0.999] | 1.000 [1.000, 1.000] |
| `sbert` | 0.662 [0.580, 0.727] | 0.720 [0.644, 0.780] | 0.916 [0.859, 0.963] | 0.931 [0.824, 1.000] |
| `sbert_cal` | 0.662 [0.581, 0.727] | 0.766 [0.683, 0.830] | 0.916 [0.859, 0.963] | 0.931 [0.824, 1.000] |
| `sbert_chunk` | 0.680 [0.602, 0.741] | 0.769 [0.705, 0.817] | 0.917 [0.859, 0.965] | 0.971 [0.912, 1.000] |
| `tfidf_corpus_cal` | 0.696 [0.619, 0.761] | 0.837 [0.770, 0.890] | 0.987 [0.968, 0.999] | 1.000 [1.000, 1.000] |
| `sbert_chunk_cal` | 0.676 [0.598, 0.738] | 0.806 [0.744, 0.855] | 0.917 [0.859, 0.965] | 0.971 [0.912, 1.000] |
| `hybrid` | 0.699 [0.621, 0.763] | 0.842 [0.787, 0.887] | 0.966 [0.927, 0.991] | 1.000 [1.000, 1.000] |

## Calibration -- mean predicted score per relevance grade

Well-calibrated = grade 0 near 0, rising monotonically with grade.

| Method | grade 0 | grade 1 | grade 2 |
|---|---|---|---|
| `tfidf` | 2.8 ± 2.0 | 8.0 ± 5.0 | 17.8 ± 9.0 |
| `tfidf_corpus` | 2.4 ± 2.0 | 9.2 ± 6.3 | 23.0 ± 11.5 |
| `sbert` | 23.3 ± 10.1 | 40.9 ± 9.8 | 56.2 ± 13.9 |
| `sbert_cal` | 10.1 ± 10.6 | 36.3 ± 20.8 | 66.2 ± 26.0 |
| `sbert_chunk` | 24.3 ± 5.7 | 36.0 ± 7.2 | 46.8 ± 7.2 |
| `tfidf_corpus_cal` | 7.0 ± 8.5 | 39.9 ± 29.9 | 87.8 ± 20.5 |
| `sbert_chunk_cal` | 7.2 ± 8.9 | 38.8 ± 28.0 | 74.6 ± 21.9 |
| `hybrid` | 7.1 ± 7.8 | 39.3 ± 27.1 | 81.2 ± 19.7 |

## Significance (paired Wilcoxon on per-query NDCG@3)

- `sbert` vs `tfidf`: p = 0.4008
- `sbert` vs `tfidf_corpus`: p = 0.0109

> NOTE: with only a handful of queries this test has almost no power. Expand the gold set (see eval/README.md) before quoting p-values.
