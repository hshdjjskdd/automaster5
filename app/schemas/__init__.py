"""Pydantic-схемы обмена данными между слоями."""

from app.schemas.car import CarConfigurationData, CarData
from app.schemas.diagnostics import (
    CheckOption,
    CheckRunView,
    ConclusionFault,
    ConclusionResult,
    DiagnosticOverview,
    ReadingView,
    ToolOption,
)
from app.schemas.player import PlayerProfile, RegistrationResult, TelegramUserData
from app.schemas.results import (
    LedgerResult,
    OrderCompletionResult,
    ProgressResult,
    PurchaseResult,
)
from app.schemas.workshop import (
    AcceptResult,
    Board,
    CancelResult,
    CarCard,
    OfferCard,
    WorkshopOrderCard,
)

__all__ = [
    "CheckOption",
    "CheckRunView",
    "ConclusionFault",
    "ConclusionResult",
    "DiagnosticOverview",
    "ReadingView",
    "ToolOption",
    "AcceptResult",
    "Board",
    "CancelResult",
    "CarCard",
    "OfferCard",
    "WorkshopOrderCard",
    "CarConfigurationData",
    "CarData",
    "LedgerResult",
    "OrderCompletionResult",
    "PlayerProfile",
    "ProgressResult",
    "PurchaseResult",
    "RegistrationResult",
    "TelegramUserData",
]
