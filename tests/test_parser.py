"""Tests for PDF and DOCX text extraction.

The PDFs are built in the test with PyMuPDF, with bullet glyphs and bullet
texts in separate text boxes, like the real uploads that came out scrambled.
"""

import docx
import fitz
import pytest

from app.services import parser
from app.services.analyzer import analyze_resume, extract_work_experience

SIDEBAR = ["Contact", "Phone: +383 45 951 871", "Education", "University of Prishtina",
           "Bachelor in Computer Engineering", "Technical skills", "SQL, Python, Docker"]

MAIN = [
    ("Work experience", None),
    ("Gjirafa Inc | Quality Assurance Automation Engineer Lead", None),
    ("January 2024 - Present", None),
    ("Engineered real-time data pipelines across Apache Pulsar,", "-"),
    ("ClickHouse and Apache Pinot for analytics.", None),
    ("Validated application behavior and data accuracy through", "-"),
    ("API and database testing.", None),
    ("Gjirafa Inc | Junior Quality Assurance Engineer", None),
    ("February 2023 - December 2023", None),
    ("Developed reusable C# and Selenium automation frameworks.", "-"),
]


def _two_column_pdf(path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for i, line in enumerate(SIDEBAR):
        page.insert_text((40, 100 + 20 * i), line, fontsize=9)
    for i, (line, glyph) in enumerate(MAIN):
        y = 100 + 20 * i
        if glyph:
            page.insert_text((280, y), glyph, fontsize=9)
        page.insert_text((300 if glyph or i and MAIN[i - 1][1] else 263, y), line, fontsize=9)
    doc.save(path)
    doc.close()


def test_two_columns_are_read_one_after_the_other(tmp_path):
    path = str(tmp_path / "cv.pdf")
    _two_column_pdf(path)
    lines = parser.extract_text(path).splitlines()
    assert lines[:len(SIDEBAR)] == SIDEBAR
    assert lines[len(SIDEBAR)] == "Work experience"


def test_bullet_glyph_is_put_back_in_front_of_its_text(tmp_path):
    path = str(tmp_path / "cv.pdf")
    _two_column_pdf(path)
    text = parser.extract_text(path)
    assert "- Engineered real-time data pipelines across Apache Pulsar," in text.splitlines()


def test_two_column_cv_roles_and_bullets(tmp_path):
    path = str(tmp_path / "cv.pdf")
    _two_column_pdf(path)
    roles = extract_work_experience(parser.extract_text(path))
    assert [(r["title"], r["company"], r["start"]) for r in roles] == [
        ("Quality Assurance Automation Engineer Lead", "Gjirafa Inc", "January 2024"),
        ("Junior Quality Assurance Engineer", "Gjirafa Inc", "February 2023"),
    ]
    assert roles[0]["bullets"] == [
        "Engineered real-time data pipelines across Apache Pulsar, ClickHouse and Apache "
        "Pinot for analytics.",
        "Validated application behavior and data accuracy through API and database testing.",
    ]
    assert roles[1]["bullets"] == [
        "Developed reusable C# and Selenium automation frameworks.",
    ]


def test_full_width_header_and_footer_keep_columns_apart(tmp_path):
    header = "Jane Doe, Senior Backend Engineer with eight years of experience in payment APIs"
    footer = "References available on request from previous employers and managers, page 1 of 1"
    path = str(tmp_path / "cv.pdf")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 60), header, fontsize=10)
    for i, line in enumerate(SIDEBAR):
        page.insert_text((40, 100 + 20 * i), line, fontsize=9)
    main = [line for line, _ in MAIN]
    for i, line in enumerate(main):
        page.insert_text((263, 100 + 20 * i), line, fontsize=9)
    page.insert_text((40, 740), footer, fontsize=8)
    doc.save(path)
    doc.close()
    assert parser.extract_text(path).splitlines() == [header, *SIDEBAR, *main, footer]


def test_single_column_page_keeps_line_order(tmp_path):
    path = str(tmp_path / "cv.pdf")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    body = [f"Line {i}: a full-width sentence that runs across the middle of the page."
            for i in range(12)]
    for i, line in enumerate(body):
        page.insert_text((40, 100 + 20 * i), line, fontsize=9)
    doc.save(path)
    doc.close()
    assert parser.extract_text(path).splitlines() == body


def test_private_use_bullets_are_normalized():
    assert parser._normalize_bullets("\uf0b7 SQL\n\uf0a7 Python") == "• SQL\n• Python"


@pytest.mark.parametrize("marker", ["●", "■", "➢", "✓", "✔", "►", "o"])
def test_template_bullet_symbols_become_bullets(marker):
    text = parser._normalize_bullets(
        "Experience\nBackend Developer, Acme\nJan 2020 - Present\n"
        f"{marker} Built APIs in Python\n{marker} Wrote integration tests\n"
    )
    roles = extract_work_experience(text)
    assert roles[0]["bullets"] == ["Built APIs in Python", "Wrote integration tests"]


def test_only_line_leading_markers_are_changed():
    assert parser._normalize_bullets("Skills: o and x\nLeo ● Jones\n  ● Indented") == \
        "Skills: o and x\nLeo ● Jones\n  • Indented"


def _docx(tmp_path, build):
    doc = docx.Document()
    build(doc)
    path = str(tmp_path / "cv.docx")
    doc.save(path)
    return path


def test_docx_automatic_bullets_are_kept(tmp_path):
    def build(doc):
        doc.add_paragraph("Experience")
        doc.add_paragraph("Backend Developer | Acme")
        doc.add_paragraph("Jan 2020 - Present")
        doc.add_paragraph("Built APIs in Python", style="List Bullet")
        doc.add_paragraph("Wrote integration tests", style="List Number")

    text = parser.extract_text(_docx(tmp_path, build))
    assert "• Built APIs in Python" in text.splitlines()
    assert extract_work_experience(text)[0]["bullets"] == [
        "Built APIs in Python", "Wrote integration tests",
    ]


def test_docx_page_header_is_read(tmp_path):
    def build(doc):
        doc.sections[0].header.paragraphs[0].text = "Jane Doe | jane@example.com | +1 555 123 4567"
        doc.add_paragraph("Experience")

    analysis = analyze_resume(parser.extract_text(_docx(tmp_path, build)))
    assert analysis["email"] == "jane@example.com"
    assert analysis["phone"] is not None


def test_docx_table_layout_is_read_column_by_column(tmp_path):
    def build(doc):
        doc.add_paragraph("Jane Doe")
        table = doc.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "jane@example.com\nSkills\nPython\nSQL"
        table.cell(0, 1).text = "Experience\nBackend Developer | Acme\nJan 2020 - Present"
        table.cell(0, 1).add_paragraph("Built APIs in Python", style="List Bullet")

    text = parser.extract_text(_docx(tmp_path, build))
    assert text.splitlines() == [
        "Jane Doe", "jane@example.com", "Skills", "Python", "SQL",
        "Experience", "Backend Developer | Acme", "Jan 2020 - Present",
        "• Built APIs in Python",
    ]


def test_docx_merged_cell_is_read_once(tmp_path):
    def build(doc):
        table = doc.add_table(rows=1, cols=3)
        table.cell(0, 0).merge(table.cell(0, 1)).text = "Jane Doe"
        table.cell(0, 2).text = "jane@example.com"

    assert parser.extract_text(_docx(tmp_path, build)).splitlines() == [
        "Jane Doe", "jane@example.com",
    ]


def test_legacy_doc_is_rejected():
    with pytest.raises(ValueError, match="Use PDF or DOCX"):
        parser.extract_text("cv.doc")
