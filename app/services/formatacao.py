from datetime import UTC, date, datetime
from decimal import Decimal

CORES = ["#3157D5", "#8B6CE8", "#21A67A", "#F0A34A", "#AAB4C5"]
MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def brl(valor: float | Decimal) -> str:
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def data_curta(d: date) -> str:
    return f"{d.day} {MESES_ABREV[d.month - 1].lower()}, {d.year}"


def com_fuso(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def tempo_relativo(dt: datetime) -> str:
    segundos = int((datetime.now(UTC) - com_fuso(dt)).total_seconds())
    if segundos < 60:
        return "Agora há pouco"
    if segundos < 3600:
        return f"Há {segundos // 60} min"
    if segundos < 86400:
        return f"Há {segundos // 3600} h"
    return f"Há {segundos // 86400} d"
