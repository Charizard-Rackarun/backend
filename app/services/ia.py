"""IA generativa: transforma estatísticas agregadas em recomendações em linguagem natural.

Só números agregados são enviados ao provedor, nunca respostas individuais.
Se a chave não estiver configurada ou a chamada falhar, o chamador usa o texto padrão.
"""

import logging

import httpx

from app.core.config import settings
from app.services.analytics import Regra

logger = logging.getLogger(__name__)

API_URL = "https://api.anthropic.com/v1/messages"
SYSTEM = (
    "Você é um consultor comercial de shopping center. Responda em português do Brasil, "
    "em no máximo 2 frases, com uma recomendação prática de campanha. "
    "Use somente os números fornecidos e não invente dados."
)


async def refinar_descricao(regra: Regra, segmento_loja: str) -> str | None:
    if not settings.ai_api_key:
        return None
    prompt = (
        f"Segmento da loja do lojista: {segmento_loja}.\n"
        f"Padrão encontrado nas pesquisas (dados agregados e anônimos): entre visitantes interessados em "
        f"{regra.antecedente}, {round(regra.confianca * 100)}% também se interessam por {regra.consequente} "
        f"(lift {regra.lift:.1f}, {regra.ocorrencias} respostas). "
        "Escreva a recomendação para o lojista."
    )
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            resposta = await client.post(
                API_URL,
                headers={
                    "x-api-key": settings.ai_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.ai_model,
                    "max_tokens": 300,
                    "system": SYSTEM,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resposta.raise_for_status()
            blocos = resposta.json()["content"]
    except (httpx.HTTPError, KeyError, ValueError) as erro:
        logger.warning("Falha ao chamar a IA generativa: %s", erro)
        return None
    texto = "".join(b.get("text", "") for b in blocos if b.get("type") == "text").strip()
    return texto[:900] or None
