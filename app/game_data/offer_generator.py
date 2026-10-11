"""Генератор предложений клиентов (чистая логика, без БД)."""

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.game_data.economy import OFFER_LIFETIME_HOURS
from app.game_data.fleet import FLEET, Trim
from app.game_data.scenarios import SCENARIOS, Scenario

CUSTOMER_NAMES: tuple[str, ...] = (
    "Алексей Смирнов", "Дмитрий Кузнецов", "Игорь Попов", "Сергей Васильев",
    "Андрей Петров", "Михаил Соколов", "Николай Орлов", "Павел Морозов",
    "Елена Волкова", "Ольга Фёдорова", "Наталья Новикова", "Татьяна Лебедева",
    "Виктор Зайцев", "Артём Беляев", "Мария Ковалёва", "Роман Григорьев",
)
COLORS: tuple[str, ...] = (
    "белый", "чёрный", "серебристый", "серый", "синий", "красный", "зелёный", "бежевый",
)
_PLATE_LETTERS = "АВЕКМНОРСТУХ"
_VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
_REGIONS = ("77", "50", "78", "63", "16", "52", "66", "74")
REFERENCE_YEAR = 2026


@dataclass(frozen=True, slots=True)
class OfferDraft:
    trim: Trim
    year: int
    mileage_km: int
    condition_pct: int
    color: str
    vin: str
    plate: str
    customer_name: str
    scenario: Scenario
    payment: int
    deadline_hours: int
    expires_at: datetime


def round_price(value: float) -> int:
    """Округляет цену до 50 ₽."""
    return int(round(value / 50.0)) * 50


def compute_payment(scenario: Scenario, trim: Trim, mileage_km: int) -> int:
    """Оплата зависит от сценария, комплектации (дороже сложнее) и пробега."""
    price = scenario.base_payment * trim.price_factor_pct / 100
    if mileage_km >= 200_000:
        price *= 1.15
    elif mileage_km >= 120_000:
        price *= 1.07
    return max(50, round_price(price))


def _plate(rng: random.Random) -> str:
    letters = [rng.choice(_PLATE_LETTERS) for _ in range(3)]
    return f"{letters[0]}{rng.randint(100, 999)}{letters[1]}{letters[2]} {rng.choice(_REGIONS)}"


def _vin(rng: random.Random) -> str:
    return "".join(rng.choice(_VIN_CHARS) for _ in range(17))


def generate_offer(rng: random.Random, level: int, now: datetime | None = None) -> OfferDraft:
    """Случайное предложение, подходящее игроку по уровню."""
    now = now or datetime.now(UTC)
    while True:
        trim = rng.choice(FLEET)
        fitting = [s for s in SCENARIOS if s.fits(trim.model, trim.transmission, level)]
        if fitting:
            break
    scenario = rng.choice(fitting)
    year = rng.choice(trim.years)
    age = max(1, REFERENCE_YEAR - year)
    mileage = min(450_000, int(age * rng.randint(8_000, 20_000)) // 100 * 100)
    condition = max(30, min(95, 95 - age * 2 - mileage // 20_000 + rng.randint(-5, 5)))
    return OfferDraft(
        trim=trim,
        year=year,
        mileage_km=mileage,
        condition_pct=condition,
        color=rng.choice(COLORS),
        vin=_vin(rng),
        plate=_plate(rng),
        customer_name=rng.choice(CUSTOMER_NAMES),
        scenario=scenario,
        payment=compute_payment(scenario, trim, mileage),
        deadline_hours=scenario.deadline_hours,
        expires_at=now + timedelta(hours=OFFER_LIFETIME_HOURS),
    )
