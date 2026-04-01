from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Candidato(Base):
    __tablename__ = "candidatos"

    id = Column(Integer, primary_key=True, index=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    chapa_id = Column(Integer, ForeignKey("chapas.id"), nullable=True)
    nome = Column(String(100), nullable=False)
    cargo = Column(String(100), nullable=True)
    descricao = Column(Text, nullable=True)
    foto_url = Column(String(255), nullable=True)
    ordem = Column(Integer, default=0)

    # Relationships
    eleicao = relationship("Eleicao", back_populates="candidatos")
    chapa = relationship("Chapa", back_populates="candidatos")
    votos = relationship("Voto", back_populates="candidato")

    def __repr__(self):
        return f"<Candidato {self.nome}>"
