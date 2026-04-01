from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.cooperados import router as cooperados_router
from app.routers.eleicoes import router as eleicoes_router
from app.routers.candidatos import router as candidatos_router
from app.routers.chapas import router as chapas_router
from app.routers.pautas import router as pautas_router
from app.routers.votos import router as votos_router
from app.routers.dashboard import router as dashboard_router
from app.routers.configuracoes import router as configuracoes_router
from app.routers.auditoria import router as auditoria_router
from app.routers.views import router as views_router

__all__ = [
    "auth_router",
    "usuarios_router",
    "cooperados_router",
    "eleicoes_router",
    "candidatos_router",
    "chapas_router",
    "pautas_router",
    "votos_router",
    "dashboard_router",
    "configuracoes_router",
    "auditoria_router",
    "views_router"
]
