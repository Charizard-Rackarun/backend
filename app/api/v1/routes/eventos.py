from datetime import timedelta

from fastapi import APIRouter

from app.schemas.gestao import EventoSexta13
from app.services import sexta13, tempo
from app.services.formatacao import data_br

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.get("/sexta-13", response_model=EventoSexta13)
async def sexta_13():
    """Público: o frontend usa para exibir o banner temático e o contador da próxima Sexta 13."""
    hoje = tempo.hoje()
    ativo = sexta13.eh_sexta_13(hoje)
    proxima = hoje if ativo else sexta13.proxima_sexta_13(hoje + timedelta(days=1))
    mensagem = (
        "Hoje é Sexta 13! Ofertas secretas liberadas e pontos em dobro nos questionários."
        if ativo
        else f"A próxima Sexta 13 será em {data_br(proxima)}. Ofertas secretas e pontos em dobro!"
    )
    return EventoSexta13(
        ativo=ativo, nome=sexta13.NOME_EVENTO, mensagem=mensagem, proxima_data=proxima,
        multiplicador_pontos=sexta13.MULTIPLICADOR_PONTOS if ativo else 1,
    )
