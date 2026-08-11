import datetime
import re

TECH_SKILLS = [
    "python", "java", "javascript", "react", "node.js", "django", "flask",
    "sql", "mongodb", "aws", "docker", "kubernetes", "git", "html", "css",
    "tensorflow", "pytorch", "machine learning", "deep learning", "api",
    "linux", "c++", "typescript", "postgresql", "redis", "graphql",
    "angular", "vue.js", "spring boot", "express.js", ".net", "azure",
    "gcp", "firebase", "elasticsearch", "rabbitmq", "kafka", "nginx",
    "jenkins", "ci/cd", "terraform", "ansible", "pandas", "numpy",
    "scikit-learn", "opencv", "nlp", "rest api", "microservices"
]

SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem solving",
    "critical thinking", "time management", "adaptability", "creativity",
    "collaboration", "project management", "analytical", "detail oriented",
    "self motivated", "multitasking", "decision making", "negotiation",
    "mentoring", "presentation", "strategic thinking", "conflict resolution"
]

EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "b.sc", "m.sc", "b.tech", "m.tech",
    "mba", "diploma", "degree", "university", "college", "institute",
    "b.e", "m.e", "b.s", "m.s", "associate", "certification", "certified"
]

SECTION_HEADERS = [
    "experience", "education", "skills", "projects", "certifications",
    "summary", "objective", "awards", "publications", "languages",
    "interests", "references", "work history", "professional experience"
]


def extract_email(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.findall(pattern, text)
    return match[0] if match else None


_PHONE_REGIONS = ("XK", "AL", "US")


def _extract_phone_regex(text):
    """Fallback used only if the phonenumbers library is unavailable.

    Two phone shapes; lookarounds keep matches from splicing across longer digit
    runs (ZIP+4, dates, IDs, year ranges):
      1. US/local: optional +CC, then (NNN) or NNN<sep>, then NNN<sep>NNNN.
      2. International: +CC<sep> followed by 6-14 digits with optional separators.
    """
    pattern = (
        r"(?<!\d)(?:"
        r"(?:\+\d{1,3}[-.\s]?)?(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.\s]\d{4}"
        r"|"
        r"\+\d{1,3}[-.\s]\d(?:[-.\s]?\d){5,13}"
        r")(?!\d)"
    )
    match = re.findall(pattern, text)
    return match[0] if match else None


def extract_phone(text):
    """Find a phone number in free resume text and return it in international form.

    Uses Google's libphonenumber (phonenumbers) to locate and *validate* numbers,
    which handles local formats written without a country code (e.g. Kosovo
    "044 123 456", Albania "069 20 12 345") that a rigid regex misses, while
    rejecting dates, IDs and ZIP codes. Regions are tried in likelihood order so
    a bare local number is interpreted correctly. Falls back to a regex if the
    library is missing.
    """
    try:
        import phonenumbers
    except ImportError:
        return _extract_phone_regex(text)

    fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL


    for region in _PHONE_REGIONS:
        for match in phonenumbers.PhoneNumberMatcher(text, region):
            if phonenumbers.is_valid_number(match.number):
                return phonenumbers.format_number(match.number, fmt)


    explicit_cc = {
        phonenumbers.CountryCodeSource.FROM_NUMBER_WITH_PLUS_SIGN,
        phonenumbers.CountryCodeSource.FROM_NUMBER_WITH_IDD,
    }
    for region in _PHONE_REGIONS:
        for match in phonenumbers.PhoneNumberMatcher(
            text, region, leniency=phonenumbers.Leniency.POSSIBLE
        ):
            num = match.number
            if num.country_code_source in explicit_cc and phonenumbers.is_possible_number(num):
                return phonenumbers.format_number(num, fmt)

    return None


def extract_name(text):
    """Try to extract name from the first few lines of the resume."""
    lines = text.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if not line or "@" in line or re.search(r"\d{3}", line):
            continue
        if "http" in line.lower() or "linkedin" in line.lower():
            continue
        if len(line.split()) <= 4 and re.match(r"^[A-Za-z\s.'-]+$", line):
            return line
    return None


def _has_skill(text_lower, skill):
    pattern = rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def extract_skills(text):
    text_lower = text.lower()
    found_tech = [s for s in TECH_SKILLS if _has_skill(text_lower, s)]
    found_soft = [s for s in SOFT_SKILLS if _has_skill(text_lower, s)]
    return {"technical": found_tech, "soft": found_soft}


def extract_education(text):
    lines = text.split("\n")
    education = []
    for line in lines:
        if any(kw in line.lower() for kw in EDUCATION_KEYWORDS):
            if len(line.strip()) > 5:
                education.append(line.strip())
    return education


_EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?"
)
_EXPERIENCE_HEADER_RE = re.compile(
    r"^\s*(?:work\s+experience|professional\s+experience|work\s+history|"
    r"employment(?:\s+history)?|experience)\s*:?\s*$",
    re.IGNORECASE,
)
_OTHER_SECTION_HEADER_RE = re.compile(
    r"^\s*(?:education|skills|technical\s+skills|projects|certifications?|"
    r"summary|objective|awards|achievements|publications|languages|"
    r"interests|references)\s*:?\s*$",
    re.IGNORECASE,
)

