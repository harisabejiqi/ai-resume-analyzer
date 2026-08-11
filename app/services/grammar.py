"""Grammar and spelling checks via LanguageTool (language_tool_python).

Runs an offline LanguageTool engine (a local Java service the library manages)
over the resume text and returns concrete grammar/spelling issues with
suggested corrections.

Resumes are noisy input for a general grammar checker: bullets are intentional
fragments, and they are full of proper nouns and technology names (ClickHouse,
GraphQL, SQL, VAST). So we keep only the issue types that genuinely matter on a
resume — spelling and grammar — and additionally drop "misspellings" that look
like technical identifiers, which are almost always false positives.
"""

from functools import lru_cache

LANG = "en-US"

_KEEP_ISSUE_TYPES = {"misspelling", "grammar", "duplication"}


@lru_cache(maxsize=1)
def _get_tool():
    """Start the LanguageTool engine once and reuse it (startup is expensive;
    the first ever call also downloads LanguageTool, a one-time cost)."""
    import language_tool_python

    return language_tool_python.LanguageTool(LANG)


def is_available():
    try:
        _get_tool()
        return True
    except Exception:
        return False


def _looks_technical(token):
    """True for tech terms / acronyms / identifiers that aren't real typos and
    would otherwise be flagged as misspellings (ClickHouse, GraphQL, SQL, k8s)."""
    if not token:
        return True
    if any(ch.isdigit() for ch in token):
        return True
    if token.isupper() and len(token) >= 2: 
        return True
    if any(c.isupper() for c in token[1:]):
        return True
    return False


def check_grammar(text, max_issues=25):
    """Return grammar/spelling issues found in `text`.

    Shape: {"available": bool, "issue_count": int, "issues": [
        {"type", "message", "text", "suggestions": [...], "context"}
    ]}. Returns available=False (and no issues) if the engine can't start, so
    the rest of the analysis still succeeds.
    """
    try:
        tool = _get_tool()
        matches = tool.check(text)
    except Exception:
        return {"available": False, "issue_count": 0, "issues": []}

    issues = []
    for m in matches:
        itype = getattr(m, "rule_issue_type", "") or ""
        if itype not in _KEEP_ISSUE_TYPES:
            continue
        token = (getattr(m, "matched_text", "") or "").strip()
        if itype == "misspelling":
            if _looks_technical(token):
                continue
            if token[:1].isupper():
                continue
        issues.append(
            {
                "type": itype,
                "message": m.message,
                "text": token,
                "suggestions": list(m.replacements[:3]),
                "context": m.context.strip(),
            }
        )
        if len(issues) >= max_issues:
            break

    return {"available": True, "issue_count": len(issues), "issues": issues}
