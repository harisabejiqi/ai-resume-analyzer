"""Tests for `scorer.score_job_match` and the split suggestion functions.

The main check is that the job match score is the same as
`calculate_match_score` and that the CV is only embedded once.
"""

import pytest

from app.services import embeddings, scorer
from app.services.analyzer import analyze_resume
from app.services.jd_parser import parse_job_description

from conftest import read_job, read_resume

PAIRS = [
    ("backend_01", "backend_jd"),
    ("backend_01", "nurse_jd"),
    ("datasci_01", "datasci_jd"),
    ("backend_03_junior", "backend_jd"),
]


def _job_match(resume_text, jd_text):
    analysis = analyze_resume(resume_text)
    return scorer.score_job_match(resume_text, jd_text, analysis, parse_job_description(jd_text))


@pytest.mark.parametrize("resume, job", PAIRS)
def test_score_is_identical_to_calculate_match_score(fake_embeddings, resume, job):
    resume_text, jd_text = read_resume(resume), read_job(job)
    assert _job_match(resume_text, jd_text)["score"] == \
        scorer.calculate_match_score(resume_text, jd_text)


def test_embeds_once_per_side(monkeypatch, fake_embeddings):
    calls = []

    def counting(texts):
        calls.append(len(texts))
        return fake_embeddings(texts)

    monkeypatch.setattr(embeddings, "embed", counting)
    _job_match(read_resume("backend_01"), read_job("backend_jd"))
    assert len(calls) == 2


def test_falls_back_to_tfidf_when_model_fails(monkeypatch):
    def broken(texts):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(embeddings, "embed", broken)
    result = _job_match(read_resume("backend_01"), read_job("backend_jd"))
    assert result["score"] == 16.1
    assert result["evidence"] == []


def test_evidence_covers_every_requirement(fake_embeddings):
    result = _job_match(read_resume("backend_01"), read_job("backend_jd"))
    assert result["reliability"] == "normal"
    assert result["reliability_note"] is None
    assert len(result["evidence"]) == result["requirement_count"] == 9
    assert set(result["evidence"][0]) == {"requirement", "best_chunk", "score"}


def test_too_short_posting_has_no_score(fake_embeddings):
    result = _job_match(read_resume("backend_03_junior"), "Python")
    assert result["requirement_count"] == 0
    assert result["score"] is None
    assert result["reliability"] == "insufficient"
    assert result["reliability_note"] == scorer.TOO_SHORT_NOTE


def test_short_posting_is_flagged_low_reliability(fake_embeddings):
    jd = "Python developer with Django and SQL"
    result = _job_match(read_resume("backend_03_junior"), jd)
    assert result["requirement_count"] == 1
    assert result["score"] == scorer.calculate_match_score(read_resume("backend_03_junior"), jd)
    assert result["reliability"] == "low"
    assert "only 1 requirement(s)" in result["reliability_note"]


def test_skill_match_and_requirements_check(fake_embeddings):
    result = _job_match(read_resume("backend_03_junior"), read_job("backend_jd"))
    assert result["skill_match"] == {
        "matched": ["python", "sql", "docker"],
        "missing": ["aws", "ci/cd", "microservices"],
        "coverage": 50.0,
    }
    jd = parse_job_description(read_job("backend_jd"))
    analysis = analyze_resume(read_resume("backend_03_junior"))
    check = result["requirements_check"]
    assert check["experience"]["required"] == jd["experience_required"]
    assert check["experience"]["candidate"] == analysis["experience_years"]
    assert check["education"]["required"] == jd["education_required"]


def test_suggestions_are_job_specific_only(fake_embeddings):
    resume_text, jd_text = read_resume("backend_01"), read_job("backend_jd")
    analysis = analyze_resume(resume_text)
    result = scorer.score_job_match(resume_text, jd_text, analysis,
                                    parse_job_description(jd_text))
    expected = scorer.generate_job_suggestions(
        analysis, result["score"], result["missing_keywords"], result["skill_match"]
    )
    assert result["suggestions"] == expected
    stats = scorer._experience_stats(analysis["work_experience"])
    general = scorer.generate_general_suggestions(analysis, stats)
    assert not set(result["suggestions"]) & set(general)
    assert result["disclaimer"] == scorer.JOB_MATCH_DISCLAIMER


def test_job_suggestions_skip_score_advice_without_a_score():
    analysis = analyze_resume(read_resume("backend_03_junior"))
    assert scorer.generate_job_suggestions(analysis, None, ["aws"], None) == [
        "The posting stresses aws, none of which appear in your resume. Add the ones you "
        "have real experience with, in context (not a keyword list)."
    ]