_REQUIREMENT_CONTEXT = re.compile(
    r"(?:requir\w*|minimum|at least|must have|needs?|preferred|"
    r"seeking|looking for|candidates?\s+with)\s+\w*\s*$"
)

_MONTH_TO_NUM = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTH_TO_NUM, key=len, reverse=True))
_PRESENT_WORDS = ("present", "current", "now", "ongoing")


_DATE_POINT = (
    rf"(?:(?:{_MONTH_ALT})\.?|\d{{1,2}})?[\s./-]*(?:19|20)\d{{2}}"
    rf"|present|current|now|ongoing"
)

_DATE_RANGE_RE = re.compile(
    rf"(?P<start>{_DATE_POINT})\s*(?:-|–|—|to|until|through)\s*(?P<end>{_DATE_POINT})",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*[-•*·▪◦‣]\s+")
_SEPARATORS_RE = re.compile(r"\s*(?:\||•|·|–|—|,|@|\bat\b)\s*", re.IGNORECASE)


def _date_point_to_months(token):
    """Convert a single date point to an absolute month index (year*12 + month-1)."""
    t = token.strip().lower()
    if any(w in t for w in _PRESENT_WORDS):
        today = datetime.date.today()
        return today.year * 12 + (today.month - 1)
    year_match = re.search(r"(?:19|20)\d{2}", t)
    if not year_match:
        return None
    year = int(year_match.group(0))
    month = 1
    name = re.search(rf"(?:{_MONTH_ALT})", t)
    if name:
        month = _MONTH_TO_NUM[name.group(0)]
    else:
        num = re.match(r"\s*(\d{1,2})[\s./-]", t)
        if num and 1 <= int(num.group(1)) <= 12:
            month = int(num.group(1))
    return year * 12 + (month - 1)


def _interval(start_raw, end_raw):
    """Parse a (start, end) pair into an absolute-month interval, or None."""
    if not start_raw or not end_raw:
        return None
    start = _date_point_to_months(start_raw)
    end = _date_point_to_months(end_raw)
    if start is None or end is None or end < start:
        return None
    return (start, end)


def _total_experience_months(entries):
    """Total months across roles, merging overlaps so concurrent jobs don't
    double-count (e.g. 2018-2022 + 2020-2024 = 6 years, not 8)."""
    intervals = sorted(
        iv for iv in (_interval(e.get("start"), e.get("end")) for e in entries) if iv
    )
    if not intervals:
        return 0
    total = 0
    cur_start, cur_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= cur_end:  
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
    total += cur_end - cur_start
    return total



def _looks_like_sentence(line):
    return len(line) > 50 or line.rstrip().endswith(".")


_CONTINUATION_TAILS = (",", "&", "/", "-", "–", "—", ":", ";")


def _continues_bullet(prev_bullet, line):
    """True if `line` is a wrapped continuation of the previous bullet rather
    than a new bullet — i.e. it starts mid-sentence (lowercase) or the previous
    fragment ended on a connector with no terminal punctuation. Used to rejoin
    a single bullet that a PDF wrapped across several physical lines."""
    if not prev_bullet:
        return False
    if line[:1].islower():
        return True
    return prev_bullet.rstrip()[-1:] in _CONTINUATION_TAILS


def _split_header(line, range_match):
    """Split a role header line (after removing its date range) into title/company."""
    header = (line[:range_match.start()] + " " + line[range_match.end():]).strip()
    header = header.strip(" \t-–—|,·•@")
    if not header:
        return None, None
    parts = [p.strip() for p in _SEPARATORS_RE.split(header) if p.strip()]
    title = parts[0] if parts else None
    company = parts[1] if len(parts) > 1 else None
    return title, company


def _parse_entries(lines):
    """Group lines into structured role entries anchored on date ranges.

    Each entry is {title, company, start, end, duration_months, bullets}.
    A line carrying a date range opens a new role; bullet-marked or descriptive
    lines below attach to it; a short non-bullet line just above a dated header
    is treated as the role title.
    """
    entries = []
    current = None
    pending_title = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        bullet = _BULLET_RE.match(line)
        rng = None if bullet else _DATE_RANGE_RE.search(line)

        if rng:
            header_title, header_company = _split_header(line, rng)
            if pending_title:
                pt_parts = [p.strip() for p in _SEPARATORS_RE.split(pending_title) if p.strip()]
                title = pt_parts[0] if pt_parts else None
                company = header_title or header_company or \
                    (pt_parts[1] if len(pt_parts) > 1 else None)
            else:
                title, company = header_title, header_company
            start_raw = rng.group("start").strip()
            end_raw = rng.group("end").strip()
            iv = _interval(start_raw, end_raw)
            current = {
                "title": title,
                "company": company,
                "start": start_raw,
                "end": end_raw,
                "duration_months": (iv[1] - iv[0]) if iv else 0,
                "bullets": [],
            }
            entries.append(current)
            pending_title = None
            continue

        if bullet:
            text = line[bullet.end():].strip()
            if current is not None and text:
                current["bullets"].append(text)
            continue

        if current is not None and current["bullets"] \
                and _continues_bullet(current["bullets"][-1], line):
            current["bullets"][-1] = current["bullets"][-1].rstrip() + " " + line
        elif current is not None and not current["bullets"] \
                and current["company"] is None and len(line) <= 60 \
                and not _looks_like_sentence(line):
            current["company"] = line
        elif current is not None and _looks_like_sentence(line):
            current["bullets"].append(line)
        elif "@" in line or "http" in line.lower() or re.search(r"\d{3}\D*\d{4}", line):
            pending_title = None
        else:
            pending_title = line
    return entries


def _experience_section_lines(text):
    """Lines under an experience header, or None if no such header exists."""
    in_section = False
    found = False
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _EXPERIENCE_HEADER_RE.match(stripped):
            in_section = True
            found = True
            continue
        if in_section:
            if _OTHER_SECTION_HEADER_RE.match(stripped):
                in_section = False
                continue
            lines.append(line)
    return lines if found else None


def _is_education_line(line):
    low = line.lower()
    return any(kw in low for kw in EDUCATION_KEYWORDS)


def extract_work_experience(text):
    """Parse work history into structured role entries.

    Prefers the explicitly-labelled experience section. If no such header exists
    (or it yields no dated roles), falls back to scanning the whole document for
    date-anchored entries, skipping education lines so degrees aren't mistaken
    for jobs.
    """
    section = _experience_section_lines(text)
    entries = _parse_entries(section) if section else []
    if not entries:
        fallback = [l for l in text.split("\n") if not _is_education_line(l)]
        entries = _parse_entries(fallback)
    return entries


def extract_experience(text, work_experience=None):
    """Estimate years of experience.

    Prefers an explicit "X years (of) experience" claim (ignoring matches inside
    job-requirement phrases). Otherwise infers from the merged duration of dated
    roles, so resumes that only list job dates still score.
    """
    text_lower = text.lower()
    explicit = []
    for m in _EXPERIENCE_PATTERN.finditer(text_lower):
        preceding = text_lower[max(0, m.start() - 40):m.start()]
        if _REQUIREMENT_CONTEXT.search(preceding):
            continue
        explicit.append(int(m.group(1)))
    explicit_years = max(explicit) if explicit else 0

    if work_experience is None:
        work_experience = extract_work_experience(text)
    inferred_years = round(_total_experience_months(work_experience) / 12, 1)

    years = max(explicit_years, inferred_years)
    return int(years) if float(years).is_integer() else years


def extract_sections(text):
    """Detect which resume sections are present."""
    text_lower = text.lower()
    found = [s for s in SECTION_HEADERS if s in text_lower]
    return found


def analyze_resume(text):
    work_experience = extract_work_experience(text)
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience(text, work_experience),
        "work_experience": work_experience,
        "sections": extract_sections(text),
        "word_count": len(text.split()),
    }
