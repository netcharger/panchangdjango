"""Localization rendering services for Panchang output."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from .constants import (
    AMANTA_MONTH_NAMES,
    HORA_PLANETS,
    KARANA_NAMES,
    NAKSHATRA_NAMES,
    PAKSHA_NAMES,
    PURNIMANTA_MONTH_NAMES,
    SAKA_MONTH_NAMES,
    TITHI_NAMES,
    YOGA_NAMES,
)
from .profiles import ProfileAssets, get_profile_assets


def _map_name(base_name: str, base_seq: List[str], localized_seq: List[str]) -> str:
    try:
        idx = base_seq.index(base_name)
    except ValueError:
        return base_name
    if 0 <= idx < len(localized_seq):
        return localized_seq[idx]
    return base_name


def _localize_events(events: List[Dict[str, Any]], localized_names: List[str]) -> List[Dict[str, Any]]:
    localized_events: List[Dict[str, Any]] = []
    for event in events:
        ordinal = event.get("ordinal")
        name = event.get("name", "")
        if isinstance(ordinal, int) and 1 <= ordinal <= len(localized_names):
            name = localized_names[ordinal - 1]
        localized_events.append(
            {
                "name": name,
                "start": event.get("start"),
                "end": event.get("end"),
                "ordinal": ordinal,
            }
        )
    return localized_events


def _localize_horas(entries: List[str], profile: ProfileAssets) -> List[str]:
    localized_entries: List[str] = []
    planet_map = profile.hora_planet_map
    for entry in entries:
        if ": " in entry:
            planet, duration = entry.split(": ", 1)
            localized_entries.append(f"{planet_map.get(planet, planet)}: {duration}")
        else:
            localized_entries.append(entry)
    return localized_entries


def _apply_value_localization(raw: Dict[str, Any], profile: ProfileAssets) -> Dict[str, Any]:
    data = copy.deepcopy(raw)

    paksha_entry = data.get("Paksha")
    if isinstance(paksha_entry, dict) and "name" in paksha_entry:
        paksha_entry["name"] = _map_name(paksha_entry["name"], PAKSHA_NAMES, profile.paksha)

    amanta_entry = data.get("Amanta Month")
    if isinstance(amanta_entry, dict) and "name" in amanta_entry:
        amanta_entry["name"] = _map_name(amanta_entry["name"], AMANTA_MONTH_NAMES, profile.amanta_month)

    purnimanta_entry = data.get("Purnimanta Month")
    if isinstance(purnimanta_entry, dict) and "name" in purnimanta_entry:
        purnimanta_entry["name"] = _map_name(
            purnimanta_entry["name"], PURNIMANTA_MONTH_NAMES, profile.purnimanta_month
        )

    civil_entry = data.get("Indian Civil Calendar")
    if isinstance(civil_entry, dict) and "month" in civil_entry:
        civil_entry["month"] = _map_name(civil_entry["month"], SAKA_MONTH_NAMES, profile.saka_month)

    core = data.get("core_panchang", {})
    if isinstance(core, dict):
        if "Tithulu" in core:
            core["Tithulu"] = _localize_events(core["Tithulu"], profile.tithi_full)
        if "Nakshatramulu" in core:
            core["Nakshatramulu"] = _localize_events(core["Nakshatramulu"], profile.nakshatra)
        if "Karana" in core:
            core["Karana"] = _localize_events(core["Karana"], profile.karana)
        if "Yoga" in core:
            core["Yoga"] = _localize_events(core["Yoga"], profile.yoga)

    horas = data.get("horas")
    if isinstance(horas, dict):
        if "day" in horas:
            horas["day"] = _localize_horas(horas["day"], profile)
        if "night" in horas:
            horas["night"] = _localize_horas(horas["night"], profile)

    return data


def format_panchang_for_profile(raw: Dict[str, Any], profile_code: str) -> Dict[str, Any]:
    profile = get_profile_assets(profile_code)
    data = _apply_value_localization(raw, profile)

    sections: List[Dict[str, Any]] = []

    civil = data.get("Indian Civil Calendar", {})
    sections.append(
        {
            "title": profile.section_titles["indian_civil"],
            "items": [
                {"label": profile.field_labels["year"], "value": civil.get("year")},
                {"label": profile.field_labels["month"], "value": civil.get("month")},
                {"label": profile.field_labels["day_number"], "value": civil.get("day")},
            ],
        }
    )

    lunar_items = []
    amanta_entry = data.get("Amanta Month") or {}
    lunar_items.append(
        {"label": profile.field_labels["amanta_month"], "value": amanta_entry.get("name")}
    )
    purnimanta_entry = data.get("Purnimanta Month") or {}
    lunar_items.append(
        {"label": profile.field_labels["purnimanta_month"], "value": purnimanta_entry.get("name")}
    )
    paksha_entry = data.get("Paksha") or {}
    lunar_items.append(
        {"label": profile.field_labels["paksha"], "value": paksha_entry.get("name")}
    )
    sections.append({"title": profile.section_titles["lunar_context"], "items": lunar_items})

    sun_moon = data.get("sunrise_moonrise", {})
    sections.append(
        {
            "title": profile.section_titles["sun_moon"],
            "items": [
                {"label": profile.field_labels["sunrise"], "value": (sun_moon.get("Sunrise") or {}).get("value")},
                {"label": profile.field_labels["sunset"], "value": (sun_moon.get("Sunset") or {}).get("value")},
                {"label": profile.field_labels["moonrise"], "value": (sun_moon.get("Moonrise") or {}).get("value")},
                {"label": profile.field_labels["moonset"], "value": (sun_moon.get("Moonset") or {}).get("value")},
            ],
        }
    )

    core = data.get("core_panchang", {})
    core_items: List[Dict[str, Any]] = []
    if "Tithulu" in core:
        core_items.append(
            {
                "label": profile.field_labels["tithi"],
                "type": "event_list",
                "events": core["Tithulu"],
                "event_labels": profile.event_labels,
            }
        )
    if "Nakshatramulu" in core:
        core_items.append(
            {
                "label": profile.field_labels["nakshatra"],
                "type": "event_list",
                "events": core["Nakshatramulu"],
                "event_labels": profile.event_labels,
            }
        )
    if "Karana" in core:
        core_items.append(
            {
                "label": profile.field_labels["karana"],
                "type": "event_list",
                "events": core["Karana"],
                "event_labels": profile.event_labels,
            }
        )
    if "Yoga" in core:
        core_items.append(
            {
                "label": profile.field_labels["yoga"],
                "type": "event_list",
                "events": core["Yoga"],
                "event_labels": profile.event_labels,
            }
        )
    sections.append({"title": profile.section_titles["core_panchang"], "items": core_items})

    auspicious = data.get("auspicious_timings", {})
    sections.append(
        {
            "title": profile.section_titles["auspicious"],
            "items": [
                {
                    "label": profile.auspicious_labels.get(label, label),
                    "value": info.get("value") if isinstance(info, dict) else info,
                }
                for label, info in auspicious.items()
            ],
        }
    )

    inauspicious = data.get("inauspicious_timings", {})
    sections.append(
        {
            "title": profile.section_titles["inauspicious"],
            "items": [
                {
                    "label": profile.inauspicious_labels.get(label, label),
                    "value": info.get("value") if isinstance(info, dict) else info,
                }
                for label, info in inauspicious.items()
            ],
        }
    )

    horas = data.get("horas", {})
    sections.append(
        {
            "title": profile.section_titles["horas"],
            "items": [
                {"label": profile.field_labels["day_horas"], "value": horas.get("day", [])},
                {"label": profile.field_labels["night_horas"], "value": horas.get("night", [])},
            ],
        }
    )

    festivals: Optional[List[str]] = data.get("festivals")
    sections.append(
        {
            "title": profile.section_titles["festivals"],
            "items": [
                {
                    "label": profile.section_titles["festivals"],
                    "value": festivals or profile.field_labels["no_festivals"],
                }
            ],
        }
    )

    localized_output = {
        "profile": {
            "code": profile.code,
            "language": profile.language,
            "script": profile.script,
        },
        "date": data.get("date"),
        "sections": sections,
    }

    return localized_output



