"""Жалобы клиентов и наблюдаемые симптомы.

Сценарий описывает то, что видит мастер при приёмке: жалобу словами клиента и
внешние симптомы. Причина поломки здесь намеренно не раскрывается — её предстоит
находить диагностикой (следующие этапы).
"""

from dataclasses import dataclass

from app.game_data.enums import Transmission


@dataclass(frozen=True, slots=True)
class Scenario:
    code: str
    complaint: str
    symptoms: tuple[str, ...]
    base_payment: int
    deadline_hours: int
    # None — подходит любой модели / любой коробке / любому уровню.
    models: frozenset[str] | None = None
    transmissions: frozenset[Transmission] | None = None
    min_level: int = 1

    def fits(self, model: str, transmission: Transmission, level: int) -> bool:
        return (
            level >= self.min_level
            and (self.models is None or model in self.models)
            and (self.transmissions is None or transmission in self.transmissions)
        )


_AUTO = frozenset({Transmission.AUTOMATIC, Transmission.CVT, Transmission.ROBOT})
_MANUAL = frozenset({Transmission.MANUAL})


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "brake_squeal", "Скрипят тормоза и машина хуже тормозит.",
        ("Скрип при торможении", "Педаль тормоза «мягкая»", "Лёгкая вибрация руля при торможении"),
        2_800, 24,
    ),
    Scenario(
        "knock_front", "На кочках что-то стучит спереди.",
        ("Глухой стук при проезде неровностей", "Лёгкий увод в сторону", "Неравномерный износ шин"),
        3_500, 24,
    ),
    Scenario(
        "no_start_cold", "Утром в мороз не заводится.",
        ("Стартер крутит вяло", "Приборы тускнеют при запуске", "Заводится только со второго раза"),
        2_200, 12,
    ),
    Scenario(
        "idle_unstable", "Плавают обороты на холостом ходу.",
        ("Обороты скачут 600–1200", "Двигатель иногда глохнет на светофоре", "Горит Check Engine"),
        3_000, 24,
    ),
    Scenario(
        "oil_leak", "Под машиной пятна масла.",
        ("Масляные пятна на асфальте", "Запах горелого масла после поездки", "Уровень масла падает"),
        4_200, 36,
    ),
    Scenario(
        "overheat", "Двигатель перегревается в пробках.",
        ("Стрелка температуры уходит к красной зоне", "Вентилятор радиатора не включается", "Запах антифриза"),
        3_800, 24, min_level=2,
    ),
    Scenario(
        "lights_dead", "Не работает часть света и мигают приборы.",
        ("Не горит ближний свет слева", "Приборная панель мигает", "Подсел аккумулятор"),
        1_900, 12,
    ),
    Scenario(
        "vaz_carburetor_like", "Троит двигатель и дёргается при разгоне.",
        ("Неровная работа мотора", "Провалы при нажатии на газ", "Чёрный выхлоп"),
        2_900, 24, models=frozenset({"2114", "Granta"}),
    ),
    Scenario(
        "vaz_heater", "Не греет печка, потеют стёкла.",
        ("Из дефлекторов идёт холодный воздух", "Запотевают стёкла", "Влажный коврик у пассажира"),
        2_400, 24, models=frozenset({"2114", "Granta"}),
    ),
    Scenario(
        "corolla_vibration", "Вибрация на скорости около 100 км/ч.",
        ("Дрожь руля на трассе", "Гул из передней части", "Стук при поворотах"),
        4_600, 36, models=frozenset({"Corolla"}),
    ),
    Scenario(
        "polo_dsg_like", "Загорелся Check Engine и пропали обороты.",
        ("Горит Check Engine", "Двигатель работает неровно", "Мигает контрольная лампа"),
        4_100, 36, models=frozenset({"Polo"}),
    ),
    Scenario(
        "solaris_suspension", "Стук и скрип подвески сзади.",
        ("Скрип при проезде «лежачих»", "Задняя часть «гуляет» в поворотах", "Стук на кочках"),
        3_900, 30, models=frozenset({"Solaris"}),
    ),
    Scenario(
        "misfire_cel", "Мигает Check Engine, двигатель троит.",
        ("Вибрация на холостом ходу", "Рывки при наборе скорости", "Мигает лампа Check Engine"),
        3_200, 24,
    ),
    Scenario(
        "battery_drain", "За ночь садится аккумулятор.",
        ("Утром стартер еле крутит", "Приборы тусклые на холостых", "Аккумулятор менялся недавно"),
        2_600, 24,
    ),
    Scenario(
        "weak_acceleration", "Машина не тянет на разгоне.",
        ("Провалы при полном газе", "Растёт расход топлива", "На холостых работает ровно"),
        3_600, 30,
    ),
    Scenario(
        "pulls_braking", "При торможении уводит в сторону.",
        ("Руль тянет вправо или влево", "Тормозной путь увеличился", "Педаль иногда «мягкая»"),
        3_100, 24,
    ),
)

# Контроль целостности при импорте: коды сценариев уникальны.
if len({s.code for s in SCENARIOS}) != len(SCENARIOS):
    raise RuntimeError("В сценариях повторяются коды")
