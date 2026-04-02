from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Eleicao, StatusEleicao

router = APIRouter(tags=["Views"])
templates = Jinja2Templates(directory="app/templates")


# ============ AUTH ============
@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"title": "Login"}
    )


@router.get("/verificar-otp", response_class=HTMLResponse)
async def otp_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/verificar_otp.html",
        context={"title": "Verificar Código"}
    )


# ============ ADMIN ============
@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login_admin.html",
        context={"title": "Login Admin"}
    )


@router.get("/admin", response_class=HTMLResponse)
@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"title": "Dashboard"}
    )


@router.get("/admin/eleicoes", response_class=HTMLResponse)
async def admin_eleicoes(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/eleicoes/lista.html",
        context={"title": "Eleições"}
    )


@router.get("/admin/eleicoes/criar", response_class=HTMLResponse)
async def admin_criar_eleicao(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/eleicoes/criar.html",
        context={"title": "Nova Eleição"}
    )


@router.get("/admin/eleicoes/{eleicao_id}", response_class=HTMLResponse)
async def admin_eleicao_detalhe(request: Request, eleicao_id: int):
    return templates.TemplateResponse(
        request=request,
        name="admin/eleicoes/detalhe.html",
        context={"title": "Detalhes da Eleição", "eleicao_id": eleicao_id}
    )


@router.get("/admin/eleicoes/{eleicao_id}/configurar", response_class=HTMLResponse)
async def admin_configurar_eleicao(request: Request, eleicao_id: int):
    return templates.TemplateResponse(
        request=request,
        name="admin/eleicoes/configurar.html",
        context={"title": "Configurar Eleição", "eleicao_id": eleicao_id}
    )


@router.get("/admin/eleicoes/{eleicao_id}/editar", response_class=HTMLResponse)
async def admin_editar_eleicao(request: Request, eleicao_id: int):
    return templates.TemplateResponse(
        request=request,
        name="admin/eleicoes/editar.html",
        context={"title": "Editar Eleição", "eleicao_id": eleicao_id}
    )


@router.get("/admin/cooperados", response_class=HTMLResponse)
async def admin_cooperados(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/cooperados/lista.html",
        context={"title": "Cooperados"}
    )


@router.get("/admin/relatorios", response_class=HTMLResponse)
async def admin_relatorios(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/relatorios/index.html",
        context={"title": "Relatórios"}
    )


@router.get("/admin/configuracoes", response_class=HTMLResponse)
async def admin_configuracoes(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/configuracoes/index.html",
        context={"title": "Configurações"}
    )


@router.get("/admin/usuarios", response_class=HTMLResponse)
async def admin_usuarios(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/usuarios/lista.html",
        context={"title": "Usuários"}
    )


@router.get("/admin/eleicoes/{eleicao_id}/votos", response_class=HTMLResponse)
async def admin_votos_eleicao(request: Request, eleicao_id: int):
    return templates.TemplateResponse(
        request=request,
        name="admin/votos/lista.html",
        context={"title": "Votos da Eleição", "eleicao_id": eleicao_id}
    )


# ============ VOTAÇÃO ============
@router.get("/votar", response_class=HTMLResponse)
async def votacao_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="votacao/selecionar_eleicao.html",
        context={"title": "Minhas Eleições"}
    )


@router.get("/votar/{eleicao_id}", response_class=HTMLResponse)
async def votacao_votar(request: Request, eleicao_id: int):
    return templates.TemplateResponse(
        request=request,
        name="votacao/votar.html",
        context={"title": "Votar", "eleicao_id": eleicao_id}
    )


@router.get("/votar/confirmacao/{hash_voto}", response_class=HTMLResponse)
async def votacao_confirmacao(request: Request, hash_voto: str):
    return templates.TemplateResponse(
        request=request,
        name="votacao/confirmacao.html",
        context={"title": "Voto Confirmado", "hash_voto": hash_voto}
    )
