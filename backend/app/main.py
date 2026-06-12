# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AIProviderException, AIResponseValidationException
from app.api.v1.router import api_router   # ← top-level import, not inline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Future: warmup AI clients, verify DB connectivity
    yield

# print(f"{settings.app_name} started in {settings.app_env} mode.")
app = FastAPI(
    title=settings.app_name,
    description="AI-powered platform that transforms software ideas into requirements, architecture, diagrams, and code.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.get('/')(lambda: {"message": f"Welcome to {settings.app_name}!"})

# ── Middleware ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ─────────────────────────────────────
@app.exception_handler(AIProviderException)
async def ai_provider_exception_handler(request: Request, exc: AIProviderException):
    return JSONResponse(
        status_code=502,
        content={"detail": f"AI service error: {exc.detail}", "provider": exc.provider},
    )

@app.exception_handler(AIResponseValidationException)
async def ai_validation_exception_handler(request: Request, exc: AIResponseValidationException):
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc)},
    )

# ── Routers ───────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── Health ────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}