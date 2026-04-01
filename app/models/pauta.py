from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TipoVotoPauta(str, enum.Enum):
    SIM_NAO = "sim_nao"
    MULTIPLA_ESCOLHA = "multipla_escolha"


class Pauta(Base):
    __tablename__ = "pautas"

    id = Column(Integer, primary_key=True, index=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    ordem = Column(Integer, default=0)
    tipo_voto = Column(SQLEnum(TipoVotoPauta), default=TipoVotoPauta.SIM_NAO)
    opcoes = Column(Text, nullable=True)  # JSON string para múltipla escolha

    # Relationships
    eleicao = relationship("Eleicao", back_populates="pautas")
    votos = relationship("Voto", back_populates="pauta")

    def __repr__(self):
        return f"<Pauta {self.titulo}>"
