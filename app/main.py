from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.routers import (
    auth_router,
    usuarios_router,
    cooperados_router,
    eleicoes_router,
    candidatos_router,
    chapas_router,
    pautas_router,
    votos_router,
    dashboard_router,
    configuracoes_router,
    auditoria_router,
    views_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Sistema de Votação Eletrônica Segura para Cooperativas",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routers
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(cooperados_router)
app.include_router(eleicoes_router)
app.include_router(candidatos_router)
app.include_router(chapas_router)
app.include_router(pautas_router)
app.include_router(votos_router)
app.include_router(dashboard_router)
app.include_router(configuracoes_router)
app.include_router(auditoria_router)

# View Router (HTML pages)
app.include_router(views_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    favicon_path = base_dir / "static" / "img" / "logo.png"
    if favicon_path.exists():
        return FileResponse(str(favicon_path), media_type="image/png")
    return FileResponse("static/img/logo.png", media_type="image/png")
