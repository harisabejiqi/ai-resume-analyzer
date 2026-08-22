"""Section/requirement-level matching between a resume and a job description.

The whole-document matcher in `embeddings.py` encodes an entire resume into one
vector. That has two costs: the model truncates at 256 word-pieces (so a
two-page CV is scored on roughly its first half), and averaging a whole document
into one point blurs the specific bullet that actually answers a requirement.

This module compares at the level of *content units* instead:

    resume  ->  experience bullets, skills lines, education, certifications
    job     ->  individual requirement / responsibility lines

Every requirement is scored against every resume chunk, and each requirement
keeps its single best-matching chunk. The document score is the mean of those
per-requirement bests, so a resume is judged on how well it answers each thing
the posting asks for, rather than on aggregate topical similarity.

The same requirement->chunk pairing is what the UI needs to *explain* a score
("this requirement is covered by this line of your CV"), so `match_requirements`
returns the evidence alongside the number.
"""

import re

import numpy as np

from . import embeddings

_BULLET = re.compile(r"^\s*(?:[-*•–·▪◦‣]|\d+[.)])\s+")
_CV_HEADER = re.compile(
    r"^(summary|profile|work experience|experience|education|skills|"
    r"projects?|certifications?)\s*:?\s*$",
    re.IGNORECASE,
)
_JD_HEADER = re.compile(
    r"^(responsibilities|requirements|qualifications|what you.{0,20}do|"
    r"who you are|must[- ]?haves?)\s*:?\s*$",
    re.IGNORECASE,
)
_CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.\w+|\+?\d[\d\s()-]{7,}")
_DATE_LINE = re.compile(
    r"^\s*\w+\.?\s*\d{4}\s*[-–—]\s*(present|current|ongoing|\w+\.?\s*\d{4})\s*$",
    re.IGNORECASE,
)
_ROLE_LINE = re.compile(
    r"^[A-Z][\w/&. ]{2,40},\s*[A-Z][\w/&.' ]{2,40}$"
)

_MIN_WORDS = 3


def _is_continuation(prev, line):
    """True if `line` is the wrapped remainder of `prev` rather than a new unit.

    Resumes wrap long bullets across lines. Splitting on "\\n" alone would cut
    sentences in half and match half-thoughts against requirements.
    """
    if not prev:
        return False
    if prev.rstrip().endswith((".", ":", ";")):
        return False
    return line[:1].islower() or prev.rstrip().endswith(",")


def _units(text, header_re, drop_contact):
    """Split text into content units, re-joining lines wrapped from the previous."""
    units = []
    for raw in text.split("\n"):
        stripped = raw.strip()
        if not stripped:
            continue
        is_bullet = bool(_BULLET.match(raw))
        line = _BULLET.sub("", stripped)
        if not line or header_re.match(line) or _DATE_LINE.match(line):
            continue
        if drop_contact and (_CONTACT.search(line) or _ROLE_LINE.match(line)):
            continue
        if not is_bullet and units and _is_continuation(units[-1], line):
            units[-1] = units[-1].rstrip() + " " + line
            continue
        units.append(line)
    return [u for u in units if len(u.split()) >= _MIN_WORDS]


def resume_chunks(text):
    """Content units of a resume: experience bullets, skills, education, certs."""
    return _units(text, _CV_HEADER, drop_contact=True)


def job_requirements(text):
    """Individual requirement / responsibility lines of a job posting."""
    return _units(text, _JD_HEADER, drop_contact=False)


def match_requirements(resume_text, job_description):
    """Score the pair per requirement and return the supporting evidence.

    Returns a dict with the 0-100 `score` (mean of the per-requirement bests) and
    an `evidence` list of {requirement, best_chunk, score} ordered as the posting
    lists them. Returns an empty result when either side yields no chunks.

    Known limitation -- very short resumes. A 45-word CV yields 2-3 chunks against
    a posting's ~9 requirements, so most requirements find no answering line and
    the mean is low even when the candidate plainly works in the field. Two fixes
    were measured on the 243-pair gold set and both were rejected:

      * a per-requirement floor from the whole-resume embedding moved the score
        only ~2 points (a requirement is short, so it matches a whole document
        much less than a full posting does);
      * taking max(chunked, whole-document) did fix short CVs, but tripled the
        length bias against long ones (correlation between chunk count and score
        on grade-2 pairs went from -0.15 to -0.59) and forfeited chunking's
        significant ranking win (p 0.043 -> 0.068).

    Plain per-requirement pooling is kept because it ranks best and is the least
    length-biased. The residual effect is real: a sparse CV scores lower than a
    detailed CV of an equally qualified candidate, because it evidences less.
    """
    chunks = resume_chunks(resume_text)
    requirements = job_requirements(job_description)
    if not chunks or not requirements:
        return {"score": 0.0, "evidence": []}

    req_vecs = embeddings.embed(requirements)
    chunk_vecs = embeddings.embed(chunks)
    sim = req_vecs @ chunk_vecs.T

    best_idx = sim.argmax(axis=1)
    best_sim = sim.max(axis=1)

    evidence = [
        {
            "requirement": requirements[i],
            "best_chunk": chunks[int(best_idx[i])],
            "score": round(100 * max(0.0, float(best_sim[i])), 2),
        }
        for i in range(len(requirements))
    ]
    score = round(100 * max(0.0, float(np.mean(best_sim))), 2)
    return {"score": score, "evidence": evidence}


def chunked_similarity(resume_text, job_description):
    """Section-level relevance of a resume to a posting (0-100)."""
    return match_requirements(resume_text, job_description)["score"]
