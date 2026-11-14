from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM, hash_token
from app.db.session import get_db
from app.models import Estabelecimento, Visitante

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_estabelecimento(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> Estabelecimento:
    erro = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        estabelecimento_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erro
    estabelecimento = await db.get(Estabelecimento, estabelecimento_id)
    if estabelecimento is None:
        raise erro
    return estabelecimento


async def get_visitante_opcional(
    db: DbSession, x_visitante_token: Annotated[str | None, Header()] = None
) -> Visitante | None:
    """Identifica o visitante anônimo pelo cabeçalho X-Visitante-Token, se enviado."""
    if not x_visitante_token:
        return None
    return await db.scalar(select(Visitante).where(Visitante.token_hash == hash_token(x_visitante_token)))


CurrentEstabelecimento = Annotated[Estabelecimento, Depends(get_current_estabelecimento)]
VisitanteOpcional = Annotated[Visitante | None, Depends(get_visitante_opcional)]