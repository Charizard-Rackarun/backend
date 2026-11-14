from datetime import date

from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.api.deps import CurrentEstabelecimento, DbSession
from app.models import Campanha, Cupom, Resgate
from app.schemas.gestao import CampanhaCreate
from app.schemas.painel import Campaign
from app.services import tempo
from app.services.formatacao import data_br

router = APIRouter(prefix="/campaigns", tags=["Campanhas"])


def _status(c: Campanha, hoje: date) -> str:
    if hoje < c.data_inicio:
        return "Agendada"
    return "Encerrada" if hoje > c.data_fim else "Ativa"


def _para_schema(c: Campanha, resgates: int, hoje: date) -> Campaign:
    return Campaign(
        id=c.id, name=c.nome, store="Sua loja", type=c.tipo, status=_status(c, hoje), reach=c.alcance,
        redemptions=resgates, start_date=data_br(c.data_inicio), end_date=data_br(c.data_fim), discount=c.desconto,
    )


@router.get("", response_model=list[Campaign])
async def listar(estabelecimento: CurrentEstabelecimento, db: DbSession):
    hoje = tempo.hoje()
    campanhas = (await db.scalars(
        select(Campanha).where(Campanha.estabelecimento_id == estabelecimento.id).order_by(Campanha.id.desc())
    )).all()
    resgates = dict((await db.execute(
        select(Cupom.campanha_id, func.count(Resgate.id))
        .select_from(Cupom)
        .join(Resgate, Resgate.cupom_id == Cupom.id)
        .where(Cupom.estabelecimento_id == estabelecimento.id, Cupom.campanha_id.is_not(None))
        .group_by(Cupom.campanha_id)
    )).all())
    itens = [_para_schema(c, resgates.get(c.id, 0), hoje) for c in campanhas]

    return itens


@router.post("", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def criar(dados: CampanhaCreate, estabelecimento: CurrentEstabelecimento, db: DbSession):
    campanha = Campanha(estabelecimento_id=estabelecimento.id, **dados.model_dump())
    db.add(campanha)
    await db.commit()
    await db.refresh(campanha)
    return _para_schema(campanha, 0, tempo.hoje())
