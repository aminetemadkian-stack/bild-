import io

import pytest

from app.services.document_reader import MAX_BYTES, MAX_TEXT_CHARS, read_document


def _docx_bytes(text):
    from docx import Document
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _xlsx_bytes():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "متره"
    ws.append(["کف", 1500])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_plain_text_is_read_in_persian():
    result = read_document("note.txt", "سلام معمار".encode("utf-8"))
    assert result.status == "OK"
    assert result.text == "سلام معمار"


def test_docx_and_xlsx_are_extracted():
    assert "ضوابط تراکم" in read_document("plan.docx", _docx_bytes("ضوابط تراکم")).text
    assert "[Sheet: متره]" in read_document("bq.xlsx", _xlsx_bytes()).text


def test_broken_office_file_is_reported_not_raised():
    result = read_document("broken.docx", b"not a zip")
    assert result.status == "PARSE_ERROR"
    assert result.text == ""


def test_unsupported_suffix_is_reported():
    assert read_document("photo.png", b"\x89PNG").status == "UNSUPPORTED"


def test_empty_text_is_reported_as_empty():
    assert read_document("empty.txt", b"   ").status == "EMPTY"


def test_oversize_file_is_rejected_before_parsing():
    assert read_document("big.txt", b"x" * (MAX_BYTES + 1)).status == "TOO_LARGE"


def test_path_traversal_in_filename_is_stripped():
    assert read_document("../../etc/passwd.txt", b"ok").name == "passwd.txt"


def test_long_text_is_truncated_and_flagged():
    result = read_document("long.txt", ("a" * (MAX_TEXT_CHARS + 10)).encode())
    assert result.truncated is True
    assert len(result.text) == MAX_TEXT_CHARS
