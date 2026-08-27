# TF-IDF vs SBERT -- resume/JD matching evaluation

Gold set: **243 labeled pairs**, 27 resumes (queries), relevance grades [0, 1, 2]. 95% bootstrap CIs in brackets.

## Headline metrics

| Method | Spearman rho | Pearson r | NDCG@3 | MRR |
|---|---|---|---|---|
| `tfidf` | 0.641 [0.568, 0.702] | 0.782 [0.722, 0.837] | 0.953 [0.914, 0.985] | 1.000 [1.000, 1.000] |
| `tfidf_corpus` | 0.650 [0.577, 0.713] | 0.807 [0.747, 0.858] | 0.958 [0.918, 0.990] | 1.000 [1.000, 1.000] |
| `sbert` | 0.603 [0.525, 0.674] | 0.683 [0.597, 0.755] | 0.915 [0.858, 0.962] | 0.963 [0.889, 1.000] |
| `sbert_chunk` | 0.633 [0.542, 0.706] | 0.737 [0.665, 0.794] | 0.959 [0.911, 0.999] | 0.972 [0.917, 1.000] |
| `sbert_chunk_cal_shipped` | 0.633 [0.543, 0.706] | 0.841 [0.777, 0.893] | 0.959 [0.911, 0.999] | 0.972 [0.917, 1.000] |
| `tfidf_corpus_cal` | 0.648 [0.574, 0.711] | 0.837 [0.761, 0.895] | 0.958 [0.918, 0.990] | 1.000 [1.000, 1.000] |
| `sbert_chunk_cal` | 0.631 [0.541, 0.704] | 0.833 [0.766, 0.887] | 0.959 [0.911, 0.999] | 0.972 [0.917, 1.000] |
| `hybrid` | 0.651 [0.574, 0.717] | 0.856 [0.790, 0.907] | 0.975 [0.942, 0.999] | 1.000 [1.000, 1.000] |

## Calibration -- mean predicted score per relevance grade

Well-calibrated = grade 0 near 0, rising monotonically with grade.

| Method | grade 0 | grade 1 | grade 2 |
|---|---|---|---|
| `tfidf` | 3.0 ± 2.2 | 9.9 ± 4.7 | 18.2 ± 9.0 |
| `tfidf_corpus` | 2.7 ± 2.4 | 11.4 ± 6.1 | 23.2 ± 11.4 |
| `sbert` | 24.3 ± 11.2 | 43.6 ± 8.1 | 56.8 ± 13.5 |
| `sbert_chunk` | 24.3 ± 6.5 | 39.2 ± 7.3 | 46.5 ± 7.2 |
| `sbert_chunk_cal_shipped` | 4.4 ± 7.5 | 48.6 ± 29.5 | 72.4 ± 26.3 |
| `tfidf_corpus_cal` | 5.7 ± 8.2 | 43.3 ± 31.8 | 80.7 ± 28.4 |
| `sbert_chunk_cal` | 4.5 ± 7.7 | 48.9 ± 30.1 | 71.5 ± 26.9 |
| `hybrid` | 5.1 ± 7.2 | 46.1 ± 27.9 | 76.1 ± 26.3 |

## Calibration error (mean |predicted - grade target|, lower is better)

| Method | calibration error |
|---|---|
| `tfidf` | 13.97 |
| `tfidf_corpus` | 13.09 |
| `sbert` | 24.45 |
| `sbert_chunk` | 25.56 |
| `sbert_chunk_cal_shipped` | 8.80 |
| `tfidf_corpus_cal` | 9.35 |
| `sbert_chunk_cal` | 9.00 |
| `hybrid` | 8.73 |

## Significance (paired Wilcoxon on per-query NDCG@3)

Tested over 26 queries. `*` marks p < 0.05. The test is two-sided, so read `dNDCG` for the direction: it is method A's mean NDCG@3 minus method B's, over the queries the test used.

| Comparison | dNDCG | p | | Question |
|---|---|---|---|---|
| `tfidf_corpus` vs `tfidf` | +0.005 | 0.6858 |  | does corpus-fit IDF beat the shipped two-document fit? |
| `sbert` vs `tfidf_corpus` | -0.044 | 0.1282 |  | does whole-document semantic matching beat the lexical baseline? |
| `sbert_chunk` vs `sbert` | +0.044 | 0.0425 | * | does section/requirement-level chunking beat whole-document? |
| `sbert_chunk` vs `tfidf_corpus` | +0.001 | 0.6858 |  | does chunked semantic matching beat the lexical baseline? |
| `hybrid` vs `tfidf_corpus_cal` | +0.016 | 0.5002 |  | does adding a semantic component beat calibrated lexical alone? |
| `hybrid` vs `sbert_chunk_cal` | +0.016 | 0.1797 |  | does adding a lexical component beat calibrated chunked alone? |

> A non-significant result is not evidence of no effect: at this gold-set size the test only resolves fairly large differences. Note also that the labels themselves drive these outcomes -- see eval/README.md on the grading rule before quoting any p-value.
