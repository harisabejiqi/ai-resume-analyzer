"""Tests for app/services/scorer.py.

Expected values were taken from the scorer before the scores were split.
The semantic tests use the fake encoder, so their scores are not real ones.
"""

import pytest

from app.services import embeddings, scorer
from app.services.analyzer import analyze_resume
from app.services.jd_parser import match_required_skills, parse_job_description

from conftest import read_job, read_resume

@pytest.mark.parametrize(
    "resume, job, expected",
    [
        ("backend_01", "backend_jd", 16.1),
        ("backend_01", "nurse_jd", 1.01),
        ("datasci_01", "datasci_jd", 32.34),
    ],
)
def test_tfidf_match_score(resume, job, expected):
    assert scorer.calculate_tfidf_match_score(read_resume(resume), read_job(job)) == expected


@pytest.mark.parametrize(
    "resume, job, expected",
    [
        ("backend_01", "backend_jd", 31.14),
        ("backend_01", "nurse_jd", 4.74),
        ("datasci_01", "datasci_jd", 30.46),
    ],
)
def test_match_score_semantic_path(fake_embeddings, resume, job, expected):
    score = scorer.calculate_match_score(read_resume(resume), read_job(job))
    assert score == pytest.approx(expected, abs=0.01)


def test_match_score_ranks_relevant_job_above_irrelevant(fake_embeddings):
    resume = read_resume("backend_01")
    assert scorer.calculate_match_score(resume, read_job("backend_jd")) > \
        scorer.calculate_match_score(resume, read_job("nurse_jd"))


def test_match_score_falls_back_to_tfidf_when_model_fails(monkeypatch):
    def broken(texts):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(embeddings, "embed", broken)
    resume, job = read_resume("backend_01"), read_job("backend_jd")
    assert scorer.calculate_match_score(resume, job) == \
        scorer.calculate_tfidf_match_score(resume, job) == 16.1


def test_empty_job_description():
    assert scorer.calculate_match_score("some resume", "   ") == 0.0
    assert scorer.calculate_tfidf_match_score("some resume", " ") == 0.0
    assert scorer.find_missing_keywords("some resume", " ") == []


def test_match_method_is_unchanged():
    assert scorer.MATCH_METHOD == "sbert_chunk"


@pytest.mark.parametrize(
    "resume, job, expected",
    [
        ("backend_01", "backend_jd", [
            "sql", "apis", "databases", "cloud", "developer", "distributed", "design",
            "implement", "between", "write", "well-tested", "code", "model",
            "relational", "deploy",
        ]),
        ("backend_01", "nurse_jd", [
            "communication", "care", "patient", "hospital", "registered", "nurse",
            "intensive", "unit", "direct", "monitor", "vital", "signs", "administer",
            "medications", "treatments",
        ]),
        ("datasci_01", "datasci_jd", [
            "pytorch", "analyze", "large", "datasets", "algorithms", "exploratory",
            "analysis", "deep", "frameworks", "solve", "problems", "communicate",
            "findings", "non-technical", "stakeholders",
        ]),
    ],
)
def test_find_missing_keywords(resume, job, expected):
    assert scorer.find_missing_keywords(read_resume(resume), read_job(job)) == expected


def _inputs(resume, job=None):
    text = read_resume(resume)
    analysis = analyze_resume(text)
    stats = scorer._experience_stats(analysis["work_experience"])
    if job is None:
        return analysis, stats, None, []
    jd_text = read_job(job)
    jd = parse_job_description(jd_text)
    skill_match = match_required_skills(
        jd["required_skills"]["technical"], analysis["skills"]["technical"]
    )
    return analysis, stats, skill_match, scorer.find_missing_keywords(text, jd_text)


UNSTRUCTURED_BACKEND_01 = [
    "No work experience could be parsed. Add a clearly labelled 'Work Experience' "
    "section with a dated entry for each role.",
    "Add a couple of soft skills (e.g. leadership, communication, teamwork); ideally "
    "evidenced in your experience bullets rather than just listed.",
    "No education detected. Add a clearly labelled Education section.",
    "No email address found. Make your contact details clearly visible.",
    "No phone number found. Add a reachable contact number.",
    "At 62 words the resume is very thin; expand on your experience and projects.",
]

JUNIOR_BULLETS = [
    "5 of your 6 experience bullets have no measurable result, e.g. \"Implemented REST "
    "API endpoints in Django for a…\" Add numbers (%, $, time saved, team size) to "
    "show impact.",
    "Lead bullets with a strong action verb. Rewrite \"Wrote SQL queries and migrations "
    "against a PostgreSQL…\" to start with verbs like 'Led', 'Built' or 'Improved'.",
]

JUNIOR_MISSING = (
    "The posting stresses microservices, ci/cd, aws, databases, cloud, distributed, "
    "none of which appear in your resume. Add the ones you have real experience with, "
    "in context (not a keyword list)."
)


def test_general_suggestions_unstructured_resume():
    analysis, stats, _, _ = _inputs("backend_01")
    assert scorer.generate_general_suggestions(analysis, stats) == UNSTRUCTURED_BACKEND_01


def test_general_suggestions_structured_resume():
    analysis, stats, _, _ = _inputs("backend_03_junior")
    assert scorer.generate_general_suggestions(analysis, stats) == JUNIOR_BULLETS


def test_general_suggestions_strong_resume_is_empty():
    analysis, stats, _, _ = _inputs("fullstack_01")
    assert scorer.generate_general_suggestions(analysis, stats) == []
    assert scorer.STRONG_RESUME == (
        "Strong resume: it covers contact details, skills, education and quantified "
        "experience."
    )


def test_job_suggestions_skills_listed_but_not_evidenced():
    analysis, _, skill_match, missing = _inputs("backend_03_junior", "backend_jd")
    assert skill_match == {
        "matched": ["python", "sql", "docker"],
        "missing": ["aws", "ci/cd", "microservices"],
        "coverage": 50.0,
    }
    assert scorer.generate_job_suggestions(analysis, 20.0, missing, skill_match) == [
        "You list 50% of the required skills, but the match score is only ~20% because "
        "your experience doesn't show you using them. Add a bullet for python, docker "
        "saying what you built with it and what changed as a result.",
        JUNIOR_MISSING,
    ]


def test_job_suggestions_moderate_match():
    analysis, _, skill_match, missing = _inputs("backend_03_junior", "backend_jd")
    assert scorer.generate_job_suggestions(analysis, 45.0, missing, skill_match) == [
        "Moderate match (~45%). Surface more of the role's terminology where you "
        "genuinely have the experience.",
        JUNIOR_MISSING,
    ]


def test_job_suggestions_high_match():
    analysis, _, skill_match, missing = _inputs("backend_03_junior", "backend_jd")
    assert scorer.generate_job_suggestions(analysis, 80.0, missing, skill_match) == [
        JUNIOR_MISSING,
    ]


def test_job_suggestions_low_match_without_skill_coverage():
    analysis, _, _, missing = _inputs("backend_03_junior", "backend_jd")
    assert scorer.generate_job_suggestions(analysis, 20.0, missing, None) == [
        "Your resume matches only ~20% of this job description. Rework your summary and "
        "experience to mirror its language and priorities.",
        JUNIOR_MISSING,
    ]
