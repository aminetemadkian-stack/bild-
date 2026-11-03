from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.api.extra_routes import extra_router
from app.core.config import settings
from app.services.storage import init_db, cleanup_chat_history
import asyncio
from contextlib import suppress

app = FastAPI(title=settings.app_name, version="0.1.0", description="Conceptual multi-agent architectural design assistant. Not for construction use.")
app.include_router(router, prefix="/api/v1")
app.include_router(extra_router, prefix="/api/v1")

_cleanup_task = None

async def _cleanup_loop():
    while True:
        await asyncio.to_thread(cleanup_chat_history)
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup() -> None:
    global _cleanup_task
    init_db()
    cleanup_chat_history()
    _cleanup_task = asyncio.create_task(_cleanup_loop())

@app.on_event("shutdown")
async def shutdown() -> None:
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await _cleanup_task
        _cleanup_task = None

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name, "mode": settings.llm_provider}

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("app/static/index.html")
