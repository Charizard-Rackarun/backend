from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models import Estabelecimento

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


CurrentEstabelecimento = Annotated[Estabelecimento, Depends(get_current_estabelecimento)]