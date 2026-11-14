from datetime import date

from pydantic import Field, model_validator

from app.schemas.base import CamelModel


class CampanhaCreate(CamelModel):
    nome: str = Field(min_length=3, max_length=120)
    tipo: str = Field(min_length=2, max_length=40)
    desconto: str = Field(min_length=1, max_length=40)
    data_inicio: date
    data_fim: date
    alcance: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def datas_validas(self):
        if self.data_fim < self.data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        return self


class CupomCreate(CamelModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=3, max_length=200)
    desconto: str = Field(min_length=1, max_length=40)
    categoria: str = Field(min_length=2, max_length=40)
    custo_pontos: int = Field(ge=1, le=100000)
    estoque: int | None = Field(default=None, ge=1)
    validade: date
    exclusivo_sexta_13: bool = False
    campanha_id: int | None = None


class CupomRead(CamelModel):
    id: int
    titulo: str
    descricao: str
    desconto: str
    categoria: str
    codigo: str
    custo_pontos: int
    estoque: int | None
    validade: date
    ativo: bool
    exclusivo_sexta_13: bool


class ResgateCreate(CamelModel):
    code: str = Field(min_length=3, max_length=30)


class ResgateResposta(CamelModel):
    success: bool
    message: str
    resgate_codigo: str | None = None
    pontos_restantes: int | None = None


class ResgateValidar(CamelModel):
    codigo: str = Field(min_length=3, max_length=40)


class ResgateValidado(CamelModel):
    success: bool
    message: str


class EventoSexta13(CamelModel):
    ativo: bool
    nome: str
    mensagem: str
    proxima_data: date
    multiplicador_pontos: int
