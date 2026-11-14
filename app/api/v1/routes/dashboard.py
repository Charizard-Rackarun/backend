from fastapi import APIRouter

from app.api.deps import CurrentEstabelecimento, DbSession
from app.schemas.painel import DashboardData
from app.services.dashboard import montar_dashboard

router = APIRouter(tags=["Painel"])


@router.get("/dashboard", response_model=DashboardData)
async def dashboard(estabelecimento: CurrentEstabelecimento, db: DbSession):
    # Dados de vendas são sempre filtrados pelo estabelecimento logado (RNF05)
    return await montar_dashboard(db, estabelecimento.id)
