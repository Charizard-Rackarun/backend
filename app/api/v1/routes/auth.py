from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentEstabelecimento, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Estabelecimento
from app.schemas.estabelecimento import EstabelecimentoCreate, EstabelecimentoRead, Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registro", response_model=EstabelecimentoRead, status_code=status.HTTP_201_CREATED)
async def registrar(dados: EstabelecimentoCreate, db: DbSession):
    existente = await db.scalar(select(Estabelecimento).where(Estabelecimento.email == dados.email))
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    estabelecimento = Estabelecimento(
        nome=dados.nome,
        segmento=dados.segmento,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
    )
    db.add(estabelecimento)
    await db.commit()
    await db.refresh(estabelecimento)
    return estabelecimento


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    estabelecimento = await db.scalar(
        select(Estabelecimento).where(Estabelecimento.email == form.username)
    )
    if estabelecimento is None or not verify_password(form.password, estabelecimento.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(estabelecimento.id)))


@router.get("/me", response_model=EstabelecimentoRead)
async def me(estabelecimento: CurrentEstabelecimento):
    return estabelecimento