from enum import StrEnum

from pydantic import BaseModel, Field


class Categoria(StrEnum):
    moda = "moda"
    alimentacao = "alimentacao"
    eletronicos = "eletronicos"
    casa_decoracao = "casa_decoracao"
    beleza = "beleza"
    lazer = "lazer"


class FrequenciaVisita(StrEnum):
    primeira_vez = "primeira_vez"
    mensal = "mensal"
    semanal = "semanal"


class PesquisaCreate(BaseModel):
    categorias: list[Categoria] = Field(min_length=1, max_length=6)
    frequencia_visita: FrequenciaVisita


class PesquisaResposta(BaseModel):
    id: int
    pontos_ganhos: int