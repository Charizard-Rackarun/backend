from fastapi import APIRouter, status

from app.api.deps import CurrentEstabelecimento, DbSession
from app.models import Venda
from app.schemas.venda import VendaCreate, VendaRead

router = APIRouter(prefix="/vendas", tags=["Vendas"])


@router.post("", response_model=VendaRead, status_code=status.HTTP_201_CREATED)
async def registrar_venda(dados: VendaCreate, estabelecimento: CurrentEstabelecimento, db: DbSession):
    venda = Venda(estabelecimento_id=estabelecimento.id, **dados.model_dump())
    db.add(venda)
    await db.commit()
    await db.refresh(venda)
    return venda