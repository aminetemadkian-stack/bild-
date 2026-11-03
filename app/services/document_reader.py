"""Pure document reader: turns an uploaded file's bytes into text, with an explicit report.

No FastAPI, no network, no disk writes. The web layer passes bytes in and gets a
structured result back. Every failure is reported per file; nothing is silently dropped.
"""
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import PurePosixPath

MAX_BYTES = 12 * 1024 * 1024
MAX_TEXT_CHARS = 50_000
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml", ".log", ".py", ".html", ".css", ".js", ".ts", ".sql"}

@dataclass
class ReadResult:
    name: str
    status: str  # OK | UNSUPPORTED | TOO_LARGE | PARSE_ERROR | EMPTY
    text: str = ""
    detail: str = ""
    truncated: bool = False
    extra: dict = field(default_factory=dict)

def _clip(text: str) -> tuple[str, bool]:
    return (text[:MAX_TEXT_CHARS], len(text) > MAX_TEXT_CHARS)

def read_document(name: str, raw: bytes) -> ReadResult:
    safe_name = PurePosixPath(name or "upload").name
    if len(raw) > MAX_BYTES:
        return ReadResult(safe_name, "TOO_LARGE", detail=f"بیش از {MAX_BYTES // (1024 * 1024)} مگابایت")
    suffix = PurePosixPath(safe_name).suffix.lower()
    try:
        if suffix in TEXT_SUFFIXES:
            text = raw.decode("utf-8-sig", errors="replace")
        elif suffix == ".pdf":
            from pypdf import PdfReader
            pages = PdfReader(BytesIO(raw), strict=False).pages[:35]
            text = "\n".join((p.extract_text() or "") for p in pages)
        elif suffix == ".docx":
            from docx import Document
            text = "\n".join(p.text for p in Document(BytesIO(raw)).paragraphs)
        elif suffix == ".pptx":
            from pptx import Presentation
            lines = []
            for slide in Presentation(BytesIO(raw)).slides:
                for shape in slide.shapes:
                    if getattr(shape, "has_text_frame", False):
                        lines.append(shape.text)
            text = "\n".join(lines)
        elif suffix == ".xlsx":
            from openpyxl import load_workbook
            wb = load_workbook(BytesIO(raw), read_only=True, data_only=True)
            lines = []
            for ws in wb.worksheets[:10]:
                lines.append(f"[Sheet: {ws.title}]")
                for row in ws.iter_rows(max_row=1000, values_only=True):
                    lines.append(" | ".join("" if v is None else str(v) for v in row))
            text = "\n".join(lines)
        else:
            return ReadResult(safe_name, "UNSUPPORTED", detail=f"پسوند {suffix or 'بدون پسوند'} هنوز پردازش نمی‌شود")
    except Exception as exc:
        return ReadResult(safe_name, "PARSE_ERROR", detail=f"{type(exc).__name__}: خواندن فایل ممکن نشد")
    text = text.strip()
    if not text:
        return ReadResult(safe_name, "EMPTY", detail="متنی در فایل پیدا نشد (ممکن است تصویری باشد)")
    clipped, truncated = _clip(text)
    return ReadResult(safe_name, "OK", text=clipped, truncated=truncated, extra={"chars": len(text)})
