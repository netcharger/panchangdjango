"""Base Sanskrit/English constants used across Panchang calculations."""

from __future__ import annotations

from typing import Dict, List


# Core astro label tables ---------------------------------------------------

TITHI_NAMES: List[str] = [
    "Pratipada",
    "Dvitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Purnima",
    "Pratipada",
    "Dvitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Amavasya",
]


PAKSHA_NAMES: List[str] = [
    "Shukla Paksha",
    "Krishna Paksha",
]


NAKSHATRA_NAMES: List[str] = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]


KARANA_NAMES: List[str] = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Garaja",
    "Vanija",
    "Vishti",
    "Shakuni",
    "Chatushpada",
    "Naga",
    "Kimstughna",
]


YOGA_NAMES: List[str] = [
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyan",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]


SAKA_MONTH_NAMES: List[str] = [
    "Chaitra",
    "Vaisakha",
    "Jyaistha",
    "Asadha",
    "Sravana",
    "Bhadra",
    "Asvina",
    "Kartika",
    "Agrahayana",
    "Pausa",
    "Magha",
    "Phalguna",
]


AMANTA_MONTH_NAMES: List[str] = SAKA_MONTH_NAMES
PURNIMANTA_MONTH_NAMES: List[str] = [
    "Chaitra",
    "Vaisakha",
    "Jyaistha",
    "Asadha",
    "Sravana",
    "Bhadra",
    "Asvina",
    "Kartika",
    "Margashirsha",
    "Pausa",
    "Magha",
    "Phalguna",
]


WEEKDAY_NAMES: List[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


HORA_PLANETS: List[str] = [
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
    "Saturn",
    "Jupiter",
    "Mars",
]


def identity_map(values: List[str]) -> Dict[str, str]:
    return {value: value for value in values}


ENGLISH_LOCALIZATION_DEFAULTS: Dict[str, Dict[str, str]] = {
    "tithi": identity_map(TITHI_NAMES[:15]),
    "tithi_full": identity_map(TITHI_NAMES),
    "nakshatra": identity_map(NAKSHATRA_NAMES),
    "paksha": identity_map(PAKSHA_NAMES),
    "weekday": identity_map(WEEKDAY_NAMES),
    "hora_planet": identity_map(HORA_PLANETS),
    "amanta_month": identity_map(AMANTA_MONTH_NAMES),
    "purnimanta_month": identity_map(PURNIMANTA_MONTH_NAMES),
}


