from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CriadoEm


class Visitante(Base):
    """Visitante anônimo: guarda apenas o hash de um token e o saldo de pontos."""

    __tablename__ = "visitantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    pontos: Mapped[int] = mapped_column(default=0)
    criado_em: Mapped[CriadoEm]


class Cupom(Base):
    __tablename__ = "cupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    campanha_id: Mapped[int | None] = mapped_column(ForeignKey("campanhas.id"))
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(String(200))
    desconto: Mapped[str] = mapped_column(String(40))
    categoria: Mapped[str] = mapped_column(String(40))
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    custo_pontos: Mapped[int]
    estoque: Mapped[int | None]  # None = ilimitado
    validade: Mapped[date] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(default=True)
    # Cupons secretos: só aparecem e podem ser resgatados nas Sextas 13
    exclusivo_sexta_13: Mapped[bool] = mapped_column(default=False)
    criado_em: Mapped[CriadoEm]


class Resgate(Base):
    __tablename__ = "resgates"

    id: Mapped[int] = mapped_column(primary_key=True)
    cupom_id: Mapped[int] = mapped_column(ForeignKey("cupons.id"), index=True)
    visitante_id: Mapped[int] = mapped_column(ForeignKey("visitantes.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    usado: Mapped[bool] = mapped_column(default=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[CriadoEm]
