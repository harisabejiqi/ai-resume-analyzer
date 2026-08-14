# TF-IDF vs SBERT -- resume/JD matching evaluation

Gold set: **36 labeled pairs**, 6 resumes (queries), relevance grades [0, 1, 2]. 95% bootstrap CIs in brackets.

## Headline metrics

| Method | Spearman rho | Pearson r | NDCG@3 | MRR |
|---|---|---|---|---|
| `tfidf` | 0.785 [0.565, 0.902] | 0.845 [0.773, 0.928] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| `tfidf_corpus` | 0.780 [0.556, 0.902] | 0.855 [0.778, 0.934] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| `sbert` | 0.812 [0.643, 0.906] | 0.901 [0.813, 0.950] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| `sbert_cal` | 0.812 [0.643, 0.906] | 0.923 [0.829, 0.974] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

## Calibration -- mean predicted score per relevance grade

Well-calibrated = grade 0 near 0, rising monotonically with grade.

| Method | grade 0 | grade 1 | grade 2 |
|---|---|---|---|
| `tfidf` | 1.3 ± 1.3 | 5.1 ± 2.7 | 21.5 ± 8.2 |
| `tfidf_corpus` | 1.6 ± 1.9 | 6.4 ± 3.3 | 29.0 ± 10.2 |
| `sbert` | 18.4 ± 9.4 | 41.0 ± 10.6 | 71.6 ± 8.0 |
| `sbert_cal` | 6.1 ± 7.2 | 37.0 ± 23.7 | 91.9 ± 6.2 |

## Significance (paired Wilcoxon on per-query NDCG@3)

- `sbert` vs `tfidf`: p = 1.0000
- `sbert` vs `tfidf_corpus`: p = 1.0000

> NOTE: with only a handful of queries this test has almost no power. Expand the gold set (see eval/README.md) before quoting p-values.
