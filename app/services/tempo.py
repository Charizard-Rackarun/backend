from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def hoje() -> date:
    """Data de hoje no fuso configurado (TIMEZONE). Facilita fixar a data nos testes."""
    return datetime.now(ZoneInfo(settings.timezone)).date()
