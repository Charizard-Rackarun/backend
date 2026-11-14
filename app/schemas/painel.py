"""Schemas que espelham exatamente os tipos TypeScript do frontend (src/types)."""

from typing import Annotated, Literal

from pydantic import BeforeValidator

from app.schemas.base import CamelModel

StrId = Annotated[str, BeforeValidator(str)]


class SalesPoint(CamelModel):
    month: str
    revenue: float
    orders: int


class CategoryPoint(CamelModel):
    name: str
    value: int
    color: str


class Activity(CamelModel):
    id: str
    title: str
    description: str
    time: str
    type: Literal["coupon", "sale", "consumer", "campaign"]


class DashboardData(CamelModel):
    revenue: float
    revenue_change: float
    orders: int
    orders_change: float
    average_ticket: float
    average_ticket_change: float
    active_consumers: int
    consumer_change: float
    sales_series: list[SalesPoint]
    category_series: list[CategoryPoint]
    recent_activity: list[Activity]


class ConsumerSegment(CamelModel):
    id: str
    name: str
    count: int
    percentage: int
    trend: int
    color: str
    interests: list[str]


class Opportunity(CamelModel):
    id: StrId
    title: str
    description: str
    stores: list[str]
    potential: str
    confidence: int
    category: str
    priority: Literal["Alta", "Média", "Baixa"]


class Campaign(CamelModel):
    id: StrId
    name: str
    store: str
    type: str
    status: Literal["Ativa", "Agendada", "Encerrada"]
    reach: int
    redemptions: int
    start_date: str
    end_date: str
    discount: str


class Reward(CamelModel):
    id: StrId
    title: str
    store: str
    description: str
    discount: str
    category: str
    expires: str
    code: str


class RewardSummary(CamelModel):
    points: int
    level: str
    next_level_points: int
    coupons: list[Reward]
