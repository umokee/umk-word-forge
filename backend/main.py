import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.database import Base, engine
from backend.core.exceptions import AppException
from backend.core.security import APIKeyMiddleware

from backend.modules.words.routes import router as words_router
from backend.modules.learning.routes import router as learning_router
from backend.modules.training.routes import router as training_router
from backend.modules.stats.routes import router as stats_router
from backend.modules.ai.routes import router as ai_router
from backend.modules.settings.routes import router as settings_router

# Logging — writes to file when LOG_DIR is set (for fail2ban), else stderr
_log_dir = os.environ.get("WORDFORGE_LOG_DIR", "")
_log_file = os.environ.get("WORDFORGE_LOG_FILE", "app.log")
_log_fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
_handlers[0].setFormatter(_log_fmt)

if _log_dir:
    os.makedirs(_log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(_log_dir, _log_file))
    fh.setFormatter(_log_fmt)
    _handlers.append(fh)
logging.basicConfig(level=logging.INFO, handlers=_handlers, force=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WordForge",
    description="Self-hosted English vocabulary learning application",
    version="2.0.0",
)

app.add_middleware(APIKeyMiddleware)
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger = logging.getLogger("wordforge")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(words_router)
app.include_router(learning_router)
app.include_router(training_router)
app.include_router(stats_router)
app.include_router(ai_router)
app.include_router(settings_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/auth/check")
def auth_check():
    """Protected endpoint — returns 200 only with a valid API key.
    Used by the frontend AuthGate to decide whether to show the login screen."""
    return {"authenticated": True}
