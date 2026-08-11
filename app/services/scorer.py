import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import calibration, embeddings


STOPWORDS = set(
    """
a an the and or but if while of in on at to for with by from as is are was were be been being
have has had do does did will would could should may might must shall can need this that these
those it its their there here our your my his her i you we they them us about into out up down
off over under again further then once all any both each few more most other some such no nor
not only own same so than too very also more new use using used like make made get got
""".split()
)

ACTION_VERBS = {
    "led", "built", "developed", "designed", "implemented", "launched", "managed",
    "created", "improved", "increased", "reduced", "optimized", "optimised",
    "delivered", "architected", "drove", "owned", "shipped", "spearheaded",
    "established", "automated", "mentored", "scaled", "engineered", "streamlined",
    "accelerated", "initiated", "coordinated", "directed", "executed", "generated",
    "negotiated", "oversaw", "produced", "resolved", "transformed", "analyzed",
    "analysed", "founded", "headed", "introduced", "maximized", "modernized",
    "pioneered", "boosted", "cut", "grew", "saved", "won", "migrated", "deployed",
}


def _has_metric(bullet):
    """A bullet is 'quantified' if it contains a number that isn't just a year."""
    cleaned = re.sub(r"\b(?:19|20)\d{2}\b", "", bullet)
    return bool(re.search(r"\d", cleaned))


def _starts_with_action_verb(bullet):
    m = re.match(r"\s*([A-Za-z]+)", bullet)
    return bool(m and m.group(1).lower() in ACTION_VERBS)


def _experience_stats(work_experience):
    """Aggregate quality signals over the structured work-experience entries."""
    entries = work_experience or []
    bullets = [b for e in entries for b in e.get("bullets", [])]
    n = len(bullets)
    return {
        "entries": len(entries),
        "bullet_count": n,
        "metric_ratio": (sum(_has_metric(b) for b in bullets) / n) if n else 0.0,
        "verb_ratio": (sum(_starts_with_action_verb(b) for b in bullets) / n) if n else 0.0,
        "roles_without_dates": sum(1 for e in entries if not e.get("start")),
        "roles_without_bullets": sum(1 for e in entries if not e.get("bullets")),
        "avg_bullets": (n / len(entries)) if entries else 0.0,
    }


def _experience_quality(stats):
    """0-100 content-quality score for the work-experience section."""
    if stats["entries"] == 0:
        return 0.0
    if stats["bullet_count"] == 0:
        return 30.0
    depth = min(stats["avg_bullets"] / 3.0, 1.0)
    return round(
        100 * (0.4 * stats["metric_ratio"] + 0.4 * stats["verb_ratio"] + 0.2 * depth),
        1,
    )


def calculate_tfidf_match_score(resume_text, job_description):
    """Lexical baseline: TF-IDF + cosine similarity (0-100).

    Kept as the comparison baseline against the semantic (embedding) score. It
    only rewards shared surface words, so paraphrased experience scores low.
    """
    if not job_description.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, job_description])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(score * 100, 2)


def calculate_match_score(resume_text, job_description):
    """Semantic relevance between resume and job description (0-100).

    Uses transformer embeddings (see embeddings.py) so meaning, not just shared
    keywords, drives the score, then applies a fitted calibration (see
    calibration.py) so the number is interpretable on a 0-100 scale rather than
    a raw cosine that compresses strong matches into the 50s. Falls back to the
    TF-IDF baseline if the model cannot be loaded, so the app degrades
    gracefully rather than failing.
    """
    if not job_description.strip():
        return 0.0
    try:
        raw = embeddings.semantic_similarity(resume_text, job_description)
        return calibration.calibrate(raw)
    except Exception:
        return calculate_tfidf_match_score(resume_text, job_description)


def find_missing_keywords(resume_text, job_description, top_n=15):
    """Return up to top_n keywords frequent in the JD but absent from the resume.

    Ranks by raw frequency in the JD (with stopword and short-token filtering) and
    checks presence in the resume with word-boundary matching so 'java' does not
    count as present when only 'javascript' appears.
    """
    if not job_description.strip():
        return []

    tokens = re.findall(r"[a-z][a-z0-9+./#-]{2,}", job_description.lower())
    tokens = [re.sub(r"[^a-z0-9+#]+$", "", t) for t in tokens]
    tokens = [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]
    if not tokens:
        return []

    resume_lower = resume_text.lower()
    missing = []
    for word, _ in Counter(tokens).most_common():
        pattern = rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])"
        if not re.search(pattern, resume_lower):
            missing.append(word)
        if len(missing) >= top_n:
            break
    return missing


def _role_label(entry):
    """Human-readable label for a role, e.g. 'Backend Developer at Acme'."""
    title = (entry.get("title") or "").strip()
    company = (entry.get("company") or "").strip()
    if title and company:
        return f"{title} at {company}"
    return title or company or "an unlabeled role"


def _join_roles(entries, limit=2):
    """Quote up to `limit` role labels, summarising the rest as '+N more'."""
    labels = [f"'{_role_label(e)}'" for e in entries[:limit]]
    extra = len(entries) - limit
    if extra > 0:
        labels.append(f"and {extra} more")
    return ", ".join(labels)


