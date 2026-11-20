"""Extractive summary of a CV.

Picks the k lines (see chunking.resume_chunks) closest to the average
embedding of the CV and returns them unchanged, in their original order.
"""

import numpy as np

from . import chunking, embeddings


def extractive_summary(text, k=4):
    """Return {"sentences": [...], "method": "sbert_centroid" | "fallback"}.

    "fallback" means the first k units were returned unranked: either the model
    could not be used, or the CV has no more than k units to choose from.
    """
    units = [u for u in chunking.resume_chunks(text) if not u.rstrip().endswith(":")]
    if len(units) <= k:
        return {"sentences": units, "method": "fallback"}

    try:
        vecs = np.asarray(embeddings.embed(units), dtype=float)
    except Exception:
        return {"sentences": units[:k], "method": "fallback"}

    centroid = vecs.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm == 0:
        return {"sentences": units[:k], "method": "fallback"}

    closeness = vecs @ (centroid / norm)
    chosen = sorted(np.argsort(-closeness, kind="stable")[:k])
    return {"sentences": [units[i] for i in chosen], "method": "sbert_centroid"}
