"""Offline evaluation harness for the resume--job-description matching methods.

Compares the lexical baseline (TF-IDF cosine) against the semantic method
(Sentence-BERT embeddings) on a small, hand-labeled gold set of
(resume, job) pairs, and reports correlation, ranking, and calibration metrics
with bootstrap confidence intervals and a paired significance test.

Run from the repository root:  python -m eval.run_eval
"""
