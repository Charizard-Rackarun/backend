"""Análise de preferências dos visitantes: segmentos e regras de associação.

Trabalha só com dados agregados e anônimos. Grupos com menos de `min_group` respostas
são descartados (k-anonimato), para nunca expor perfis individuais (LGPD / RNF01).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import permutations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Opcao, Pergunta, Resposta, RespostaItem
from app.services.formatacao import com_fuso


@dataclass
class Cestas:
    """Cada cesta = categorias escolhidas em uma submissão de questionário."""

    itens: list[tuple[frozenset[str], datetime]]
    nomes: dict[str, str]

    def nome(self, chave: str) -> str:
        return self.nomes.get(chave, chave.title())


@dataclass
class Segmento:
    nome: str
    contagem: int
    percentual: int
    tendencia: int
    interesses: list[str]


@dataclass
class Regra:
    antecedente: str
    consequente: str
    suporte: float
    confianca: float
    lift: float
    ocorrencias: int


async def carregar_cestas(db: AsyncSession) -> Cestas:
    consulta = (
        select(RespostaItem.resposta_id, Opcao.texto, Resposta.criado_em)
        .join(Opcao, Opcao.id == RespostaItem.opcao_id)
        .join(Pergunta, Pergunta.id == RespostaItem.pergunta_id)
        .join(Resposta, Resposta.id == RespostaItem.resposta_id)
        .where(Pergunta.dimensao == "categoria")
    )
    nomes: dict[str, str] = {}
    por_resposta: dict[int, tuple[set[str], datetime]] = {}
    for resposta_id, texto, quando in (await db.execute(consulta)).all():
        chave = texto.strip().casefold()
        nomes.setdefault(chave, texto.strip())
        conjunto, _ = por_resposta.setdefault(resposta_id, (set(), com_fuso(quando)))
        conjunto.add(chave)
    return Cestas([(frozenset(c), q) for c, q in por_resposta.values()], nomes)


def calcular_segmentos(cestas: Cestas, agora: datetime, min_group: int) -> list[Segmento]:
    total, atual, anterior = Counter(), Counter(), Counter()
    junto: dict[str, Counter] = defaultdict(Counter)
    for itens, quando in cestas.itens:
        for a in itens:
            total[a] += 1
            if quando >= agora - timedelta(days=30):
                atual[a] += 1
            elif quando >= agora - timedelta(days=60):
                anterior[a] += 1
            for b in itens:
                if a != b:
                    junto[a][b] += 1
    selecoes = sum(total.values())
    segmentos = []
    for a, n in total.most_common():
        if n < min_group:
            continue
        interesses = [cestas.nome(b) for b, c in junto[a].most_common(3) if c >= min_group]
        tendencia = round((atual[a] - anterior[a]) / anterior[a] * 100) if anterior[a] else 0
        segmentos.append(Segmento(cestas.nome(a), n, round(n / selecoes * 100), tendencia, interesses))
    return segmentos


def calcular_regras(cestas: Cestas, min_group: int) -> list[Regra]:
    """Regras de associação A -> B com suporte, confiança e lift."""
    n_total = len(cestas.itens)
    if n_total == 0:
        return []
    contagem, pares = Counter(), Counter()
    for itens, _ in cestas.itens:
        contagem.update(itens)
        pares.update(permutations(itens, 2))
    melhores: dict[frozenset[str], Regra] = {}
    for (a, b), n_ab in pares.items():
        if n_ab < min_group:
            continue
        confianca = n_ab / contagem[a]
        lift = confianca / (contagem[b] / n_total)
        if lift <= 1:
            continue
        regra = Regra(cestas.nome(a), cestas.nome(b), n_ab / n_total, confianca, lift, n_ab)
        chave = frozenset((a, b))
        if chave not in melhores or regra.confianca > melhores[chave].confianca:
            melhores[chave] = regra
    return sorted(melhores.values(), key=lambda r: r.lift * r.confianca, reverse=True)


def classificar(regra: Regra) -> tuple[str, str]:
    if regra.confianca >= 0.7 and regra.lift >= 1.2:
        return "Alta", "Alto potencial"
    if regra.confianca >= 0.5:
        return "Média", "Potencial moderado"
    return "Baixa", "Potencial a validar"


def descricao_padrao(regra: Regra) -> str:
    return (
        f"Entre os visitantes interessados em {regra.antecedente}, "
        f"{round(regra.confianca * 100)}% também demonstram interesse em {regra.consequente}. "
        f"Sugestão: campanha conjunta entre lojas de {regra.antecedente} e {regra.consequente}."
    )
