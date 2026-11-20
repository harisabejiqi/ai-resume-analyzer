"""Tests for app/services/summary.py, with the embedding model mocked."""

import numpy as np

from app.services import embeddings, summary

UNITS = [
    "Built REST APIs in Python and Django for a booking platform",
    "Enjoys hiking and photography on weekends",
    "Wrote Python services for payments and invoicing",
    "Deployed Python APIs on Docker and AWS",
    "Volunteer at the local animal shelter",
    "Designed Python data pipelines for reporting",
]
CV = "\n".join(f"- {u}" for u in UNITS)


def _topic_embed(texts):
    rows = []
    for t in texts:
        python = 1.0 if "Python" in t else 0.0
        rows.append([python, 1.0 - python, 0.1 * len(t.split())])
    rows = np.array(rows)
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def test_picks_units_closest_to_centroid_in_original_order(monkeypatch):
    monkeypatch.setattr(embeddings, "embed", _topic_embed)
    result = summary.extractive_summary(CV, k=4)
    assert result["method"] == "sbert_centroid"
    assert result["sentences"] == [UNITS[0], UNITS[2], UNITS[3], UNITS[5]]


def test_sentences_are_verbatim_units(fake_embeddings):
    result = summary.extractive_summary(CV, k=3)
    assert len(result["sentences"]) == 3
    assert all(s in UNITS for s in result["sentences"])
    assert result["sentences"] == sorted(result["sentences"], key=UNITS.index)


def test_falls_back_to_first_k_when_model_fails(monkeypatch):
    def broken(texts):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(embeddings, "embed", broken)
    assert summary.extractive_summary(CV, k=4) == {
        "sentences": UNITS[:4], "method": "fallback",
    }


def test_short_cv_returns_all_units_without_embedding(monkeypatch):
    def must_not_be_called(texts):
        raise AssertionError("embed called")

    monkeypatch.setattr(embeddings, "embed", must_not_be_called)
    short = "\n".join(f"- {u}" for u in UNITS[:3])
    assert summary.extractive_summary(short, k=4) == {
        "sentences": UNITS[:3], "method": "fallback",
    }


def test_heading_lines_are_skipped(fake_embeddings):
    cv = "- Cloud & DevOps tools:\n" + CV
    result = summary.extractive_summary(cv, k=len(UNITS))
    assert result["sentences"] == UNITS


def test_empty_text():
    assert summary.extractive_summary("") == {"sentences": [], "method": "fallback"}
