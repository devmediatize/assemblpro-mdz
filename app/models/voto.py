from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Voto(Base):
    __tablename__ = "votos"

    id = Column(Integer, primary_key=True, index=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    cooperado_id = Column(Integer, ForeignKey("cooperados.id"), nullable=False)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=True)
    chapa_id = Column(Integer, ForeignKey("chapas.id"), nullable=True)
    pauta_id = Column(Integer, ForeignKey("pautas.id"), nullable=True)
    opcao = Column(String(50), nullable=True)  # 'sim', 'nao', 'branco', 'abstencao' ou opção múltipla
    hash_voto = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    eleicao = relationship("Eleicao", back_populates="votos")
    cooperado = relationship("Cooperado", back_populates="votos")
    candidato = relationship("Candidato", back_populates="votos")
    chapa = relationship("Chapa", back_populates="votos")
    pauta = relationship("Pauta", back_populates="votos")

    def __repr__(self):
        return f"<Voto {self.hash_voto[:8]}...>"
