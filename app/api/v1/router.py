from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    vendas,
)

api_router = APIRouter(prefix="/api/v1")
for modulo in (auth, vendas):
    api_router.include_router(modulo.router)
