"""Flask test-client tests for POST /api/analyze.

File parsing and the grammar engine are mocked so the tests are fast and
offline; the semantic matcher runs on the fake encoder from conftest.py.
"""

import io
import os

import pytest

from app import create_app
from app import routes
from app.services import scorer

from conftest import read_job, read_resume

NO_ISSUES = {"available": True, "issue_count": 0, "issues": []}


@pytest.fixture
def seen_paths():
    return []


@pytest.fixture
def client(monkeypatch, fake_embeddings, seen_paths):
    resume_text = read_resume("backend_03_junior")

    def fake_extract(path):
        seen_paths.append(path)
        return resume_text

    monkeypatch.setattr(routes, "extract_text", fake_extract)
    monkeypatch.setattr(routes, "check_grammar", lambda text: NO_ISSUES)
    return create_app().test_client()


def _post(client, filename="cv.pdf", job_description=None):
    data = {"resume": (io.BytesIO(b"%PDF-1.4 test"), filename)}
    if job_description is not None:
        data["job_description"] = job_description
    return client.post("/api/analyze", data=data, content_type="multipart/form-data")


def test_cv_only(client, seen_paths):
    response = _post(client)
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"analysis", "grammar", "cv_quality", "job_description", "job_match"}
    assert set(body["cv_quality"]) == {
        "score", "breakdown", "statistics", "summary", "checks", "suggestions",
    }
    assert body["cv_quality"]["score"] == 82.0
    assert body["job_description"] is None
    assert body["job_match"] is None
    assert not os.path.exists(seen_paths[0])


def test_cv_with_job_description(client):
    jd = read_job("backend_jd")
    body = _post(client, job_description=jd).get_json()
    assert body["job_match"]["score"] == \
        scorer.calculate_match_score(read_resume("backend_03_junior"), jd)
    assert body["job_match"]["disclaimer"] == scorer.JOB_MATCH_DISCLAIMER
    assert body["job_match"]["reliability"] == "normal"
    assert body["job_description"]["required_skills"]["technical"]
    assert body["cv_quality"]["score"] == 82.0


def test_job_match_does_not_change_cv_quality(client):
    without = _post(client).get_json()["cv_quality"]
    with_jd = _post(client, job_description=read_job("nurse_jd")).get_json()["cv_quality"]
    assert without == with_jd


@pytest.mark.parametrize("jd", ["", "   \n\t "])
def test_empty_job_description_is_no_posting(client, jd):
    body = _post(client, job_description=jd).get_json()
    assert body["job_description"] is None
    assert body["job_match"] is None


def test_too_short_job_description(client):
    body = _post(client, job_description="Python").get_json()
    assert body["job_match"]["score"] is None
    assert body["job_match"]["reliability_note"] == scorer.TOO_SHORT_NOTE


@pytest.mark.parametrize("filename", ["cv.txt", "cv.doc"])
def test_wrong_file_type(client, filename):
    response = _post(client, filename=filename)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Only PDF and DOCX files are allowed"}


def test_no_file(client):
    response = client.post("/api/analyze", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json() == {"error": "No file uploaded"}


def test_job_description_too_long(client):
    response = _post(client, job_description="x" * (routes.MAX_JD_BYTES + 1))
    assert response.status_code == 413
    assert response.get_json() == {"error": "Job description is too long (max 50 KB)."}


def test_unreadable_file_is_deleted(monkeypatch, client, seen_paths):
    def broken(path):
        seen_paths.append(path)
        raise ValueError("corrupt")

    monkeypatch.setattr(routes, "extract_text", broken)
    response = _post(client)
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "We couldn't read this file. It may be corrupted or password-protected.",
    }
    assert not os.path.exists(seen_paths[0])


def test_scanned_file(monkeypatch, client):
    monkeypatch.setattr(routes, "extract_text", lambda path: "   ")
    response = _post(client)
    assert response.status_code == 422
    assert response.get_json()["error"].startswith("We couldn't extract text from this file.")
