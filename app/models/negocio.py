from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CriadoEm


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    produto: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str | None] = mapped_column(String(40))
    quantidade: Mapped[int]
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    criado_em: Mapped[CriadoEm]


class Campanha(Base):
    __tablename__ = "campanhas"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(40))
    desconto: Mapped[str] = mapped_column(String(40))
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)
    alcance: Mapped[int] = mapped_column(default=0)
    criado_em: Mapped[CriadoEm]


class Oportunidade(Base):
    """Insight gerado pela análise (regras de associação + IA generativa)."""

    __tablename__ = "oportunidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    estabelecimento_id: Mapped[int] = mapped_column(ForeignKey("estabelecimentos.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(String(1000))
    lojas_sugeridas: Mapped[list[str]] = mapped_column(JSON)
    potencial: Mapped[str] = mapped_column(String(40))
    confianca: Mapped[int]
    categoria: Mapped[str] = mapped_column(String(40))
    prioridade: Mapped[str] = mapped_column(String(10))
    criado_em: Mapped[CriadoEm]
