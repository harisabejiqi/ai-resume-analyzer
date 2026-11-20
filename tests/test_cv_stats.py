"""Tests for app/services/cv_stats.py. Expected values were captured by running the code."""

from app.services import cv_stats
from app.services.analyzer import analyze_resume

from conftest import read_resume


def _run(name):
    text = read_resume(name)
    return text, analyze_resume(text)


def test_statistics_structured_resume():
    text, analysis = _run("backend_03_junior")
    assert cv_stats.compute_statistics(text, analysis) == {
        "word_count": 163,
        "line_count": 23,
        "sections": ["experience", "education", "skills", "summary", "professional experience"],
        "roles": 2,
        "bullet_count": 6,
        "avg_bullets_per_role": 3.0,
        "avg_words_per_bullet": 9.8,
        "quantified_bullets_pct": 16.7,
        "action_verb_bullets_pct": 33.3,
        "technical_skills": 9,
        "soft_skills": 2,
        "education_entries": 2,
        "experience_years": 1.3,
    }


def test_statistics_unstructured_resume():
    text, analysis = _run("backend_01")
    stats = cv_stats.compute_statistics(text, analysis)
    assert stats["roles"] == stats["bullet_count"] == 0
    assert stats["avg_words_per_bullet"] == 0.0
    assert stats["word_count"] == 62


def _by_id(checks):
    return {c["id"]: c for c in checks}


def test_checks_all_pass_on_structured_resume():
    text, analysis = _run("backend_03_junior")
    checks = cv_stats.readability_checks(text, analysis)
    assert [c["id"] for c in checks] == [
        "contact", "sections", "length", "bullets", "dates", "bullet_length", "paragraphs",
    ]
    assert all(c["passed"] for c in checks)


def test_checks_on_unstructured_resume():
    text, analysis = _run("backend_01")
    checks = _by_id(cv_stats.readability_checks(text, analysis))
    assert {k for k, c in checks.items() if not c["passed"]} == {
        "contact", "sections", "length", "bullets", "dates",
    }
    assert checks["contact"]["detail"] == "Not found: email, phone."
    assert checks["sections"]["detail"] == \
        "No heading found for: experience, education, skills."
    assert checks["length"]["detail"] == "62 words (recommended 150 to 1000)."


def test_long_bullets_and_paragraphs_are_flagged():
    text, analysis = _run("backend_03_junior")
    long_bullet = " ".join(["word"] * (cv_stats.MAX_BULLET_WORDS + 1))
    analysis["work_experience"][0]["bullets"].append(long_bullet)
    paragraph = " ".join(["word"] * (cv_stats.MAX_PARAGRAPH_WORDS + 1))
    checks = _by_id(cv_stats.readability_checks(text + "\n" + paragraph, analysis))
    assert checks["bullet_length"]["passed"] is False
    assert checks["bullet_length"]["detail"] == "1 bullet(s) are longer than 40 words."
    assert checks["paragraphs"]["passed"] is False


def test_role_without_dates_or_bullets_fails():
    text, analysis = _run("backend_03_junior")
    analysis["work_experience"][1]["start"] = None
    analysis["work_experience"][1]["bullets"] = []
    checks = _by_id(cv_stats.readability_checks(text, analysis))
    assert checks["dates"]["detail"] == "1 of 2 role(s) have no dates."
    assert checks["bullets"]["detail"] == "1 of 2 role(s) have no bullets."


def test_docstring_says_not_an_ats():
    assert "not a commercial ATS" in cv_stats.readability_checks.__doc__
