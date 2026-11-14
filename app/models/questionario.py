from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CriadoEm


class Questionario(Base):
    __tablename__ = "questionarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(String(300))
    ativo: Mapped[bool] = mapped_column(default=True)
    pontos: Mapped[int] = mapped_column(default=10)
    criado_em: Mapped[CriadoEm]

    perguntas: Mapped[list["Pergunta"]] = relationship(
        cascade="all, delete-orphan", order_by="Pergunta.ordem", lazy="selectin"
    )


class Pergunta(Base):
    __tablename__ = "perguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    questionario_id: Mapped[int] = mapped_column(ForeignKey("questionarios.id"), index=True)
    texto: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(10))  # "unica" | "multipla"
    # Marca perguntas usadas na análise: "categoria" (interesses) ou "frequencia"
    dimensao: Mapped[str | None] = mapped_column(String(20))
    ordem: Mapped[int] = mapped_column(default=0)

    opcoes: Mapped[list["Opcao"]] = relationship(
        cascade="all, delete-orphan", order_by="Opcao.ordem", lazy="selectin"
    )


class Opcao(Base):
    __tablename__ = "opcoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    pergunta_id: Mapped[int] = mapped_column(ForeignKey("perguntas.id"), index=True)
    texto: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(default=0)


class Resposta(Base):
    """Uma submissão de questionário. Ligada só a um visitante anônimo (sem dados pessoais)."""

    __tablename__ = "respostas"
    __table_args__ = (UniqueConstraint("questionario_id", "visitante_id", name="uq_resposta_visitante"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    questionario_id: Mapped[int] = mapped_column(ForeignKey("questionarios.id"), index=True)
    visitante_id: Mapped[int] = mapped_column(ForeignKey("visitantes.id"), index=True)
    criado_em: Mapped[CriadoEm]


class RespostaItem(Base):
    __tablename__ = "resposta_itens"

    id: Mapped[int] = mapped_column(primary_key=True)
    resposta_id: Mapped[int] = mapped_column(ForeignKey("respostas.id"), index=True)
    pergunta_id: Mapped[int] = mapped_column(ForeignKey("perguntas.id"), index=True)
    opcao_id: Mapped[int] = mapped_column(ForeignKey("opcoes.id"), index=True)
