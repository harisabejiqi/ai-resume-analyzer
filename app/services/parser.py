import os

import fitz
from docx import Document


def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_doc(file_path):
    """Extract text from a legacy .doc (binary Word) file.

    python-docx only reads .docx (the modern Office Open XML format). The old
    .doc format is an OLE compound binary, so we drive an installed Microsoft
    Word instance through COM automation to read it. Requires Windows + Word +
    pywin32; callers should be prepared for this to raise if any are missing.
    """
    import pythoncom
    import win32com.client as win32

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(
            os.path.abspath(file_path), False, True, False, "-no-password-"
        )
        text = doc.Content.Text
        for sep in ("\r", "\x07", "\x0b", "\x0c"):
            text = text.replace(sep, "\n")
        text = "".join(ch for ch in text if ch in "\n\t" or ch >= " ")
        return text
    finally:
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


def extract_text(file_path):
    ext = file_path.lower()
    if ext.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif ext.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif ext.endswith(".doc"):
        return extract_text_from_doc(file_path)
    else:
        raise ValueError("Unsupported file format. Use PDF, DOC, or DOCX.")
