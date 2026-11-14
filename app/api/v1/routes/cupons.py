import re
import secrets
import unicodedata
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentEstabelecimento, DbSession
from app.models import Campanha, Cupom, Resgate
from app.schemas.gestao import CupomCreate, CupomRead, ResgateValidado, ResgateValidar

router = APIRouter(tags=["Cupons (lojista)"])


def _gerar_codigo(titulo: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode().upper()
    base = re.sub(r"[^A-Z0-9]", "", ascii_)[:6] or "CUPOM"
    return f"{base}{secrets.token_hex(2).upper()}"


@router.post("/cupons", response_model=CupomRead, status_code=status.HTTP_201_CREATED)
async def criar_cupom(dados: CupomCreate, estabelecimento: CurrentEstabelecimento, db: DbSession):
    if dados.campanha_id is not None:
        campanha = await db.get(Campanha, dados.campanha_id)
        if campanha is None or campanha.estabelecimento_id != estabelecimento.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Campanha não encontrada")
    cupom = Cupom(estabelecimento_id=estabelecimento.id, codigo=_gerar_codigo(dados.titulo), **dados.model_dump())
    db.add(cupom)
    await db.commit()
    await db.refresh(cupom)
    return cupom


@router.get("/cupons", response_model=list[CupomRead])
async def listar_cupons(estabelecimento: CurrentEstabelecimento, db: DbSession):
    consulta = select(Cupom).where(Cupom.estabelecimento_id == estabelecimento.id).order_by(Cupom.id.desc())
    return (await db.scalars(consulta)).all()


@router.post("/resgates/validar", response_model=ResgateValidado)
async def validar_resgate(dados: ResgateValidar, estabelecimento: CurrentEstabelecimento, db: DbSession):
    """O lojista confirma, no balcão, o código apresentado pelo visitante."""
    resgate = await db.scalar(
        select(Resgate)
        .join(Cupom, Cupom.id == Resgate.cupom_id)
        .where(Resgate.codigo == dados.codigo.upper(), Cupom.estabelecimento_id == estabelecimento.id)
        .with_for_update(of=Resgate)
    )
    if resgate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Código de resgate não encontrado")
    if resgate.usado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este cupom já foi utilizado")
    resgate.usado = True
    resgate.usado_em = datetime.now(UTC)
    await db.commit()
    return ResgateValidado(success=True, message="Cupom validado com sucesso")
