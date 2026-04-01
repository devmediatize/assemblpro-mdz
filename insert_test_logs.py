import asyncio
from datetime import datetime, timezone, timedelta
import random
from app.database import async_session
from app.services.auditoria_service import AuditoriaService, TipoLog

async def inserir_logs_teste():
    async with async_session() as db:
        # Lista de logs de teste
        logs = [
            (TipoLog.LOGIN_SUCESSO, "Login realizado: Admin (admin)", 1, None, None, "192.168.0.1"),
            (TipoLog.ELEICAO_CRIADA, "Eleicao criada: Eleicao do Conselho 2024", None, None, 1, None),
            (TipoLog.LOGIN_SUCESSO, "Login realizado: Maria Silva (cooperado)", None, 1, None, "192.168.0.10"),
            (TipoLog.VOTO_REGISTRADO, "Voto registrado na eleicao: Eleicao do Conselho 2024", None, 1, 1, "192.168.0.10"),
            (TipoLog.LOGIN_SUCESSO, "Login realizado: Joao Santos (cooperado)", None, 2, None, "192.168.0.11"),
            (TipoLog.VOTO_REGISTRADO, "Voto registrado na eleicao: Eleicao do Conselho 2024", None, 2, 1, "192.168.0.11"),
            (TipoLog.LOGIN_FALHA, "Tentativa de login com credenciais invalidas: 123.456.789-00", None, None, None, "192.168.0.50"),
            (TipoLog.COOPERADO_CRIADO, "Cooperado criado: Pedro Oliveira", 1, None, None, "192.168.0.1"),
            (TipoLog.ELEICAO_INICIADA, "Votacao iniciada: Eleicao do Conselho 2024", 1, None, 1, "192.168.0.1"),
            (TipoLog.LOGIN_SUCESSO, "Login realizado: Carlos Lima (cooperado)", None, 3, None, "192.168.0.12"),
            (TipoLog.VOTO_REGISTRADO, "Voto registrado na eleicao: Eleicao do Conselho 2024", None, 3, 1, "192.168.0.12"),
            (TipoLog.LOGIN_SUCESSO, "Login realizado: Ana Costa (cooperado)", None, 4, None, "192.168.0.13"),
            (TipoLog.VOTO_BRANCO, "Voto branco registrado na eleicao: Eleicao do Conselho 2024", None, 4, 1, "192.168.0.13"),
            (TipoLog.CONFIGURACAO_ALTERADA, "Configuracao alterada: nome_sistema", 1, None, None, "192.168.0.1"),
            (TipoLog.LOGOUT, "Logout realizado: Admin", 1, None, None, "192.168.0.1"),
        ]
        
        for tipo, descricao, usuario_id, cooperado_id, eleicao_id, ip in logs:
            await AuditoriaService.registrar(
                db=db,
                tipo=tipo,
                descricao=descricao,
                usuario_id=usuario_id,
                cooperado_id=cooperado_id,
                eleicao_id=eleicao_id,
                ip_address=ip,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
            print(f"Log inserido: {tipo}")
        
        print("\nLogs de teste inseridos com sucesso!")

if __name__ == "__main__":
    asyncio.run(inserir_logs_teste())
