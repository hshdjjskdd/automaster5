"""Данные callback-кнопок диагностики."""

from aiogram.filters.callback_data import CallbackData


class DiagCb(CallbackData, prefix="dg"):
    # menu | info | run | journal | entry | concl | tog | concl_ok | tools | buy
    action: str
    order_id: int = 0
    arg: str = ""
    n: int = 0
