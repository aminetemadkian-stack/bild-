from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.services.document_reader import read_document, MAX_BYTES

MAX_TOTAL_BYTES = 20 * 1024 * 1024
MAX_FILES = 10
IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp", "image/gif"}

async def extract_uploads(files: list[UploadFile]):
    """Read chat uploads with the document reader tool.

    Returns (parsed_texts, images, not_processed) so the chat endpoint keeps its contract.
    Each non-OK file is named in not_processed; the reason is logged by the reader's status.
    """
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=413, detail="حداکثر ۱۰ فایل در هر پیام مجاز است.")
    parsed, images, not_processed = [], [], []
    total = 0
    for f in files:
        name = Path(f.filename or "upload").name
        raw = await f.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise HTTPException(status_code=413, detail=f"فایل {name} از حد ۱۲ مگابایت بزرگ‌تر است.")
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="حجم کل ضمیمه‌ها نباید از ۲۰ مگابایت بیشتر شود.")
        mime = (f.content_type or "application/octet-stream").lower()
        if mime in IMAGE_MIMES:
            images.append({"name": name, "mime": mime, "data": raw})
            continue
        result = read_document(name, raw)
        if result.status == "OK":
            label = Path(name).suffix.lstrip(".").upper() or "TEXT"
            parsed.append(f"\n[{label}: {result.name}]\n" + result.text)
        else:
            not_processed.append(result.name)
    return parsed, images, not_processed