def _snippet(text, words=8):
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def generate_suggestions(analysis, match_score, missing_keywords, has_jd, exp_stats):
    """Build prioritized, content-specific improvement suggestions.

    Rather than emitting fixed sentences, each suggestion references what *this*
    resume actually contains — named roles, real weak bullets, the actual missing
    keywords, concrete counts — so two different resumes produce different advice.
    Suggestions are appended most-impactful-first and capped, so the user sees
    the few changes that matter rather than a generic checklist.
    """
    suggestions = []
    work_experience = analysis.get("work_experience", [])

    if has_jd:
        if match_score < 30:
            suggestions.append(
                f"Your resume matches only ~{match_score:.0f}% of this job description. "
                "Rework your summary and experience to mirror its language and priorities."
            )
        elif match_score < 60:
            suggestions.append(
                f"Moderate match (~{match_score:.0f}%). Surface more of the role's "
                "terminology where you genuinely have the experience."
            )

        if missing_keywords:
            top = missing_keywords[:6]
            shown = ", ".join(top)
            suggestions.append(
                f"The posting stresses {shown} — none of which appear in your resume. "
                "Add the ones you have real experience with, in context (not a keyword list)."
            )

    if exp_stats["entries"] == 0:
        suggestions.append(
            "No work experience could be parsed. Add a clearly labelled 'Work "
            "Experience' section with a dated entry for each role."
        )
    else:
        no_dates = [e for e in work_experience if not e.get("start")]
        if no_dates:
            suggestions.append(
                f"Add start/end dates to {_join_roles(no_dates)} so your timeline and "
                "total experience can be calculated."
            )

        no_bullets = [e for e in work_experience if not e.get("bullets")]
        if no_bullets:
            suggestions.append(
                f"{_join_roles(no_bullets)} has no description. Add 2–4 bullets covering "
                "what you did and the impact it had."
            )

        all_bullets = [b for e in work_experience for b in e.get("bullets", [])]
        no_metric = [b for b in all_bullets if not _has_metric(b)]
        if all_bullets and len(no_metric) / len(all_bullets) > 0.7:
            example = _snippet(no_metric[0])
            suggestions.append(
                f"{len(no_metric)} of your {len(all_bullets)} experience bullets have no "
                f"measurable result — e.g. \"{example}\" Add numbers (%, $, time saved, "
                "team size) to show impact."
            )

        weak_verb = next(
            (b for e in work_experience for b in e.get("bullets", [])
             if not _starts_with_action_verb(b)),
            None,
        )
        if weak_verb and exp_stats["verb_ratio"] < 0.5:
            suggestions.append(
                f"Lead bullets with a strong action verb. Rewrite \"{_snippet(weak_verb)}\" "
                "to start with verbs like 'Led', 'Built' or 'Improved'."
            )

    n_tech = len(analysis["skills"]["technical"])
    if n_tech < 3:
        suggestions.append(
            f"Only {n_tech} technical skill{'s' if n_tech != 1 else ''} detected. List the "
            "concrete tools, languages and frameworks you've used in a dedicated Skills section."
        )
    if len(analysis["skills"]["soft"]) < 2:
        suggestions.append(
            "Add a couple of soft skills (e.g. leadership, communication, teamwork) — "
            "ideally evidenced in your experience bullets rather than just listed."
        )

    if not analysis["education"]:
        suggestions.append("No education detected — add a clearly labelled Education section.")
    if not analysis["email"]:
        suggestions.append("No email address found. Make your contact details clearly visible.")
    if not analysis["phone"]:
        suggestions.append("No phone number found. Add a reachable contact number.")

    if analysis["word_count"] < 150:
        suggestions.append(
            f"At {analysis['word_count']} words the resume is very thin — expand on your "
            "experience and projects."
        )
    elif analysis["word_count"] > 1000:
        suggestions.append(
            f"At {analysis['word_count']} words the resume is long — tighten it toward 1–2 pages."
        )

    if not suggestions:
        return ["Strong resume — it covers contact details, skills, education and quantified experience."]

    return suggestions[:6]


def score_resume(resume_text, job_description, analysis):
    """Score the resume.

    Each category is normalized to 0-100 against an achievable max. The total is a
    weighted average over the categories that apply (the 'relevance' category is
    only included when a job description is provided), so it is always on a
    consistent 0-100 scale.
    """
    has_jd = bool(job_description.strip())
    match_score = calculate_match_score(resume_text, job_description) if has_jd else 0.0
    missing_keywords = find_missing_keywords(resume_text, job_description)

    exp_stats = _experience_stats(analysis["work_experience"])
    duration_score = min(analysis["experience_years"] / 5 * 100, 100)
    if exp_stats["entries"]:
        experience_score = 0.6 * duration_score + 0.4 * _experience_quality(exp_stats)
    else:
        experience_score = duration_score

    categories = {
        "skills": min(len(analysis["skills"]["technical"]) / 5 * 100, 100),
        "education": 100.0 if analysis["education"] else 0.0,
        "experience": experience_score,
    }
    if has_jd:
        categories["relevance"] = float(match_score)

    if has_jd:
        weights = {"skills": 0.30, "education": 0.20, "experience": 0.20, "relevance": 0.30}
    else:
        weights = {"skills": 30 / 70, "education": 20 / 70, "experience": 20 / 70}

    total_score = sum(categories[k] * weights[k] for k in categories)

    breakdown = {k: round(v, 1) for k, v in categories.items()}
    suggestions = generate_suggestions(analysis, match_score, missing_keywords, has_jd, exp_stats)

    return {
        "total_score": round(total_score, 1),
        "match_score": match_score,
        "has_job_description": has_jd,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
        "breakdown": breakdown,
    }
