import os

# Os testes NUNCA devem tocar o banco real (Supabase): forçamos um SQLite em memória.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SECRET_KEY"] = "chave-apenas-para-testes-com-32-bytes-ou-mais"
os.environ["MIN_GROUP_SIZE"] = "2"
os.environ["AI_API_KEY"] = ""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services import tempo
from tests.helpers import DIA_COMUM


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(tempo, "hoje", lambda: DIA_COMUM)  # testes não dependem do dia real
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with maker() as sessao:
            yield sessao

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()
