# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.project import router as project_router
from app.api.v1.chat import router as chat_router
from app.api.v1.requirement import router as requirement_router
from app.api.v1.architecture import router as architecture_router
from app.api.v1.diagram import router as diagram_router
from app.api.v1.codegen import router as codegen_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(project_router)
api_router.include_router(chat_router)
api_router.include_router(requirement_router)
api_router.include_router(architecture_router)
api_router.include_router(diagram_router)
api_router.include_router(codegen_router)