from decimal import Decimal

from pydantic import BaseModel


class ResumoIndicadores(BaseModel):
    faturamento_total: Decimal
    total_vendas: int
    ticket_medio: Decimal