"""Каталог причин неисправностей и связь жалоб клиентов с возможными причинами.

Одна жалоба (сценарий) может быть вызвана несколькими разными причинами — так симптом
не называет поломку однозначно. Какая причина реальна, определяется при первой
проверке заказа и хранится в БД (скрыто от игрока).
"""

import random
from dataclasses import dataclass

from app.game_data.enums import FaultSeverity


@dataclass(frozen=True, slots=True)
class Cause:
    code: str  # до 16 символов: хранится в faults.code
    name: str
    system: str
    severity: FaultSeverity


CAUSES: tuple[Cause, ...] = (
    Cause("BAT_WEAK", "Изношенная аккумуляторная батарея", "Электрика", FaultSeverity.MODERATE),
    Cause("ALT_FAIL", "Неисправный генератор / реле-регулятор", "Электрика", FaultSeverity.SERIOUS),
    Cause("FUSE_BLOWN", "Перегоревший предохранитель", "Электрика", FaultSeverity.MINOR),
    Cause("WIRE_CORR", "Окисленные клеммы / плохая масса", "Электрика", FaultSeverity.MINOR),
    Cause("STARTER_FAIL", "Износ стартера / втягивающего реле", "Электрика", FaultSeverity.MODERATE),
    Cause("PLUGS_WORN", "Изношенные свечи зажигания", "Зажигание", FaultSeverity.MINOR),
    Cause("COIL_FAIL", "Неисправная катушка зажигания", "Зажигание", FaultSeverity.MODERATE),
    Cause("FUEL_PUMP_WEAK", "Слабый топливный насос", "Топливо", FaultSeverity.SERIOUS),
    Cause("FUEL_FILTER_CLOG", "Забитый топливный фильтр", "Топливо", FaultSeverity.MINOR),
    Cause("INTAKE_LEAK", "Подсос воздуха во впуске", "Впуск", FaultSeverity.MODERATE),
    Cause("MAF_DIRTY", "Загрязнённый датчик массового расхода воздуха", "Впуск", FaultSeverity.MINOR),
    Cause("COOLANT_LEAK", "Утечка охлаждающей жидкости", "Охлаждение", FaultSeverity.SERIOUS),
    Cause("THERMOSTAT_STUCK", "Неисправный термостат", "Охлаждение", FaultSeverity.MODERATE),
    Cause("FAN_FAIL", "Неисправен вентилятор радиатора", "Охлаждение", FaultSeverity.MODERATE),
    Cause("BRAKE_PADS_WORN", "Изношенные тормозные колодки", "Тормоза", FaultSeverity.SERIOUS),
    Cause("BRAKE_FLUID_OLD", "Обводнённая тормозная жидкость", "Тормоза", FaultSeverity.MODERATE),
    Cause("SUSP_LINK", "Изношенная стойка стабилизатора", "Подвеска", FaultSeverity.MINOR),
    Cause("SUSP_STRUT", "Изношенный амортизатор", "Подвеска", FaultSeverity.MODERATE),
    Cause("OIL_LEAK", "Течь масла (прокладка / сальник)", "Двигатель", FaultSeverity.MODERATE),
)

CAUSE_BY_CODE: dict[str, Cause] = {c.code: c for c in CAUSES}

if len(CAUSE_BY_CODE) != len(CAUSES) or any(len(c.code) > 16 for c in CAUSES):
    raise RuntimeError("Коды причин должны быть уникальными и не длиннее 16 символов")

