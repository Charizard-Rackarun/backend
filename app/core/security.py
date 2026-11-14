import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_password_hash = PasswordHash.recommended()  # Argon2
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _password_hash.verify(password, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def generate_token() -> str:
    """Token aleatório usado para identificar visitantes de forma anônima."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Só o hash do token do visitante é guardado no banco."""
    return hashlib.sha256(token.encode()).hexdigest()
