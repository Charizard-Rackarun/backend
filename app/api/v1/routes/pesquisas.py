from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.models import Pesquisa
from app.schemas.pesquisa import PesquisaCreate, PesquisaResposta

router = APIRouter(prefix="/pesquisas", tags=["Pesquisas"])

PONTOS_POR_PESQUISA = 10  # provisório até existir o módulo de recompensas


@router.post("", response_model=PesquisaResposta, status_code=status.HTTP_201_CREATED)
async def registrar_pesquisa(dados: PesquisaCreate, db: DbSession):
    pesquisa = Pesquisa(
        categorias=[c.value for c in dados.categorias],
        frequencia_visita=dados.frequencia_visita.value,
    )
    db.add(pesquisa)
    await db.commit()
    await db.refresh(pesquisa)
    return PesquisaResposta(id=pesquisa.id, pontos_ganhos=PONTOS_POR_PESQUISA)