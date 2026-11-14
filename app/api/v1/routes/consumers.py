from datetime import UTC, datetime

from fastapi import APIRouter

from app.api.deps import CurrentEstabelecimento, DbSession
from app.core.config import settings
from app.schemas.painel import ConsumerSegment
from app.services.analytics import calcular_segmentos, carregar_cestas
from app.services.formatacao import CORES

router = APIRouter(prefix="/consumers", tags=["Consumidores"])


@router.get("/segments", response_model=list[ConsumerSegment])
async def segmentos(_: CurrentEstabelecimento, db: DbSession):
    """Perfil agregado e anônimo dos visitantes do shopping, a partir das respostas dos questionários."""
    cestas = await carregar_cestas(db)
    resultado = calcular_segmentos(cestas, datetime.now(UTC), settings.min_group_size)
    return [
        ConsumerSegment(
            id=str(i + 1), name=s.nome, count=s.contagem, percentage=s.percentual,
            trend=s.tendencia, color=CORES[i % len(CORES)], interests=s.interesses,
        )
        for i, s in enumerate(resultado)
    ]
