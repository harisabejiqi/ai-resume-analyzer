"""Semantic similarity via sentence-transformer embeddings.

This is the "artificial intelligence" core of the matching pipeline. Instead of
lexical matching (TF-IDF counts shared words), we encode the resume and the job
description into dense vectors produced by a pretrained transformer model
(all-MiniLM-L6-v2, a distilled BERT-family sentence encoder). Cosine similarity
between those vectors captures *meaning*, so phrasing like "built REST APIs"
matches a job asking for "developed web services" even with no shared keywords —
something TF-IDF scores as zero.

The model (~90 MB) is downloaded on first use and cached locally by the
huggingface/sentence-transformers library, so subsequent runs (including an
offline thesis defense) need no network access.
"""

from functools import lru_cache

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    """Load the transformer once and reuse it (loading is the expensive part)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def is_available():
    """True if the model can be loaded (library installed + weights reachable)."""
    try:
        _get_model()
        return True
    except Exception:
        return False


def embed(texts):
    """Encode a list of strings into L2-normalized embedding vectors."""
    model = _get_model()
    return model.encode(list(texts), normalize_embeddings=True)


def semantic_similarity(text_a, text_b):
    """Cosine similarity of the two texts' embeddings, scaled to 0-100.

    Note: all-MiniLM truncates inputs to 256 word-pieces, so very long resumes
    are compared on their leading content. For document-level relevance this is
    an acceptable approximation; sentence-level chunking is a possible extension.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vec_a, vec_b = embed([text_a, text_b])
    score = float(np.dot(vec_a, vec_b))
    score = max(0.0, score)
    return round(score * 100, 2)
