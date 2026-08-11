"""Parse a free-text job posting into structured requirements.

Extracts the skills, years of experience, education level, and qualification
bullets a posting asks for, so the rest of the pipeline can compare them
against what the candidate's resume actually contains. Skill detection reuses
the same keyword lists as the resume analyzer so the two sides line up.
"""
import re

from app.services.analyzer import TECH_SKILLS, SOFT_SKILLS, _has_skill


_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)


_EDU_LEVELS = [
    ("phd", "PhD"),
    ("ph.d", "PhD"),
    ("doctorate", "PhD"),
    ("mba", "MBA"),
    ("master", "Master's degree"),
    ("m.sc", "Master's degree"),
    ("m.tech", "Master's degree"),
    ("m.s", "Master's degree"),
    ("m.e", "Master's degree"),
    ("bachelor", "Bachelor's degree"),
    ("b.sc", "Bachelor's degree"),
    ("b.tech", "Bachelor's degree"),
    ("b.e", "Bachelor's degree"),
    ("b.s", "Bachelor's degree"),
    ("associate", "Associate degree"),
    ("diploma", "Diploma"),
    ("degree", "Degree"),
    ("certification", "Certification"),
    ("certified", "Certification"),
]

_REQ_HEADER_RE = re.compile(
    r"(requirements|qualifications|what (?:you|we).{0,20}(?:need|looking|have)|"
    r"must[- ]?haves?|who you are|skills (?:and|&) qualifications|"
    r"minimum qualifications|you (?:should )?have|we(?:'|’)?re looking for)",
    re.IGNORECASE,
)
_STOP_HEADER_RE = re.compile(
    r"(responsibilities|what you(?:'|’)?ll do|benefits|perks|what we offer|"
    r"about (?:us|the|our)|compensation|salary|how to apply|nice[- ]to[- ]haves?|"
    r"the role|day[- ]to[- ]day|our team)",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*(?:[-*•–·▪◦‣]|\d+[.)])\s+(.*)")

_MAX_QUALIFICATIONS = 12
_MAX_QUAL_LEN = 220


def _dedupe(items):
    """Order-preserving de-duplication."""
    return list(dict.fromkeys(items))


def extract_required_skills(text):
    text_lower = text.lower()
    return {
        "technical": [s for s in TECH_SKILLS if _has_skill(text_lower, s)],
        "soft": [s for s in SOFT_SKILLS if _has_skill(text_lower, s)],
    }


def extract_experience_required(text):
    """Smallest "N years" figure the posting mentions, preferring ones written
    near the word 'experience'. Returns an int, or None if none is found."""
    text_lower = text.lower()
    with_context = []
    all_years = []
    for m in _YEARS_RE.finditer(text_lower):
        n = int(m.group(1))
        if not 0 < n <= 50:
            continue
        all_years.append(n)
        window = text_lower[m.start(): m.end() + 25]
        if "experience" in window or "exp" in window:
            with_context.append(n)
    pool = with_context or all_years
    return min(pool) if pool else None


_SPECIFIC_DEGREES = {
    "PhD",
    "MBA",
    "Master's degree",
    "Bachelor's degree",
    "Associate degree",
    "Diploma",
}


def _has_edu(text_lower, keyword):
    pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?:'s|’s|s)?(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def extract_education_required(text):
    text_lower = text.lower()
    labels = _dedupe(
        [label for kw, label in _EDU_LEVELS if _has_edu(text_lower, kw)]
    )
    if any(label in _SPECIFIC_DEGREES for label in labels):
        labels = [label for label in labels if label != "Degree"]
    return labels


def extract_qualifications(text):
    """Pull qualification/requirement bullet lines from the posting.

    Lines inside a "Requirements"/"Qualifications" block are collected, as are
    bullet-style lines anywhere in the text. Falls back gracefully when the
    posting has no clear structure.
    """
 
    section_quals = []
    bullet_quals = []
    in_req = False
    for raw in text.split("\n"):
        stripped = raw.strip()
        if not stripped:
            continue

        is_short = len(stripped) <= 60
        if is_short and _REQ_HEADER_RE.search(stripped):
            in_req = True
            continue
        if in_req and is_short and _STOP_HEADER_RE.search(stripped):
            in_req = False
            continue

        bullet = _BULLET_RE.match(raw)
        if in_req:
            section_quals.append(bullet.group(1).strip() if bullet else stripped)
        elif bullet:
            bullet_quals.append(bullet.group(1).strip())

    quals = section_quals or bullet_quals
    cleaned = [q[:_MAX_QUAL_LEN].strip() for q in quals if len(q) >= 4]
    return _dedupe(cleaned)[:_MAX_QUALIFICATIONS]


def match_required_skills(required_technical, resume_technical):
    """Compare the JD's required technical skills against the resume's.

    Returns the matched and missing skills plus a 0-100 coverage percentage
    (None when the posting lists no recognised technical skills).
    """
    required = list(dict.fromkeys(required_technical))
    resume_set = set(resume_technical)
    matched = [s for s in required if s in resume_set]
    missing = [s for s in required if s not in resume_set]
    coverage = round(len(matched) / len(required) * 100, 1) if required else None
    return {"matched": matched, "missing": missing, "coverage": coverage}


def parse_job_description(text):
    """Extract structured requirements from a job posting."""
    return {
        "required_skills": extract_required_skills(text),
        "experience_required": extract_experience_required(text),
        "education_required": extract_education_required(text),
        "qualifications": extract_qualifications(text),
    }
