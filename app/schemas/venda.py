from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class VendaCreate(BaseModel):
    data: date
    produto: str = Field(min_length=1, max_length=120)
    quantidade: int = Field(gt=0)
    valor_total: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class VendaRead(VendaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int