from io import BytesIO
from pathlib import Path
from fastapi import UploadFile, HTTPException

MAX_FILE_BYTES=12*1024*1024
MAX_TOTAL_BYTES=20*1024*1024
MAX_FILES=10
TEXT_SUFFIXES={".txt",".md",".csv",".json",".xml",".yaml",".yml",".log",".py",".html",".css",".js",".ts",".sql"}
IMAGE_MIMES={"image/png","image/jpeg","image/webp","image/gif"}

async def extract_uploads(files: list[UploadFile]):
    if len(files)>MAX_FILES:
        raise HTTPException(status_code=413,detail="حداکثر ۱۰ فایل در هر پیام مجاز است.")
    parsed=[]; images=[]; not_processed=[]; total=0
    for f in files:
        name=Path(f.filename or "upload").name
        raw=await f.read(MAX_FILE_BYTES+1)
        if len(raw)>MAX_FILE_BYTES:
            raise HTTPException(status_code=413,detail=f"فایل {name} از حد ۱۲ مگابایت بزرگ‌تر است.")
        total+=len(raw)
        if total>MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413,detail="حجم کل ضمیمه‌ها نباید از ۲۰ مگابایت بیشتر شود.")
        suffix=Path(name).suffix.lower(); mime=(f.content_type or "application/octet-stream").lower()
        try:
            if suffix in TEXT_SUFFIXES:
                parsed.append(f"\n[فایل {name}]\n"+raw.decode("utf-8-sig",errors="replace")[:50000])
            elif suffix==".pdf":
                from pypdf import PdfReader
                pdf=PdfReader(BytesIO(raw),strict=False)
                parsed.append(f"\n[PDF: {name}]\n"+"\n".join((pg.extract_text() or "") for pg in pdf.pages[:35])[:50000])
            elif suffix==".docx":
                from docx import Document
                doc=Document(BytesIO(raw))
                parsed.append(f"\n[DOCX: {name}]\n"+"\n".join(p.text for p in doc.paragraphs)[:50000])
            elif suffix==".pptx":
                from pptx import Presentation
                prs=Presentation(BytesIO(raw)); lines=[]
                for slide in prs.slides[:30]:
                    for shape in slide.shapes:
                        if getattr(shape,"has_text_frame",False): lines.append(shape.text)
                parsed.append(f"\n[PPTX: {name}]\n"+"\n".join(lines)[:50000])
            elif suffix==".xlsx":
                from openpyxl import load_workbook
                wb=load_workbook(BytesIO(raw),read_only=True,data_only=True); lines=[]
                for ws in wb.worksheets[:10]:
                    lines.append(f"[Sheet: {ws.title}]")
                    for row in ws.iter_rows(max_row=1000,values_only=True):
                        lines.append(" | ".join("" if v is None else str(v) for v in row))
                parsed.append(f"\n[XLSX: {name}]\n"+"\n".join(lines)[:50000])
            elif mime in IMAGE_MIMES:
                images.append({"name":name,"mime":mime,"data":raw})
            else:
                not_processed.append(name)
        except Exception:
            not_processed.append(name)
    return parsed,images,not_processed
