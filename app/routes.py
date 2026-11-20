import os
import tempfile
from flask import Blueprint, request, jsonify
from app.services.parser import extract_text
from app.services.analyzer import analyze_resume
from app.services.scorer import score_cv_quality, score_job_match
from app.services.cv_stats import compute_statistics, readability_checks
from app.services.summary import extractive_summary
from app.services.grammar import check_grammar
from app.services.jd_parser import parse_job_description

main = Blueprint("main", __name__)
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_JD_BYTES = 50 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _ext(filename):
    return filename.rsplit(".", 1)[1].lower()


@main.route("/api/analyze", methods=["POST"])
def api_analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files are allowed"}), 400

    if len(job_description.encode("utf-8")) > MAX_JD_BYTES:
        return jsonify({
            "error": f"Job description is too long (max {MAX_JD_BYTES // 1024} KB).",
        }), 413

    suffix = "." + _ext(file.filename)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        file.save(tmp)
        tmp.close()

        try:
            resume_text = extract_text(tmp.name)
        except Exception:
            return jsonify({
                "error": "We couldn't read this file. It may be corrupted or password-protected.",
            }), 422

        if len(resume_text.strip()) < 50:
            return jsonify({
                "error": "We couldn't extract text from this file. It may be a scanned image. Try OCR or upload a text-based PDF.",
            }), 422

        analysis = analyze_resume(resume_text)
        grammar_result = check_grammar(resume_text)

        quality = score_cv_quality(analysis, grammar_result)
        cv_quality = {
            "score": quality["score"],
            "breakdown": quality["breakdown"],
            "statistics": compute_statistics(resume_text, analysis),
            "summary": extractive_summary(resume_text),
            "checks": readability_checks(resume_text, analysis),
            "suggestions": quality["suggestions"],
        }

        jd_result = None
        job_match = None
        if job_description.strip():
            jd_result = parse_job_description(job_description)
            job_match = score_job_match(resume_text, job_description, analysis, jd_result)

        return jsonify({
            "analysis": analysis,
            "grammar": grammar_result,
            "cv_quality": cv_quality,
            "job_description": jd_result,
            "job_match": job_match,
        })
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
