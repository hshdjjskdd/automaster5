"""Клиентские заказы: доска предложений, принятие, мастерская, отмена.

Диагностика и ремонт здесь не выполняются — только приём машины в мастерскую
и управление заказом до начала работ. Все операции привязаны к player_id:
чужие предложения и заказы недоступны (для них возвращается «не найдено»).
"""

import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    InvalidOrderState,
    OfferNotFound,
    OfferUnavailable,
    OrderNotFound,
    OrderStateConflict,
    PlayerNotFound,
    WorkshopFull,
)
from app.game_data.economy import (
    BOARD_SIZE,
    cancellation_penalty,
    potential_bonus,
    workshop_capacity,
)
from app.game_data.enums import OfferStatus, OrderStatus
from app.game_data.offer_generator import OfferDraft, generate_offer
from app.game_data.order_flow import ACTIVE_STATUSES
from app.models import Car, CarConfiguration, ClientOffer
from app.models.types import utc_now
from app.repositories import (
    CarRepository,
    OfferRepository,
    OrderRepository,
    PlayerRepository,
)
from app.schemas import (
    AcceptResult,
    Board,
    CancelResult,
    CarCard,
    CarConfigurationData,
    CarData,
    OfferCard,
    WorkshopOrderCard,
)
from app.services.transaction import atomic

logger = logging.getLogger(__name__)

_CANCELLABLE = frozenset(
    {
        OrderStatus.NEW,
        OrderStatus.DIAGNOSTICS,
        OrderStatus.AWAITING_PARTS,
        OrderStatus.IN_REPAIR,
    }
)


def _config_data(draft: OfferDraft) -> CarConfigurationData:
    return CarConfigurationData(**draft.trim.configuration_kwargs(draft.year))


def _car_card(
    config: CarConfiguration,
    *,
    trim_name: str | None,
    mileage_km: int,
    color: str,
    plate: str,
    vin: str,
    condition_pct: int,
) -> CarCard:
    return CarCard(
        brand=config.brand,
        model=config.model,
        trim_name=trim_name,
        year=config.year,
        body_type=config.body_type,
        engine_code=config.engine_code,
        engine_volume_cc=config.engine_volume_cc,
        power_hp=config.power_hp,
        fuel_type=config.fuel_type,
        transmission=config.transmission,
        drive_type=config.drive_type,
        mileage_km=mileage_km,
        color=color,
        plate=plate,
        vin=vin,
        condition_pct=condition_pct,
    )


def _offer_card(offer: ClientOffer) -> OfferCard:
    return OfferCard(
        offer_id=offer.id,
        status=offer.status,
        customer_name=offer.customer_name,
        car=_car_card(
            offer.configuration,
            trim_name=offer.trim_name,
            mileage_km=offer.mileage_km,
            color=offer.color,
            plate=offer.plate,
            vin=offer.vin,
            condition_pct=offer.condition_pct,
        ),
        complaint=offer.complaint,
        symptoms=tuple(line for line in offer.symptoms.split("\n") if line),
        payment=offer.payment,
        potential_bonus=potential_bonus(offer.payment),
        deadline_hours=offer.deadline_hours,
        expires_at=offer.expires_at,
    )


