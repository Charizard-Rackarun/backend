from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import CamelModel

Tipo = Literal["unica", "multipla", "escala", "sim_nao"]
Dimensao = Literal["categoria", "frequencia"]

# Tipos com opções fixas: o servidor gera as opções, o lojista não digita nada
OPCOES_FIXAS: dict[str, list[str]] = {
    "escala": ["1 - Muito ruim", "2 - Ruim", "3 - Regular", "4 - Bom", "5 - Excelente"],
    "sim_nao": ["Sim", "Não"],
}


class OpcaoCreate(CamelModel):
    texto: str = Field(min_length=1, max_length=80)
    exclusiva: bool = False


class PerguntaCreate(CamelModel):
    texto: str = Field(min_length=3, max_length=200)
    tipo: Tipo = "unica"
    dimensao: Dimensao | None = None
    obrigatoria: bool = True
    max_selecoes: int | None = Field(default=None, ge=1, le=12)
    opcoes: list[OpcaoCreate] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validar_logica(self):
        if self.tipo in OPCOES_FIXAS:
            if self.dimensao == "categoria":
                raise ValueError("Perguntas de escala ou de sim/não não podem ser usadas como interesses")
            self.opcoes = [OpcaoCreate(texto=t) for t in OPCOES_FIXAS[self.tipo]]
            self.max_selecoes = None
            return self

        for opcao in self.opcoes:
            opcao.texto = opcao.texto.strip()
        textos = [o.texto for o in self.opcoes]
        if len(textos) < 2 or not all(textos):
            raise ValueError("Cada pergunta precisa de pelo menos 2 opções preenchidas")
        if len({t.casefold() for t in textos}) != len(textos):
            raise ValueError(f"A pergunta “{self.texto}” tem opções repetidas")

        if self.tipo == "unica":
            self.max_selecoes = None
            for opcao in self.opcoes:
                opcao.exclusiva = False
            return self

        exclusivas = [o for o in self.opcoes if o.exclusiva]
        if len(exclusivas) > 1:
            raise ValueError("Use no máximo uma opção exclusiva por pergunta")
        livres = len(self.opcoes) - len(exclusivas)
        if self.max_selecoes is not None and self.max_selecoes > livres:
            raise ValueError("O limite de seleções é maior que o número de opções")
        return self


class QuestionarioCreate(CamelModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str | None = Field(default=None, max_length=300)
    pontos: int = Field(default=10, ge=1, le=100)
    perguntas: list[PerguntaCreate] = Field(min_length=1, max_length=15)

    @model_validator(mode="after")
    def ao_menos_uma_obrigatoria(self):
        if not any(p.obrigatoria for p in self.perguntas):
            raise ValueError("Deixe pelo menos uma pergunta obrigatória")
        return self


class OpcaoRead(CamelModel):
    id: int
    texto: str
    exclusiva: bool


class PerguntaRead(CamelModel):
    id: int
    texto: str
    tipo: str
    dimensao: str | None
    obrigatoria: bool
    max_selecoes: int | None
    opcoes: list[OpcaoRead]


class QuestionarioRead(CamelModel):
    id: int
    titulo: str
    descricao: str | None
    ativo: bool
    pontos: int
    perguntas: list[PerguntaRead]


class QuestionarioPublico(QuestionarioRead):
    """O que o visitante vê: o questionário e quem está perguntando."""

    loja: str = ""


class QuestionarioPublicoResumo(CamelModel):
    """Item da lista "ganhe mais pontos", com pesquisas de todas as lojas parceiras."""

    id: int
    titulo: str
    descricao: str | None
    loja: str
    segmento: str
    pontos: int
    pontos_hoje: int  # já com o bônus da Sexta 13, quando ativo
    total_perguntas: int
    segundos_estimados: int
    respondido: bool


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
    total: int
    percentual: float


class PerguntaResultado(CamelModel):
    pergunta_id: int
    texto: str
    tipo: str
    respondentes: int  # quantas pessoas responderam esta pergunta
    media: float | None  # só para escala (1 a 5)
    opcoes: list[OpcaoResultado]


class ResultadosQuestionario(CamelModel):
    questionario_id: int
    total_respostas: int
    # True quando há poucas respostas: os números aparecem, mas com aviso de cautela
    amostra_pequena: bool
    minimo_recomendado: int
    perguntas: list[PerguntaResultado]
