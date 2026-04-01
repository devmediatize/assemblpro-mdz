from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Chapa(Base):
    __tablename__ = "chapas"

    id = Column(Integer, primary_key=True, index=True)
    eleicao_id = Column(Integer, ForeignKey("eleicoes.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    numero = Column(Integer, nullable=False)
    descricao = Column(Text, nullable=True)
    foto_url = Column(String(255), nullable=True)

    # Relationships
    eleicao = relationship("Eleicao", back_populates="chapas")
    candidatos = relationship("Candidato", back_populates="chapa")
    votos = relationship("Voto", back_populates="chapa")

    def __repr__(self):
        return f"<Chapa {self.numero} - {self.nome}>"
