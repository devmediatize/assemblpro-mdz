from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TipoEleicao(str, enum.Enum):
    CONSELHO = "conselho"
    ASSEMBLEIA = "assembleia"
    CHAPA = "chapa"


class StatusEleicao(str, enum.Enum):
    CONFIGURACAO = "configuracao"
    CONVOCACAO = "convocacao"
    VOTACAO = "votacao"
    ENCERRADA = "encerrada"
    APURADA = "apurada"


class Eleicao(Base):
    __tablename__ = "eleicoes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    tipo = Column(SQLEnum(TipoEleicao), nullable=False)
    data_inicio = Column(DateTime(timezone=True), nullable=False)
    data_fim = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(StatusEleicao), default=StatusEleicao.CONFIGURACAO)
    exige_mfa = Column(Boolean, default=True)
    permite_voto_branco = Column(Boolean, default=True)
    max_votos = Column(Integer, default=1)  # Quantidade máxima de votos por cooperado
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relationships
    candidatos = relationship("Candidato", back_populates="eleicao", cascade="all, delete-orphan")
    chapas = relationship("Chapa", back_populates="eleicao", cascade="all, delete-orphan")
    pautas = relationship("Pauta", back_populates="eleicao", cascade="all, delete-orphan")
    votos = relationship("Voto", back_populates="eleicao", cascade="all, delete-orphan")
    convites = relationship("ConviteVotacao", back_populates="eleicao", cascade="all, delete-orphan")
    criador = relationship("Usuario", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Eleicao {self.titulo}>"