class ClientOrderService:
    def __init__(self, session: AsyncSession, rng: random.Random | None = None) -> None:
        self._session = session
        self._rng = rng or random.Random()
        self._players = PlayerRepository(session)
        self._offers = OfferRepository(session)
        self._orders = OrderRepository(session)
        self._cars = CarRepository(session)

    # --- доска предложений -------------------------------------------------

    async def get_board(self, player_id: int, *, now: datetime | None = None) -> Board:
        """Актуальная доска: протухшие предложения закрываются, нехватка добирается."""
        now = now or utc_now()
        async with atomic(self._session):
            await self._offers.expire_stale(player_id, now)  # write: берём блокировку
            level = await self._players.get_level(player_id)
            if level is None:
                raise PlayerNotFound(player_id)
            missing = BOARD_SIZE - await self._offers.count_available(player_id)
            for _ in range(max(0, missing)):
                await self._add_offer(player_id, generate_offer(self._rng, level, now))
            active = await self._orders.count_active(player_id)
        offers = await self._offers.list_available(player_id)
        return Board(
            offers=tuple(_offer_card(o) for o in offers),
            active_orders=active,
            capacity=workshop_capacity(level),
        )

    async def _add_offer(self, player_id: int, draft: OfferDraft) -> None:
        config = await self._cars.get_or_create_configuration(_config_data(draft))
        await self._offers.add(
            player_id=player_id,
            configuration_id=config.id,
            draft_fields={
                "trim_name": draft.trim.name,
                "vin": draft.vin,
                "plate": draft.plate,
                "mileage_km": draft.mileage_km,
                "color": draft.color,
                "condition_pct": draft.condition_pct,
                "customer_name": draft.customer_name,
                "scenario_code": draft.scenario.code,
                "complaint": draft.scenario.complaint,
                "symptoms": "\n".join(draft.scenario.symptoms),
                "payment": draft.payment,
                "deadline_hours": draft.deadline_hours,
                "expires_at": draft.expires_at,
            },
        )

    async def get_offer(self, player_id: int, offer_id: int) -> OfferCard:
        offer = await self._offers.get(player_id, offer_id)
        if offer is None:
            raise OfferNotFound(offer_id)
        return _offer_card(offer)

    # --- принятие и отказ --------------------------------------------------

    async def accept_offer(
        self, player_id: int, offer_id: int, *, now: datetime | None = None
    ) -> AcceptResult:
        """Принимает предложение: создаёт автомобиль и заказ (NEW) — машина в мастерской.

        Всё в одной транзакции: при нехватке места или любой ошибке предложение
        остаётся доступным. Параллельное двойное принятие даёт один заказ.

        Raises: OfferNotFound, OfferUnavailable, WorkshopFull.
        """
        now = now or utc_now()
        try:
            async with atomic(self._session):
                claimed = await self._offers.resolve_if_available(
                    player_id=player_id, offer_id=offer_id, new=OfferStatus.ACCEPTED, now=now
                )
                if not claimed:
                    if await self._offers.get(player_id, offer_id) is None:
                        raise OfferNotFound(offer_id)
                    raise OfferUnavailable(offer_id)
                offer = await self._offers.get(player_id, offer_id)
                level = await self._players.get_level(player_id)
                if offer is None or level is None:
                    raise OfferNotFound(offer_id)
                capacity = workshop_capacity(level)
                if await self._orders.count_active(player_id) >= capacity:
                    raise WorkshopFull(capacity)
                car = await self._cars.create_car(
                    player_id=player_id,
                    configuration_id=offer.configuration_id,
                    data=CarData(
                        vin=offer.vin,
                        plate=offer.plate,
                        mileage_km=offer.mileage_km,
                        color=offer.color,
                        condition_pct=offer.condition_pct,
                    ),
                )
                order = await self._orders.create(
                    player_id=player_id,
                    car_id=car.id,
                    customer_name=offer.customer_name,
                    complaint=offer.complaint,
                    reward=offer.payment,
                    deadline_at=now + timedelta(hours=offer.deadline_hours),
                )
                await self._offers.link_order(offer_id=offer_id, order_id=order.id)
                result = AcceptResult(offer_id=offer_id, order_id=order.id, car_id=car.id)
        except IntegrityError as exc:
            # VIN/номер уже занят другим автомобилем — предложение считаем недоступным.
            raise OfferUnavailable(offer_id) from exc
        logger.info("Игрок %s принял предложение %s -> заказ %s", player_id, offer_id, result.order_id)
        return result

    async def decline_offer(
        self, player_id: int, offer_id: int, *, now: datetime | None = None
    ) -> None:
        """Отказывается от предложения. Бесплатно, репутация не меняется."""
        now = now or utc_now()
        async with atomic(self._session):
            done = await self._offers.resolve_if_available(
                player_id=player_id, offer_id=offer_id, new=OfferStatus.DECLINED, now=now
            )
            if not done:
                if await self._offers.get(player_id, offer_id) is None:
                    raise OfferNotFound(offer_id)
                raise OfferUnavailable(offer_id)

    # --- мастерская --------------------------------------------------------

    async def list_workshop(self, player_id: int) -> list[WorkshopOrderCard]:
        """Активные заказы игрока (машины в мастерской)."""
        orders = await self._orders.list_for_player(
            player_id, statuses=ACTIVE_STATUSES, limit=50
        )
        return [await self._order_card(player_id, o.id) for o in reversed(orders)]

    async def get_workshop_order(self, player_id: int, order_id: int) -> WorkshopOrderCard:
        return await self._order_card(player_id, order_id)

    async def _order_card(self, player_id: int, order_id: int) -> WorkshopOrderCard:
        order = await self._orders.get(player_id, order_id, with_details=True)
        if order is None:
            raise OrderNotFound(order_id)
        car: Car = order.car
        config = (await self._cars.get(player_id, car.id, with_configuration=True))
        assert config is not None
        offer = await self._offers.get_by_order(player_id, order_id)
        return WorkshopOrderCard(
            order_id=order.id,
            status=order.status,
            customer_name=order.customer_name,
            car_id=car.id,
            car=_car_card(
                config.configuration,
                trim_name=offer.trim_name if offer else None,
                mileage_km=car.mileage_km,
                color=car.color,
                plate=car.plate,
                vin=car.vin,
                condition_pct=car.condition_pct,
            ),
            complaint=order.complaint,
            symptoms=tuple(
                line for line in (offer.symptoms.split("\n") if offer else []) if line
            ),
            reward=order.reward,
            potential_bonus=potential_bonus(order.reward),
            created_at=order.created_at,
            deadline_at=order.deadline_at,
            cancel_penalty=cancellation_penalty(order.status),
        )

    # --- отмена ------------------------------------------------------------

    async def cancel_order(self, player_id: int, order_id: int) -> CancelResult:
        """Отменяет заказ в мастерской.

        NEW — бесплатно; диагностика/ожидание деталей/ремонт — штраф к репутации;
        READY и закрытые заказы отменить нельзя.

        Raises: OrderNotFound, InvalidOrderState, OrderStateConflict.
        """
        async with atomic(self._session):
            locked = await self._orders.touch_if_status(
                order_id=order_id, player_id=player_id, statuses=_CANCELLABLE
            )
            order = await self._orders.get(player_id, order_id)
            if order is None:
                raise OrderNotFound(order_id)
            if not locked:
                raise InvalidOrderState(order_id, order.status)
            penalty = cancellation_penalty(order.status)
            if penalty is None:
                raise InvalidOrderState(order_id, order.status)
            changed = await self._orders.transition_status(
                order_id=order_id,
                player_id=player_id,
                expected=order.status,
                new=OrderStatus.CANCELLED,
            )
            if not changed:
                raise OrderStateConflict(order_id)
            if penalty:
                reputation = await self._players.change_reputation(player_id, -penalty)
            else:
                reputation = await self._players.get_reputation(player_id)
        assert reputation is not None
        return CancelResult(
            order_id=order_id, reputation_penalty=penalty, reputation_after=reputation
        )
