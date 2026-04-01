from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Cooperado(Base):
    __tablename__ = "cooperados"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    telefone = Column(String(20), nullable=True)
    senha_hash = Column(String(255), nullable=False)
    regiao = Column(String(50), nullable=True)
    matricula = Column(String(50), nullable=True)
    ativo = Column(Boolean, default=True)
    tema = Column(String(10), default="dark")  # dark ou light
    otp_secret = Column(String(32), nullable=True)
    otp_ativo = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    votos = relationship("Voto", back_populates="cooperado")
    convites = relationship("ConviteVotacao", back_populates="cooperado")

    def __repr__(self):
        return f"<Cooperado {self.nome}>"
