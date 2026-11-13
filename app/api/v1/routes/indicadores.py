from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentEstabelecimento, DbSession
from app.models import Venda
from app.schemas.indicadores import ResumoIndicadores

router = APIRouter(prefix="/indicadores", tags=["Indicadores"])


@router.get("/resumo", response_model=ResumoIndicadores)
async def resumo(estabelecimento: CurrentEstabelecimento, db: DbSession):
    # O filtro por estabelecimento_id garante o isolamento dos dados entre lojas (RNF05)
    consulta = select(func.coalesce(func.sum(Venda.valor_total), 0), func.count(Venda.id)).where(
        Venda.estabelecimento_id == estabelecimento.id
    )
    faturamento, total = (await db.execute(consulta)).one()
    ticket = round(faturamento / total, 2) if total else Decimal("0.00")
    return ResumoIndicadores(faturamento_total=faturamento, total_vendas=total, ticket_medio=ticket)