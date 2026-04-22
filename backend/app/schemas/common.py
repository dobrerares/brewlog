"""Enums shared across the domain."""

from enum import Enum


class BrewMethod(str, Enum):
    V60 = "V60"
    AEROPRESS = "AeroPress"
    CHEMEX = "Chemex"
    FRENCH_PRESS = "French Press"
    ESPRESSO = "Espresso"
    MOKA_POT = "Moka Pot"
    COLD_BREW = "Cold Brew"
    OTHER = "Other"


class TasteResult(str, Enum):
    SOUR = "Sour"
    BITTER = "Bitter"
    WATERY = "Watery"
    ASTRINGENT = "Astringent"
    BALANCED = "Balanced"


class Process(str, Enum):
    WASHED = "Washed"
    NATURAL = "Natural"
    HONEY = "Honey"
    ANAEROBIC = "Anaerobic"
    OTHER = "Other"


class RoastLevel(str, Enum):
    LIGHT = "Light"
    MEDIUM = "Medium"
    MEDIUM_DARK = "Medium-dark"
    DARK = "Dark"


class EquipmentType(str, Enum):
    BREWER = "Brewer"
    GRINDER = "Grinder"
    SCALE = "Scale"
    KETTLE = "Kettle"
    OTHER = "Other"


class GrindType(str, Enum):
    STEPPED = "Stepped"
    STEPLESS = "Stepless"
