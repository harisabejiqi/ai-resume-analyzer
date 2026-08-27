# Calibration of the `sbert_chunk` relevance score

Fitted on **243 labeled pairs**. Mapping: `100 * sigmoid(k * (s/100 - x0))` with **x0 = 0.403**, **k = 26.75** (s = raw score). Strictly monotonic.

> These parameters are valid **only** for `sbert_chunk` scores. The app must apply them to the same method it was fit for -- see the `fit_for` field in `calibration_params.json`.

## Mean predicted score per relevance grade

| Grade | ideal | raw sbert_chunk | calibrated |
|---|---|---|---|
| 0 | 0 | 24.3 ± 6.5 | 4.4 ± 7.5 |
| 1 | 50 | 39.2 ± 7.3 | 48.6 ± 29.5 |
| 2 | 100 | 46.5 ± 7.2 | 72.4 ± 26.3 |

## Calibration error (mean abs. deviation from ideal, lower=better)

- raw sbert_chunk:                 **25.6**
- calibrated (fit on all):   **8.8**  *(in-sample)*
- calibrated (leave-one-out): **9.0**  *(honest, cross-validated)*

## Ranking is unchanged (the mapping is monotonic)

- Spearman rho:  raw 0.633  ->  calibrated 0.633
- Sum of per-query NDCG@3:  raw 24.940  ->  calibrated 24.940

> Identical by construction: a strictly increasing transform cannot reorder candidates, so all rank-based metrics are invariant. Only the absolute, human-facing score changes.
