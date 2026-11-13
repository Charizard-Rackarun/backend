from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    segmento: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Pesquisa(Base):
    """Resposta anônima: não guarda nome, e-mail, IP nem identificador do visitante (LGPD)."""

    __tablename__ = "pesquisas"

    id: Mapped[int] = mapped_column(primary_key=True)
    categorias: Mapped[list[str]] = mapped_column(ARRAY(String(40)))
    frequencia_visita: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    produto: Mapped[str] = mapped_column(String(120))
    quantidade: Mapped[int]
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))