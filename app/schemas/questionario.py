from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel

Tipo = Literal["unica", "multipla"]
Dimensao = Literal["categoria", "frequencia"]


class OpcaoCreate(CamelModel):
    texto: str = Field(min_length=1, max_length=80)


class PerguntaCreate(CamelModel):
    texto: str = Field(min_length=3, max_length=200)
    tipo: Tipo = "unica"
    dimensao: Dimensao | None = None
    opcoes: list[OpcaoCreate] = Field(min_length=2, max_length=12)


class QuestionarioCreate(CamelModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str | None = Field(default=None, max_length=300)
    pontos: int = Field(default=10, ge=1, le=100)
    perguntas: list[PerguntaCreate] = Field(min_length=1, max_length=15)


class OpcaoRead(CamelModel):
    id: int
    texto: str


class PerguntaRead(CamelModel):
    id: int
    texto: str
    tipo: str
    dimensao: str | None
    opcoes: list[OpcaoRead]


class QuestionarioRead(CamelModel):
    id: int
    titulo: str
    descricao: str | None
    ativo: bool
    pontos: int
    perguntas: list[PerguntaRead]


class QuestionarioResumo(CamelModel):
    id: int
    titulo: str
    ativo: bool
    pontos: int
    total_respostas: int


class QuestionarioStatus(CamelModel):
    ativo: bool


class RespostaPergunta(CamelModel):
    pergunta_id: int
    opcao_ids: list[int] = Field(min_length=1)


class RespostaCreate(CamelModel):
    respostas: list[RespostaPergunta] = Field(min_length=1)


class RespostaResultado(CamelModel):
    pontos_ganhos: int
    pontos_total: int
    bonus_sexta_13: bool
    # Só vem preenchido quando um visitante novo é criado: o frontend deve guardá-lo
    visitante_token: str | None


class OpcaoResultado(CamelModel):
    opcao_id: int
    texto: str
    total: int | None
    percentual: float | None


class PerguntaResultado(CamelModel):
    pergunta_id: int
    texto: str
    opcoes: list[OpcaoResultado]


class ResultadosQuestionario(CamelModel):
    questionario_id: int
    total_respostas: int
    # True quando há respostas de menos para exibir sem risco de identificar alguém
    suprimido: bool
    perguntas: list[PerguntaResultado]
