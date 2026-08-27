# TF-IDF vs SBERT -- resume/JD matching evaluation

Gold set: **225 labeled pairs**, 25 resumes (queries), relevance grades [0, 1, 2]. 95% bootstrap CIs in brackets.

## Headline metrics

| Method | Spearman rho | Pearson r | NDCG@3 | MRR |
|---|---|---|---|---|
| `tfidf` | 0.645 [0.565, 0.707] | 0.779 [0.710, 0.838] | 0.959 [0.921, 0.990] | 1.000 [1.000, 1.000] |
| `tfidf_corpus` | 0.657 [0.581, 0.719] | 0.805 [0.742, 0.863] | 0.975 [0.938, 1.000] | 1.000 [1.000, 1.000] |
| `sbert` | 0.604 [0.521, 0.673] | 0.680 [0.584, 0.756] | 0.918 [0.855, 0.969] | 0.958 [0.875, 1.000] |
| `sbert_chunk` | 0.657 [0.579, 0.719] | 0.767 [0.697, 0.820] | 0.966 [0.916, 1.000] | 0.969 [0.906, 1.000] |
| `sbert_chunk_cal_shipped` | 0.657 [0.579, 0.719] | 0.853 [0.790, 0.904] | 0.966 [0.916, 1.000] | 0.969 [0.906, 1.000] |
| `tfidf_corpus_cal` | 0.655 [0.580, 0.716] | 0.830 [0.746, 0.893] | 0.975 [0.938, 1.000] | 1.000 [1.000, 1.000] |
| `sbert_chunk_cal` | 0.655 [0.576, 0.717] | 0.844 [0.779, 0.898] | 0.966 [0.916, 1.000] | 0.969 [0.906, 1.000] |
| `hybrid` | 0.664 [0.588, 0.723] | 0.858 [0.788, 0.913] | 0.983 [0.954, 1.000] | 1.000 [1.000, 1.000] |

## Calibration -- mean predicted score per relevance grade

Well-calibrated = grade 0 near 0, rising monotonically with grade.

| Method | grade 0 | grade 1 | grade 2 |
|---|---|---|---|
| `tfidf` | 3.1 ± 2.2 | 10.1 ± 4.6 | 18.4 ± 9.3 |
| `tfidf_corpus` | 2.8 ± 2.4 | 11.9 ± 6.1 | 23.7 ± 11.9 |
| `sbert` | 24.7 ± 11.0 | 44.1 ± 8.0 | 56.7 ± 14.1 |
| `sbert_chunk` | 25.0 ± 6.0 | 40.2 ± 5.7 | 47.2 ± 7.1 |
| `sbert_chunk_cal_shipped` | 4.4 ± 7.2 | 48.9 ± 28.2 | 73.8 ± 25.7 |
| `tfidf_corpus_cal` | 6.0 ± 8.1 | 44.0 ± 31.5 | 79.6 ± 29.7 |
| `sbert_chunk_cal` | 4.4 ± 7.4 | 49.3 ± 28.9 | 72.9 ± 26.4 |
| `hybrid` | 5.2 ± 7.0 | 46.7 ± 26.9 | 76.3 ± 27.0 |

## Calibration error (mean |predicted - grade target|, lower is better)

| Method | calibration error |
|---|---|
| `tfidf` | 13.97 |
| `tfidf_corpus` | 13.09 |
| `sbert` | 24.66 |
| `sbert_chunk` | 25.85 |
| `sbert_chunk_cal_shipped` | 8.55 |
| `tfidf_corpus_cal` | 9.74 |
| `sbert_chunk_cal` | 8.76 |
| `hybrid` | 8.80 |

## Significance (paired Wilcoxon on per-query NDCG@3)

Tested over 24 queries. `*` marks p < 0.05. The test is two-sided, so read `dNDCG` for the direction: it is method A's mean NDCG@3 minus method B's, over the queries the test used.

| Comparison | dNDCG | p | | Question |
|---|---|---|---|---|
| `tfidf_corpus` vs `tfidf` | +0.015 | 0.5002 |  | does corpus-fit IDF beat the shipped two-document fit? |
| `sbert` vs `tfidf_corpus` | -0.057 | 0.0464 | * | does whole-document semantic matching beat the lexical baseline? |
| `sbert_chunk` vs `sbert` | +0.048 | 0.0425 | * | does section/requirement-level chunking beat whole-document? |
| `sbert_chunk` vs `tfidf_corpus` | -0.009 | 0.4652 |  | does chunked semantic matching beat the lexical baseline? |
| `hybrid` vs `tfidf_corpus_cal` | +0.008 | 0.7150 |  | does adding a semantic component beat calibrated lexical alone? |
| `hybrid` vs `sbert_chunk_cal` | +0.017 | 0.1797 |  | does adding a lexical component beat calibrated chunked alone? |

> A non-significant result is not evidence of no effect: at this gold-set size the test only resolves fairly large differences. Note also that the labels themselves drive these outcomes -- see eval/README.md on the grading rule before quoting any p-value.
