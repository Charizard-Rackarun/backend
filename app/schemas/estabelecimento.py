from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EstabelecimentoCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    segmento: str = Field(min_length=2, max_length=60)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class EstabelecimentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    segmento: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"