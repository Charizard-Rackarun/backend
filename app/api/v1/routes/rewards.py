import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, VisitanteOpcional
from app.models import Cupom, Estabelecimento, Resgate, Visitante
from app.schemas.gestao import ResgateCreate, ResgateResposta
from app.schemas.painel import Reward, RewardSummary
from app.services import tempo
from app.services.formatacao import data_curta
from app.services.visitantes import nivel_para

router = APIRouter(tags=["Recompensas (visitante)"])


@router.get("/rewards", response_model=RewardSummary)
async def carteira(db: DbSession, visitante: VisitanteOpcional):
    """Saldo e cupons do visitante. Sem token, devolve a vitrine de cupons com 0 pontos."""
    hoje = tempo.hoje()
    consulta = (
        select(Cupom, Estabelecimento.nome)
        .join(Estabelecimento, Estabelecimento.id == Cupom.estabelecimento_id)
        .where(Cupom.ativo.is_(True), Cupom.validade >= hoje)
        .order_by(Cupom.id)
    )
    cupons = [
        Reward(
            id=c.id, title=c.titulo, store=loja, description=c.descricao, discount=c.desconto,
            category=c.categoria, expires=data_curta(c.validade), code=c.codigo,
        )
        for c, loja in (await db.execute(consulta)).all()
        if c.estoque is None or c.estoque > 0
    ]
    pontos = visitante.pontos if visitante else 0
    nivel, proximo = nivel_para(pontos)
    return RewardSummary(points=pontos, level=nivel, next_level_points=proximo, coupons=cupons)


@router.post("/coupons/redeem", response_model=ResgateResposta)
async def resgatar(dados: ResgateCreate, db: DbSession, visitante: VisitanteOpcional):
    """Troca pontos do visitante por um cupom e gera o código que ele apresenta na loja."""
    if visitante is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Responda um questionário para ganhar pontos antes de resgatar"
        )
    # Bloqueia as linhas para evitar resgate duplo ou estoque negativo em requisições simultâneas
    cupom = await db.scalar(
        select(Cupom).where(Cupom.codigo == dados.code.upper()).with_for_update()
    )
    saldo = await db.scalar(select(Visitante).where(Visitante.id == visitante.id).with_for_update())

    hoje = tempo.hoje()
    if cupom is None or not cupom.ativo or cupom.validade < hoje:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cupom indisponível")
    if cupom.estoque is not None and cupom.estoque <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cupom esgotado")
    if saldo.pontos < cupom.custo_pontos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pontos insuficientes")

    saldo.pontos -= cupom.custo_pontos
    if cupom.estoque is not None:
        cupom.estoque -= 1
    codigo = f"{cupom.codigo}-{secrets.token_hex(3).upper()}"
    db.add(Resgate(cupom_id=cupom.id, visitante_id=saldo.id, codigo=codigo))
    await db.commit()
    return ResgateResposta(
        success=True,
        message=f"Cupom resgatado! Apresente o código {codigo} na loja.",
        resgate_codigo=codigo,
        pontos_restantes=saldo.pontos,
    )
