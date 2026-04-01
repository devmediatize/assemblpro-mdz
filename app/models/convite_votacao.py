from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ConviteVotacao(Base):
    __tablename__ = "convites_votacao"

    id = Column(Integer, primary_key=True, index=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    cooperado_id = Column(Integer, ForeignKey("cooperados.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    enviado_em = Column(DateTime(timezone=True), server_default=func.now())
    visualizado_em = Column(DateTime(timezone=True), nullable=True)
    votou = Column(Boolean, default=False)
    metodo_envio = Column(String(20), default="email")  # email, sms, ambos

    # Relationships
    eleicao = relationship("Eleicao", back_populates="convites")
    cooperado = relationship("Cooperado", back_populates="convites")

    def __repr__(self):
        return f"<ConviteVotacao {self.token[:8]}...>"
