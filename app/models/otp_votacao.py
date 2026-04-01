from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

from app.database import Base


class OtpVotacao(Base):
    __tablename__ = "otp_votacao"

    id = Column(Integer, primary_key=True, index=True)
    cooperado_id = Column(Integer, ForeignKey("cooperados.id"), nullable=False)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    codigo = Column(String(6), nullable=False)
    verificado = Column(Boolean, default=False)
    tentativas = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5))

    cooperado = relationship("Cooperado")
    eleicao = relationship("Eleicao")

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    @property
    def max_tentativas_excedidas(self) -> bool:
        return self.tentativas >= 3
