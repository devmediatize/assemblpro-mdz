from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    cooperado_id = Column(Integer, ForeignKey("cooperados.id"), nullable=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    dados_json = Column(JSON, nullable=True)
    hash_integridade = Column(String(64), nullable=False)  # SHA-256 do registro anterior + dados
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<LogAuditoria {self.tipo} - {self.created_at}>"
