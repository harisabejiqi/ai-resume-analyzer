import os
import tempfile
from flask import Blueprint, request, jsonify
from app.services.parser import extract_text
from app.services.analyzer import analyze_resume
from app.services.scorer import score_resume
from app.services.grammar import check_grammar
from app.services.jd_parser import parse_job_description, match_required_skills

main = Blueprint("main", __name__)
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
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
        return jsonify({"error": "Only PDF, DOC, and DOCX files are allowed"}), 400

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
                "error": "We couldn't extract text from this file — it may be a scanned image. Try OCR or upload a text-based PDF.",
            }), 422

        analysis = analyze_resume(resume_text)

        jd_result = None
        if job_description.strip():
            jd_result = parse_job_description(job_description)
            jd_result["skill_match"] = match_required_skills(
                jd_result["required_skills"]["technical"],
                analysis["skills"]["technical"],
            )

        score_result = score_resume(
            resume_text, job_description, analysis,
            skill_match=jd_result["skill_match"] if jd_result else None,
        )


        grammar_result = check_grammar(resume_text)
        if grammar_result["issue_count"]:
            examples = ", ".join(
                f"'{i['text']}' → '{i['suggestions'][0]}'"
                for i in grammar_result["issues"][:3]
                if i["suggestions"]
            )
            msg = f"Fix {grammar_result['issue_count']} grammar/spelling issue(s)"
            score_result["suggestions"].insert(0, f"{msg} (e.g. {examples})." if examples else f"{msg}.")


        return jsonify({
            "analysis": analysis,
            "score": score_result,
            "job_description": jd_result,
            "grammar": grammar_result,
        })
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
