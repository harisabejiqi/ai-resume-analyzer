# Saktësia e ekstraktimit të informacionit

Grup testimi: **6 CV të etiketuara me dorë** (eval/extraction/). Metrikat janë llogaritur duke ekzekutuar `analyze_resume` e prodhimit dhe duke krahasuar daljen me ground-truth.

| Fusha | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Emër | 5 | 1 | 1 | 0.83 | 0.83 | 0.83 |
| Email | 5 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Telefon | 6 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Aftësi teknike | 33 | 0 | 2 | 1.00 | 0.94 | 0.97 |
| Arsim (zbulim) | 6 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| Vite përvoje | 6 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| **Mikro-mesatare** | 61 | 1 | 3 | 0.98 | 0.95 | 0.97 |

