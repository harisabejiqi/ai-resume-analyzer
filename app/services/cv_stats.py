"""Statistics and readability checks for a CV, computed from the CV alone.

The checks are simple rules of thumb, not a real ATS.
"""

from .scorer import _experience_stats

MIN_WORDS = 150
MAX_WORDS = 1000
MAX_BULLET_WORDS = 40
MAX_PARAGRAPH_WORDS = 80
CORE_SECTIONS = ("experience", "education", "skills")


def compute_statistics(text, analysis):
    """Counts describing the CV, taken from the analyzer output."""
    exp = _experience_stats(analysis["work_experience"])
    bullets = [b for e in analysis["work_experience"] or [] for b in e.get("bullets", [])]
    return {
        "word_count": analysis["word_count"],
        "line_count": sum(1 for line in text.split("\n") if line.strip()),
        "sections": list(analysis["sections"]),
        "roles": exp["entries"],
        "bullet_count": exp["bullet_count"],
        "avg_bullets_per_role": round(exp["avg_bullets"], 1),
        "avg_words_per_bullet": (
            round(sum(len(b.split()) for b in bullets) / len(bullets), 1) if bullets else 0.0
        ),
        "quantified_bullets_pct": round(100 * exp["metric_ratio"], 1),
        "action_verb_bullets_pct": round(100 * exp["verb_ratio"], 1),
        "technical_skills": len(analysis["skills"]["technical"]),
        "soft_skills": len(analysis["skills"]["soft"]),
        "education_entries": len(analysis["education"]),
        "experience_years": analysis["experience_years"],
    }


def _check(check_id, label, passed, detail):
    return {"id": check_id, "label": label, "passed": passed, "detail": detail}


def readability_checks(text, analysis):
    """Pass/fail readability checks, not a commercial ATS. The limits are
    module constants, chosen by hand."""
    exp = _experience_stats(analysis["work_experience"])
    bullets = [b for e in analysis["work_experience"] or [] for b in e.get("bullets", [])]
    checks = []

    missing_contact = [k for k in ("email", "phone") if not analysis[k]]
    checks.append(_check(
        "contact", "Contact details", not missing_contact,
        "Email and phone number found." if not missing_contact
        else f"Not found: {', '.join(missing_contact)}.",
    ))

    sections = set(analysis["sections"])
    has_experience = any("experience" in s or s == "work history" for s in sections)
    missing_sections = [
        s for s in CORE_SECTIONS
        if not (has_experience if s == "experience" else s in sections)
    ]
    checks.append(_check(
        "sections", "Standard section headings", not missing_sections,
        "Experience, Education and Skills headings found." if not missing_sections
        else f"No heading found for: {', '.join(missing_sections)}.",
    ))

    words = analysis["word_count"]
    checks.append(_check(
        "length", "Length", MIN_WORDS <= words <= MAX_WORDS,
        f"{words} words (recommended {MIN_WORDS} to {MAX_WORDS}).",
    ))

    if exp["entries"] == 0:
        checks.append(_check("bullets", "Bullet points in experience", False,
                             "No work experience could be parsed."))
        checks.append(_check("dates", "Dates on every role", False,
                             "No work experience could be parsed."))
    else:
        checks.append(_check(
            "bullets", "Bullet points in experience", exp["roles_without_bullets"] == 0,
            f"{exp['bullet_count']} bullets across {exp['entries']} role(s)."
            if exp["roles_without_bullets"] == 0
            else f"{exp['roles_without_bullets']} of {exp['entries']} role(s) have no bullets.",
        ))
        checks.append(_check(
            "dates", "Dates on every role", exp["roles_without_dates"] == 0,
            "Every role has a start date." if exp["roles_without_dates"] == 0
            else f"{exp['roles_without_dates']} of {exp['entries']} role(s) have no dates.",
        ))

    long_bullets = [b for b in bullets if len(b.split()) > MAX_BULLET_WORDS]
    checks.append(_check(
        "bullet_length", "Concise bullets", not long_bullets,
        f"No bullet is longer than {MAX_BULLET_WORDS} words." if not long_bullets
        else f"{len(long_bullets)} bullet(s) are longer than {MAX_BULLET_WORDS} words.",
    ))

    long_lines = [l for l in text.split("\n") if len(l.split()) > MAX_PARAGRAPH_WORDS]
    checks.append(_check(
        "paragraphs", "No dense paragraphs", not long_lines,
        f"No paragraph is longer than {MAX_PARAGRAPH_WORDS} words." if not long_lines
        else f"{len(long_lines)} paragraph(s) are longer than {MAX_PARAGRAPH_WORDS} words; "
             "split them into bullets.",
    ))

    return checks
