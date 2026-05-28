from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.research import router as research_router
from app.api.v1.reports import router as reports_router
from app.api.v1.export import router as export_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(research_router)
v1_router.include_router(reports_router)
v1_router.include_router(export_router)
