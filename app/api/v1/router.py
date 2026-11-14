from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    campaigns,
    cupons,
    dashboard,
    questionarios,
    rewards,
    vendas,
)

api_router = APIRouter(prefix="/api/v1")
for modulo in (auth, vendas, cupons, rewards, dashboard, campaigns):
    api_router.include_router(modulo.router)    
api_router.include_router(questionarios.router)
api_router.include_router(questionarios.public_router)
