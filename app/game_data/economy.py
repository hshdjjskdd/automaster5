"""Экономика и ограничения клиентских заказов."""

from datetime import datetime

from app.game_data.enums import OrderStatus

# Сколько предложений одновременно лежит на доске заказов.
BOARD_SIZE = 3

# Через сколько часов клиент «не дождался», и предложение исчезает.
OFFER_LIFETIME_HOURS = 12

# Премия за сдачу заказа до срока, в процентах от оплаты.
ON_TIME_BONUS_PERCENT = 15

# Штраф к репутации за отмену заказа, по которому работа уже началась.
CANCEL_AFTER_START_REPUTATION_PENALTY = 5

# Статусы, после начала которых отмена считается срывом работы клиента.
_STARTED_STATUSES = frozenset(
    {OrderStatus.DIAGNOSTICS, OrderStatus.AWAITING_PARTS, OrderStatus.IN_REPAIR}
)


def workshop_capacity(level: int) -> int:
    """Сколько заказов мастерская может вести одновременно.

    Уровни 1–2: один заказ, дальше +1 место каждые три уровня
    (3–5: два, 6–8: три, 9–10: четыре).
    """
    return 1 + max(level, 1) // 3


def potential_bonus(payment: int) -> int:
    """Размер премии за сдачу в срок для заказа с данной оплатой."""
    return payment * ON_TIME_BONUS_PERCENT // 100


def on_time_bonus(payment: int, deadline_at: datetime | None, now: datetime) -> int:
    """Премия, которая причитается за сдачу заказа в момент now.

    Нет срока или срок уже прошёл — премии нет.
    """
    if deadline_at is None or now > deadline_at:
        return 0
    return potential_bonus(payment)


def cancellation_penalty(status: OrderStatus) -> int | None:
    """Штраф к репутации за отмену заказа в данном статусе.

    0 — отмена бесплатна (работа ещё не начата); None — отменить нельзя
    (заказ готов к выдаче или уже закрыт).
    """
    if status == OrderStatus.NEW:
        return 0
    if status in _STARTED_STATUSES:
        return CANCEL_AFTER_START_REPUTATION_PENALTY
    return None
