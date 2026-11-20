"""Shared fixtures.

The real model is never loaded in tests. Tests that need the semantic path
use `fake_embeddings`, a hashed bag-of-words encoder.
"""

import hashlib
import pathlib
import re

import numpy as np
import pytest

from app.services import embeddings

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "eval" / "data"
DIM = 256


def read_resume(name):
    return (DATA_DIR / "resumes" / f"{name}.txt").read_text(encoding="utf-8")


def read_job(name):
    return (DATA_DIR / "jobs" / f"{name}.txt").read_text(encoding="utf-8")


def _fake_embed(texts):
    rows = []
    for text in texts:
        vec = np.zeros(DIM)
        for token in re.findall(r"[a-z0-9+#]+", text.lower()):
            vec[int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = np.linalg.norm(vec)
        rows.append(vec / norm if norm else vec)
    return np.array(rows)


@pytest.fixture(autouse=True)
def _no_model(monkeypatch):
    def unavailable():
        raise RuntimeError("model loading is disabled in tests")

    monkeypatch.setattr(embeddings, "_get_model", unavailable)


@pytest.fixture
def fake_embeddings(monkeypatch):
    monkeypatch.setattr(embeddings, "embed", _fake_embed)
    return _fake_embed
