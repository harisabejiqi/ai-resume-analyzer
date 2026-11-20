import re

import fitz
from docx import Document


_PRIVATE_USE_BULLETS = str.maketrans({
    "\uf0b7": "•", "\uf0a7": "•", "\uf0a8": "•", "\uf076": "•",
    "\uf0d8": "•", "\uf0fc": "•", "\uf06c": "•", "\uf06e": "•",
})

_MIN_COLUMN_LINES = 5
_MAX_CROSSING_SHARE = 0.05
_SAME_ROW_TOLERANCE = 3.0


_LINE_BULLET = re.compile(r"^(\s*)(?:[●○■□▪▫◆◇♦❖➢➤►▶✓✔→]|o(?=\s+[A-Z]))(?=\s)", re.MULTILINE)


def _normalize_bullets(text):
    """Turn every bullet marker at the start of a line into the same one,
    including Symbol/Wingdings glyphs and Word's 'o' sub-bullet."""
    return _LINE_BULLET.sub(r"\1•", text.translate(_PRIVATE_USE_BULLETS))


def _page_lines(page):
    """Every non-empty text line on the page as (x0, y0, x1, y1, text)."""
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                lines.append((*line["bbox"], text))
    return lines


def _center(line):
    return (line[1] + line[3]) / 2


def _find_gutter(lines, width):
    """x position of the gap between two text columns, or None.

    Full-width lines above or below the columns may cross the gap; lines
    beside the columns may not."""
    best = None
    for x in range(int(width * 0.2), int(width * 0.8), 2):
        left = [l for l in lines if l[2] <= x]
        right = [l for l in lines if l[0] >= x]
        if len(left) < _MIN_COLUMN_LINES or len(right) < _MIN_COLUMN_LINES:
            continue
        top = max(min(l[1] for l in left), min(l[1] for l in right))
        bottom = min(max(l[3] for l in left), max(l[3] for l in right))
        beside = sum(1 for l in lines if l[0] < x < l[2] and top < _center(l) < bottom)
        if beside <= _MAX_CROSSING_SHARE * len(lines) and (best is None or beside < best[0]):
            best = (beside, x)
    return best[1] if best else None


def _rows(lines):
    """Join pieces on the same visual row, left to right, so a bullet glyph
    stored in its own text box goes back in front of its line."""
    rows = []
    for line in sorted(lines, key=lambda l: (_center(l), l[0])):
        if rows and abs(rows[-1][0] - _center(line)) <= _SAME_ROW_TOLERANCE:
            rows[-1][1].append(line)
        else:
            rows.append((_center(line), [line]))
    return [" ".join(p[4] for p in sorted(parts, key=lambda p: p[0])) for _, parts in rows]


def _page_text(page):
    """Page text in reading order. On a two-column page, full-width lines split
    the page into bands, and each band is read left column first."""
    lines = _page_lines(page)
    gutter = _find_gutter(lines, page.rect.width)
    if gutter is None:
        return "\n".join(_rows(lines))
    spanning = sorted((l for l in lines if l[0] < gutter < l[2]), key=_center)
    columns = [l for l in lines if not l[0] < gutter < l[2]]
    out = []
    upper = float("-inf")
    for cut in spanning + [None]:
        lower = _center(cut) if cut else float("inf")
        band = [l for l in columns if upper <= _center(l) < lower]
        out += _rows([l for l in band if l[0] < gutter])
        out += _rows([l for l in band if l[0] >= gutter])
        if cut:
            out += _rows([cut])
            upper = lower
    return "\n".join(out)


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    try:
        return "\n".join(_page_text(page) for page in doc) + "\n"
    finally:
        doc.close()


def _is_list_item(paragraph):
    """True if Word numbers or bullets this paragraph, directly or via its style.

    Word draws automatic bullets itself; the bullet character is not part of
    the paragraph's text, so it has to be detected from the formatting.
    """
    ppr = paragraph._p.pPr
    if ppr is not None and ppr.numPr is not None:
        return True
    style = paragraph.style
    while style is not None:
        ppr = style.element.pPr
        if ppr is not None and ppr.numPr is not None:
            return True
        style = style.base_style
    return False


def _container_lines(container, seen_cells):
    """Lines of a document, header or table cell, with tables read in place.
    A merged cell is read only once."""
    lines = []
    for item in container.iter_inner_content():
        if hasattr(item, "rows"):
            for row in item.rows:
                for cell in row.cells:
                    if id(cell._tc) not in seen_cells:
                        seen_cells.add(id(cell._tc))
                        lines += _container_lines(cell, seen_cells)
        elif item.text.strip() and _is_list_item(item):
            lines.append("• " + item.text.strip())
        else:
            lines.append(item.text)
    return lines


def extract_text_from_docx(file_path):
    """Text of a .docx: page headers first, then the body, then page footers.

    Contact details often sit in the page header, and many CV templates lay
    the whole page out as a table; both are invisible to `doc.paragraphs`.
    """
    doc = Document(file_path)
    seen_cells = set()
    header, footer = [], []
    for section in doc.sections:
        for part, out in ((section.header, header), (section.footer, footer)):
            if not part.is_linked_to_previous:
                out += [l for l in _container_lines(part, seen_cells) if l not in out]
    body = _container_lines(doc, seen_cells)
    return "\n".join(header + body + footer)


def extract_text(file_path):
    ext = file_path.lower()
    if ext.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif ext.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")
    return _normalize_bullets(text)
