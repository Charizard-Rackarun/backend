from fastapi import APIRouter

from app.api.v1.routes import auth, indicadores, pesquisas, vendas

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(pesquisas.router)
api_router.include_router(vendas.router)
api_router.include_router(indicadores.router)