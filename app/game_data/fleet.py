"""Автопарк клиентов: модели и их комплектации.

Комплектации одной модели различаются двигателем, мощностью, коробкой передач и
годами выпуска. От этого зависят и возможные поломки (см. scenarios.py), и цена
работ (price_factor_pct).
"""

from dataclasses import dataclass

from app.game_data.enums import DriveType, FuelType, Transmission

_MT = Transmission.MANUAL
_AT = Transmission.AUTOMATIC
_AMT = Transmission.ROBOT
_CVT = Transmission.CVT


@dataclass(frozen=True, slots=True)
class Trim:
    """Комплектация автомобиля."""

    brand: str
    model: str
    name: str
    years: tuple[int, ...]
    body_type: str
    engine_code: str
    engine_volume_cc: int
    power_hp: int
    transmission: Transmission
    price_factor_pct: int
    fuel_type: FuelType = FuelType.PETROL
    drive_type: DriveType = DriveType.FWD

    @property
    def title(self) -> str:
        return f"{self.brand} {self.model}"

    def configuration_kwargs(self, year: int) -> dict[str, object]:
        """Поля технической конфигурации для автомобиля этого года выпуска."""
        if year not in self.years:
            raise ValueError(f"{self.title} «{self.name}» не выпускалась в {year} году")
        return {
            "brand": self.brand,
            "model": self.model,
            "year": year,
            "body_type": self.body_type,
            "engine_code": self.engine_code,
            "engine_volume_cc": self.engine_volume_cc,
            "power_hp": self.power_hp,
            "fuel_type": self.fuel_type,
            "transmission": self.transmission,
            "drive_type": self.drive_type,
        }


FLEET: tuple[Trim, ...] = (
    # --- ВАЗ-2114 (хэтчбек) ---
    Trim("ВАЗ", "2114", "1.5 8V Стандарт", (2004, 2005, 2006, 2007, 2008),
         "хэтчбек", "2111", 1499, 78, _MT, 80),
    Trim("ВАЗ", "2114", "1.6 8V Норма", (2008, 2009, 2010, 2011, 2012),
         "хэтчбек", "21114", 1596, 81, _MT, 85),
    Trim("ВАЗ", "2114", "1.6 16V Люкс", (2009, 2010, 2011, 2012, 2013),
         "хэтчбек", "21124", 1599, 89, _MT, 95),
    # --- LADA Granta (седан) ---
    Trim("LADA", "Granta", "1.6 8V Стандарт", (2012, 2013, 2014, 2015),
         "седан", "11186", 1596, 87, _MT, 100),
    Trim("LADA", "Granta", "1.6 8V Норма (робот)", (2016, 2017, 2018, 2019),
         "седан", "11186", 1596, 87, _AMT, 105),
    Trim("LADA", "Granta", "1.6 8V Комфорт (автомат)", (2015, 2016, 2017, 2018),
         "седан", "11189", 1596, 98, _AT, 110),
    Trim("LADA", "Granta", "1.6 16V Люкс", (2018, 2019, 2020, 2021),
         "седан", "21127", 1596, 106, _MT, 115),
    # --- Toyota Corolla (седан) ---
    Trim("Toyota", "Corolla", "1.4 Стандарт", (2007, 2008, 2009, 2010),
         "седан", "4ZZ-FE", 1398, 97, _MT, 120),
    Trim("Toyota", "Corolla", "1.6 Комфорт", (2009, 2010, 2011, 2012),
         "седан", "1ZR-FE", 1598, 124, _MT, 135),
    Trim("Toyota", "Corolla", "1.6 Комфорт (робот)", (2008, 2009, 2010),
         "седан", "1ZR-FE", 1598, 124, _AMT, 140),
    Trim("Toyota", "Corolla", "1.8 Престиж (вариатор)", (2010, 2011, 2012, 2013),
         "седан", "2ZR-FE", 1798, 140, _CVT, 160),
    # --- Volkswagen Polo (седан) ---
    Trim("Volkswagen", "Polo", "Trendline 1.6 85 л.с.", (2011, 2012, 2013, 2014),
         "седан", "CFNA", 1598, 85, _MT, 125),
    Trim("Volkswagen", "Polo", "Comfortline 1.6 105 л.с.", (2011, 2012, 2013, 2014, 2015),
         "седан", "CFNA", 1598, 105, _MT, 135),
    Trim("Volkswagen", "Polo", "Comfortline 1.6 105 л.с. (автомат)", (2012, 2013, 2014, 2015),
         "седан", "CFNA", 1598, 105, _AT, 145),
    Trim("Volkswagen", "Polo", "Highline 1.6 110 л.с. (автомат)", (2016, 2017, 2018, 2019),
         "седан", "CWVA", 1598, 110, _AT, 155),
    # --- Hyundai Solaris (седан) ---
    Trim("Hyundai", "Solaris", "Active 1.4", (2011, 2012, 2013, 2014, 2015),
         "седан", "G4FA", 1396, 107, _MT, 125),
    Trim("Hyundai", "Solaris", "Comfort 1.4 (автомат)", (2011, 2012, 2013, 2014, 2015, 2016),
         "седан", "G4FA", 1396, 107, _AT, 135),
    Trim("Hyundai", "Solaris", "Comfort 1.6", (2012, 2013, 2014, 2015, 2016),
         "седан", "G4FC", 1591, 123, _MT, 140),
    Trim("Hyundai", "Solaris", "Elegance 1.6 (автомат)", (2013, 2014, 2015, 2016, 2017),
         "седан", "G4FC", 1591, 123, _AT, 150),
)

# Контроль целостности при импорте: название комплектации уникально внутри модели.
_identities = [(t.brand, t.model, t.name) for t in FLEET]
if len(set(_identities)) != len(_identities):
    raise RuntimeError("В автопарке повторяются комплектации")
del _identities
