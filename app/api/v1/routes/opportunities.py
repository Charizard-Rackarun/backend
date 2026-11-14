import asyncio

from fastapi import APIRouter
from sqlalchemy import delete, select

from app.api.deps import CurrentEstabelecimento, DbSession
from app.core.config import settings
from app.models import Estabelecimento, Oportunidade
from app.schemas.painel import Opportunity
from app.services.analytics import (
    Regra,
    calcular_regras,
    carregar_cestas,
    classificar,
    descricao_padrao,
)
from app.services.ia import refinar_descricao

router = APIRouter(prefix="/opportunities", tags=["Oportunidades"])


def _para_schema(o: Oportunidade) -> Opportunity:
    return Opportunity(
        id=o.id, title=o.titulo, description=o.descricao, stores=o.lojas_sugeridas, potential=o.potencial,
        confidence=o.confianca, category=o.categoria, priority=o.prioridade,
    )


def _lojas_parceiras(parceiras: list[Estabelecimento], regra: Regra) -> list[str]:
    termos = {regra.antecedente.casefold(), regra.consequente.casefold()}
    return [
        p.nome for p in parceiras
        if any(t in p.segmento.casefold() or p.segmento.casefold() in t for t in termos)
    ][:3]


@router.get("", response_model=list[Opportunity])
async def listar(estabelecimento: CurrentEstabelecimento, db: DbSession):
    consulta = (
        select(Oportunidade)
        .where(Oportunidade.estabelecimento_id == estabelecimento.id)
        .order_by(Oportunidade.confianca.desc())
    )
    return [_para_schema(o) for o in (await db.scalars(consulta)).all()]


@router.post("/gerar", response_model=list[Opportunity])
async def gerar(estabelecimento: CurrentEstabelecimento, db: DbSession):
    """Analisa as respostas (regras de associação) e pede à IA a recomendação em texto."""
    cestas = await carregar_cestas(db)
    regras = calcular_regras(cestas, settings.min_group_size)[:5]
    parceiras = list((await db.scalars(
        select(Estabelecimento).where(Estabelecimento.id != estabelecimento.id)
    )).all())
    textos = await asyncio.gather(*(refinar_descricao(r, estabelecimento.segmento) for r in regras))

    await db.execute(delete(Oportunidade).where(Oportunidade.estabelecimento_id == estabelecimento.id))
    novas = []
    for regra, texto in zip(regras, textos):
        prioridade, potencial = classificar(regra)
        novas.append(Oportunidade(
            estabelecimento_id=estabelecimento.id,
            titulo=f"{regra.antecedente} + {regra.consequente}",
            descricao=texto or descricao_padrao(regra),
            lojas_sugeridas=_lojas_parceiras(parceiras, regra),
            potencial=potencial, confianca=round(regra.confianca * 100),
            categoria="Venda cruzada", prioridade=prioridade,
        ))
    db.add_all(novas)
    await db.commit()
    return [_para_schema(o) for o in novas]
