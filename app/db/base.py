from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column

CriadoEm = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now())
]


class Base(DeclarativeBase):
    pass
