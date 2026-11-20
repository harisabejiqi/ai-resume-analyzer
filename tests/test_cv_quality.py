"""Tests for Mode 1 (`scorer.score_cv_quality`).

Expected scores were captured by running the code; the hand check for
backend_01 is 0.30*0 + 0.20*100 + 0.15*0 + 0.15*100 + 0.10*0 + 0.10*41.3.
"""

import pytest

from app.services import scorer
from app.services.analyzer import analyze_resume

from conftest import read_resume

CLEAN = {"available": True, "issue_count": 0, "issues": []}
UNAVAILABLE = {"available": False, "issue_count": 0, "issues": []}
TWO_ISSUES = {
    "available": True,
    "issue_count": 2,
    "issues": [
        {"text": "recieved", "suggestions": ["received"]},
        {"text": "teh", "suggestions": []},
    ],
}


def _analysis(name):
    return analyze_resume(read_resume(name))


def test_weights_sum_to_one():
    assert sum(scorer.CV_QUALITY_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "resume, expected, expected_without_grammar",
    [
        ("backend_01", 39.1, 28.4),
        ("backend_03_junior", 82.0, 78.8),
        ("fullstack_01", 89.5, 87.6),
    ],
)
def test_cv_quality_scores(resume, expected, expected_without_grammar):
    analysis = _analysis(resume)
    assert scorer.score_cv_quality(analysis, CLEAN)["score"] == expected
    assert scorer.score_cv_quality(analysis, UNAVAILABLE)["score"] == expected_without_grammar


def test_breakdown_parts():
    breakdown = scorer.score_cv_quality(_analysis("backend_01"), CLEAN)["breakdown"]
    assert {k: v["score"] for k, v in breakdown.items()} == {
        "experience": 0.0,
        "skills": 100.0,
        "contact": 0.0,
        "language": 100.0,
        "education": 0.0,
        "length": 41.3,
    }
    assert {k: v["weight"] for k, v in breakdown.items()} == scorer.CV_QUALITY_WEIGHTS


def test_language_is_dropped_and_weights_renormalized_without_grammar_engine():
    breakdown = scorer.score_cv_quality(_analysis("backend_01"), UNAVAILABLE)["breakdown"]
    assert "language" not in breakdown
    assert sum(v["weight"] for v in breakdown.values()) == pytest.approx(1.0, abs=1e-3)


def test_grammar_issues_lower_language_score():
    result = scorer.score_cv_quality(_analysis("fullstack_01"), TWO_ISSUES)
    assert result["breakdown"]["language"]["score"] == 80.0


def test_has_no_job_relevance_part():
    breakdown = scorer.score_cv_quality(_analysis("backend_03_junior"), CLEAN)["breakdown"]
    assert "relevance" not in breakdown


def test_suggestions_are_general_with_grammar_first():
    analysis = _analysis("backend_03_junior")
    stats = scorer._experience_stats(analysis["work_experience"])
    result = scorer.score_cv_quality(analysis, TWO_ISSUES)
    assert result["suggestions"] == [
        "Fix 2 grammar/spelling issue(s) (e.g. 'recieved' → 'received').",
        *scorer.generate_general_suggestions(analysis, stats),
    ]


def test_strong_resume_without_grammar_issues():
    assert scorer.score_cv_quality(_analysis("fullstack_01"), CLEAN)["suggestions"] == [
        scorer.STRONG_RESUME
    ]


def test_grammar_suggestion_text():
    assert scorer.grammar_suggestion(CLEAN) is None
    assert scorer.grammar_suggestion(None) is None
    assert scorer.grammar_suggestion(
        {"available": True, "issue_count": 1, "issues": [{"text": "x", "suggestions": []}]}
    ) == "Fix 1 grammar/spelling issue(s)."
