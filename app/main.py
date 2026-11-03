import asyncio
from contextlib import suppress
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.extra_routes import extra_router
from app.core.config import settings
from app.services.storage import init_db, cleanup_chat_history

app = FastAPI(title=settings.app_name, version="0.1.0", description="Conceptual multi-agent architectural design assistant. Not for construction use.")
app.include_router(router, prefix="/api/v1")
app.include_router(extra_router, prefix="/api/v1")

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
LOCAL_ORIGIN_PREFIXES = ("http://127.0.0.1:", "http://localhost:", "http://[::1]:")

def _host_name(raw_host: str) -> str:
    if raw_host.startswith("["):
        return raw_host[1:raw_host.find("]")] if "]" in raw_host else raw_host
    return raw_host.split(":")[0]

@app.middleware("http")
async def local_only_guard(request: Request, call_next):
    # DNS-rebinding guard: only requests addressed to this machine are served.
    if _host_name(request.headers.get("host", "")) not in LOCAL_HOSTS:
        return JSONResponse({"detail": "Forbidden host."}, status_code=403)
    # Cross-site guard: a page from another site cannot drive the local API,
    # even though a plain multipart form POST would otherwise reach /chat.
    origin = request.headers.get("origin")
    if origin is not None and not origin.startswith(LOCAL_ORIGIN_PREFIXES):
        return JSONResponse({"detail": "Cross-origin request blocked."}, status_code=403)
    return await call_next(request)

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
