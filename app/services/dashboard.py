from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campanha, Cupom, Questionario, Resgate, Resposta, Venda
from app.schemas.painel import Activity, CategoryPoint, DashboardData, SalesPoint
from app.services import tempo
from app.services.formatacao import CORES, MESES_ABREV, brl, com_fuso, tempo_relativo


def _inicio_mes(d: date, delta: int) -> date:
    indice = d.year * 12 + (d.month - 1) + delta
    return date(indice // 12, indice % 12 + 1, 1)


def _variacao(atual: float, anterior: float) -> float:
    return round((atual - anterior) / anterior * 100, 1) if anterior else 0.0


async def _consumidores(db: AsyncSession, estab_id: int, de: datetime, ate: datetime) -> int:
    consulta = (
        select(func.count(func.distinct(Resposta.visitante_id)))
        .select_from(Resposta)
        .join(Questionario, Questionario.id == Resposta.questionario_id)
        .where(Questionario.estabelecimento_id == estab_id, Resposta.criado_em >= de, Resposta.criado_em < ate)
    )
    return await db.scalar(consulta) or 0


async def _atividades(db: AsyncSession, estab_id: int) -> list[Activity]:
    eventos: list[tuple[datetime, Activity]] = []

    vendas = await db.scalars(
        select(Venda).where(Venda.estabelecimento_id == estab_id).order_by(Venda.criado_em.desc()).limit(4)
    )
    for v in vendas:
        eventos.append((com_fuso(v.criado_em), Activity(
            id=f"sale-{v.id}", title="Venda registrada", description=f"{v.produto} · {brl(v.valor_total)}",
            time="", type="sale")))

    respostas = await db.execute(
        select(Resposta, Questionario.titulo)
        .join(Questionario, Questionario.id == Resposta.questionario_id)
        .where(Questionario.estabelecimento_id == estab_id)
        .order_by(Resposta.criado_em.desc()).limit(4)
    )
    for r, titulo in respostas.all():
        eventos.append((com_fuso(r.criado_em), Activity(
            id=f"consumer-{r.id}", title="Nova resposta recebida", description=titulo, time="", type="consumer")))

    resgates = await db.execute(
        select(Resgate, Cupom)
        .join(Cupom, Cupom.id == Resgate.cupom_id)
        .where(Cupom.estabelecimento_id == estab_id)
        .order_by(Resgate.criado_em.desc()).limit(4)
    )
    for r, c in resgates.all():
        eventos.append((com_fuso(r.criado_em), Activity(
            id=f"coupon-{r.id}", title="Cupom resgatado", description=f"{c.titulo} · {c.codigo}",
            time="", type="coupon")))

    campanhas = await db.scalars(
        select(Campanha).where(Campanha.estabelecimento_id == estab_id).order_by(Campanha.criado_em.desc()).limit(4)
    )
    for c in campanhas:
        eventos.append((com_fuso(c.criado_em), Activity(
            id=f"campaign-{c.id}", title="Nova campanha publicada", description=c.nome, time="", type="campaign")))

    eventos.sort(key=lambda e: e[0], reverse=True)
    return [a.model_copy(update={"time": tempo_relativo(q)}) for q, a in eventos[:4]]


async def montar_dashboard(db: AsyncSession, estab_id: int) -> DashboardData:
    hoje = tempo.hoje()
    ini_atual, ini_anterior = hoje - timedelta(days=30), hoje - timedelta(days=60)
    desde = min(_inicio_mes(hoje, -6), ini_anterior)

    linhas = (await db.execute(
        select(Venda.data, Venda.valor_total, Venda.categoria)
        .where(Venda.estabelecimento_id == estab_id, Venda.data >= desde, Venda.data <= hoje)
    )).all()

    atual, anterior = [0.0, 0], [0.0, 0]
    mensal: dict[tuple[int, int], list] = defaultdict(lambda: [0.0, 0])
    categorias: dict[str, float] = defaultdict(float)
    for data, valor, categoria in linhas:
        v = float(valor)
        mensal[(data.year, data.month)][0] += v
        mensal[(data.year, data.month)][1] += 1
        if data > ini_atual:
            atual[0] += v
            atual[1] += 1
            categorias[categoria or "Outros"] += v
        elif data > ini_anterior:
            anterior[0] += v
            anterior[1] += 1

    serie = []
    for delta in range(-6, 1):
        mes = _inicio_mes(hoje, delta)
        receita, pedidos = mensal.get((mes.year, mes.month), [0.0, 0])
        serie.append(SalesPoint(month=MESES_ABREV[mes.month - 1], revenue=round(receita, 2), orders=pedidos))

    total_cat = sum(categorias.values())
    ordenadas = sorted(categorias.items(), key=lambda kv: kv[1], reverse=True)
    principais, resto = ordenadas[:4], sum(v for _, v in ordenadas[4:])
    if resto:
        principais.append(("Outros", resto))
    por_categoria = [
        CategoryPoint(name=nome, value=round(v / total_cat * 100), color=CORES[i % len(CORES)])
        for i, (nome, v) in enumerate(principais)
    ] if total_cat else []

    agora = datetime.now(UTC)
    ativos = await _consumidores(db, estab_id, agora - timedelta(days=30), agora + timedelta(days=1))
    ativos_ant = await _consumidores(db, estab_id, agora - timedelta(days=60), agora - timedelta(days=30))

    ticket = atual[0] / atual[1] if atual[1] else 0.0
    ticket_ant = anterior[0] / anterior[1] if anterior[1] else 0.0

    return DashboardData(
        revenue=round(atual[0], 2), revenue_change=_variacao(atual[0], anterior[0]),
        orders=atual[1], orders_change=_variacao(atual[1], anterior[1]),
        average_ticket=round(ticket, 2), average_ticket_change=_variacao(ticket, ticket_ant),
        active_consumers=ativos, consumer_change=_variacao(ativos, ativos_ant),
        sales_series=serie, category_series=por_categoria,
        recent_activity=await _atividades(db, estab_id),
    )