# Жалоба -> возможные причины с весами. Нужно, чтобы симптом не определял поломку.
SCENARIO_CAUSES: dict[str, tuple[tuple[str, int], ...]] = {
    "brake_squeal": (("BRAKE_PADS_WORN", 5), ("BRAKE_FLUID_OLD", 2), ("SUSP_LINK", 1)),
    "knock_front": (("SUSP_LINK", 4), ("SUSP_STRUT", 3), ("BRAKE_PADS_WORN", 1)),
    "no_start_cold": (
        ("BAT_WEAK", 4), ("STARTER_FAIL", 3), ("WIRE_CORR", 2), ("ALT_FAIL", 1), ("FUSE_BLOWN", 1),
    ),
    "idle_unstable": (
        ("INTAKE_LEAK", 4), ("MAF_DIRTY", 3), ("PLUGS_WORN", 2), ("COIL_FAIL", 1),
    ),
    "oil_leak": (("OIL_LEAK", 6), ("COOLANT_LEAK", 1)),
    "overheat": (
        ("THERMOSTAT_STUCK", 3), ("COOLANT_LEAK", 3), ("FAN_FAIL", 3), ("FUSE_BLOWN", 1),
    ),
    "lights_dead": (("FUSE_BLOWN", 3), ("WIRE_CORR", 3), ("ALT_FAIL", 2), ("BAT_WEAK", 1)),
    "vaz_carburetor_like": (
        ("PLUGS_WORN", 3), ("COIL_FAIL", 3), ("FUEL_FILTER_CLOG", 2), ("INTAKE_LEAK", 1),
    ),
    "vaz_heater": (("THERMOSTAT_STUCK", 4), ("COOLANT_LEAK", 3)),
    "corolla_vibration": (("SUSP_STRUT", 3), ("SUSP_LINK", 3), ("PLUGS_WORN", 1)),
    "polo_dsg_like": (
        ("COIL_FAIL", 3), ("MAF_DIRTY", 3), ("INTAKE_LEAK", 2), ("PLUGS_WORN", 1),
    ),
    "solaris_suspension": (("SUSP_LINK", 4), ("SUSP_STRUT", 3)),
    "misfire_cel": (
        ("PLUGS_WORN", 4), ("COIL_FAIL", 3), ("INTAKE_LEAK", 1), ("FUSE_BLOWN", 1),
    ),
    "battery_drain": (("ALT_FAIL", 3), ("BAT_WEAK", 3), ("WIRE_CORR", 2), ("FUSE_BLOWN", 1)),
    "weak_acceleration": (
        ("FUEL_FILTER_CLOG", 3), ("FUEL_PUMP_WEAK", 3), ("PLUGS_WORN", 2),
        ("MAF_DIRTY", 2), ("INTAKE_LEAK", 1),
    ),
    "pulls_braking": (
        ("BRAKE_PADS_WORN", 3), ("SUSP_STRUT", 2), ("BRAKE_FLUID_OLD", 1), ("SUSP_LINK", 1),
    ),
}

for _code, _pool in SCENARIO_CAUSES.items():
    for _cause, _weight in _pool:
        if _cause not in CAUSE_BY_CODE or _weight <= 0:
            raise RuntimeError(f"Некорректная причина в сценарии {_code}: {_cause}")

# Какие цепи может затронуть перегоревший предохранитель в данном сценарии.
ALL_CIRCUITS: tuple[str, ...] = ("ignition", "fuel_pump", "fan", "lights")
FUSE_CIRCUITS_BY_SCENARIO: dict[str, tuple[str, ...]] = {
    "overheat": ("fan",),
    "lights_dead": ("lights",),
    "no_start_cold": ("ignition", "fuel_pump"),
    "misfire_cel": ("ignition",),
    "battery_drain": ("lights",),
}

# Следствия: износ одного узла часто портит другой.
_CONSEQUENCES: dict[str, tuple[str, float]] = {"ALT_FAIL": ("BAT_WEAK", 0.5)}
SECONDARY_CHANCE = 0.25
MAX_FAULTS = 2


@dataclass(frozen=True, slots=True)
class TruthFault:
    code: str
    detail: str = ""


def _pick_detail(code: str, scenario_code: str | None, rng: random.Random) -> str:
    if code == "FUSE_BLOWN":
        return rng.choice(FUSE_CIRCUITS_BY_SCENARIO.get(scenario_code or "", ALL_CIRCUITS))
    if code == "COIL_FAIL":
        return f"cyl:{rng.randint(1, 4)}"
    if code == "THERMOSTAT_STUCK":
        if scenario_code == "vaz_heater":
            return "open"
        if scenario_code == "overheat":
            return "closed"
        return rng.choice(("open", "closed"))
    if code == "INTAKE_LEAK":
        return rng.choice(("hose", "gasket"))
    if code == "ALT_FAIL":
        return rng.choice(("no_charge", "overcharge", "diode"))
    if code in ("SUSP_STRUT", "SUSP_LINK"):
        return rng.choice(("left", "right"))
    if code == "BRAKE_PADS_WORN":
        return rng.choice(("left", "right", "both"))
    return ""


def generate_truth(seed: str, scenario_code: str | None) -> list[TruthFault]:
    """Реальные неисправности автомобиля (1–2 штуки). Результат зависит только от seed."""
    rng = random.Random(seed)
    pool = SCENARIO_CAUSES.get(scenario_code or "")
    if pool is None:
        pool = tuple((c.code, 1) for c in CAUSES)
    codes = [code for code, _ in pool]
    weights = [weight for _, weight in pool]

    chosen = [rng.choices(codes, weights)[0]]
    consequence = _CONSEQUENCES.get(chosen[0])
    if consequence and rng.random() < consequence[1]:
        chosen.append(consequence[0])
    elif rng.random() < SECONDARY_CHANCE:
        rest = [c for c in codes if c not in chosen]
        if rest:
            rest_weights = [w for c, w in pool if c not in chosen]
            chosen.append(rng.choices(rest, rest_weights)[0])
    return [
        TruthFault(code, _pick_detail(code, scenario_code, rng)) for code in chosen[:MAX_FAULTS]
    ]
