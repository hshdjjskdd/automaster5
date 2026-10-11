"""Схемы клиентских заказов: карточки предложений и заказов в мастерской."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.game_data.enums import DriveType, FuelType, OfferStatus, OrderStatus, Transmission


class CarCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    brand: str
    model: str
    trim_name: str | None
    year: int
    body_type: str
    engine_code: str
    engine_volume_cc: int
    power_hp: int
    fuel_type: FuelType
    transmission: Transmission
    drive_type: DriveType
    mileage_km: int
    color: str
    plate: str
    vin: str
    condition_pct: int


class OfferCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    offer_id: int
    status: OfferStatus
    customer_name: str
    car: CarCard
    complaint: str
    symptoms: tuple[str, ...]
    payment: int
    potential_bonus: int
    deadline_hours: int
    expires_at: datetime


class WorkshopOrderCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: int
    status: OrderStatus
    customer_name: str
    car_id: int
    car: CarCard
    complaint: str
    symptoms: tuple[str, ...]
    reward: int
    potential_bonus: int
    created_at: datetime
    deadline_at: datetime | None
    # None — отменить нельзя; 0 — бесплатно; >0 — штраф к репутации.
    cancel_penalty: int | None


class Board(BaseModel):
    model_config = ConfigDict(frozen=True)

    offers: tuple[OfferCard, ...]
    active_orders: int
    capacity: int


class AcceptResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    offer_id: int
    order_id: int
    car_id: int


class CancelResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: int
    reputation_penalty: int
    reputation_after: int
