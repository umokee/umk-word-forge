from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.database import Base, engine
from backend.core.exceptions import AppException

from backend.modules.words.routes import router as words_router
from backend.modules.learning.routes import router as learning_router
from backend.modules.training.routes import router as training_router
from backend.modules.stats.routes import router as stats_router
from backend.modules.ai.routes import router as ai_router
from backend.modules.settings.routes import router as settings_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WordForge",
    description="Self-hosted English vocabulary learning application",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
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
