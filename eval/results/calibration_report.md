# Calibration of the SBERT relevance score

Fitted logistic mapping: `100 * sigmoid(k * (s/100 - x0))` with **x0 = 0.471**, **k = 11.28** (s = raw score). Strictly monotonic.

## Mean predicted score per relevance grade

| Grade | ideal | raw SBERT | calibrated |
|---|---|---|---|
| 0 | 0 | 18.4 ± 9.4 | 6.1 ± 7.2 |
| 1 | 50 | 41.0 ± 10.6 | 37.0 ± 23.7 |
| 2 | 100 | 71.6 ± 8.0 | 91.9 ± 6.2 |

## Calibration error (mean abs. deviation from ideal, lower=better)

- raw SBERT:                 **18.7**
- calibrated (fit on all):   **9.9**  *(in-sample)*
- calibrated (leave-one-out): **10.9**  *(honest, cross-validated)*

## Ranking is unchanged (the mapping is monotonic)

- Spearman rho:  raw 0.812  ->  calibrated 0.812
- Sum of per-query NDCG@3:  raw 6.000  ->  calibrated 6.000

> Identical by construction: a strictly increasing transform cannot reorder candidates, so all rank-based metrics are invariant. Only the absolute, human-facing score changes.
