"""
Full Panchang generator:
- Computes tithi & nakshatra at a given moment
- Finds next-change ("upto" time) for tithi & nakshatra
- Computes sunrise/sunset using Astral (local timezone)
- Computes Abhijit Muhurat, Rahu Kalam, Yamagandam, Gulika Kalam
- Emits JSON-like dict that matches previous schema
"""
# Source - https://stackoverflow.com/a
# Posted by Voy
# Retrieved 2025-11-07, License - CC BY-SA 4.0
import sys
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

import swisseph as swe
import datetime
import math
import pytz
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# Debug code removed for Django integration

from astral import LocationInfo
from astral.sun import sun
import json

from astral.moon import moonrise, moonset

import ephem # Added for civil calendar calculations

# ------------------ Config ------------------
LOCATION = {
    "name": "Chennai",
    "region": "India",
    "tz": "Asia/Kolkata",
    "lat": 13.0827,
    "lon": 80.2707
}

DATE_STR = "2025-12-25"  # YYYY-MM-DD
swe.set_ephe_path("")
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ------------------ Helpers ------------------
from .localization.constants import (
    AMANTA_MONTH_NAMES,
    HORA_PLANETS,
    KARANA_NAMES,
    NAKSHATRA_NAMES,
    PAKSHA_NAMES,
    PURNIMANTA_MONTH_NAMES,
    SAKA_MONTH_NAMES,
    TITHI_NAMES,
    WEEKDAY_NAMES,
    YOGA_NAMES,
)

# Traditional Panchang constants
SAMVATSARA_NAMES = [
    "ప్రభవ", "విభవ", "శుక్ల", "ప్రమోదూత", "ప్రజోత్తమ", "ఆంగీరస",
    "శ్రీముఖ", "భావ", "యువ", "ధాత", "ఈశ్వర", "బహుధాన్య",
    "ప్రమాథి", "విక్రమ", "వృష", "చిత్రభాను", "సుభాను", "తారణ",
    "పార్థివ", "వ్యయ", "సర్వజిత్", "సర్వధారి", "విరోధి", "వికృతి",
    "ఖర", "నందన", "విజయ", "జయ", "మన్మథ", "దుర్ముఖి",
    "హేమలంబి", "విలంబి", "వికారి", "శార్వరి", "ప్లవ",
    "శుభకృత్", "శోభకృత్", "క్రోధి", "విశ్వావసు", "పరాభవ",
    "ప్లవంగ", "కీలక", "సౌమ్య", "సాధారణ", "విరోధికృత్",
    "పరిధావి", "ప్రమాదీచ", "ఆనంద", "రాక్షస",
    "నల", "పింగళ", "కాళయుక్తి", "సిద్ధార్థి",
    "రౌద్రి", "దుర్మతి", "దుందుభి", "రుధిరోద్గారి",
    "రక్తాక్షి", "క్రోధన", "అక్షయ"
]

RITU_MAP = {
    "చైత్రం": "వసంత ఋతువు",
    "వైశాఖం": "వసంత ఋతువు",
    "జ్యేష్ఠం": "గ్రీష్మ ఋతువు",
    "ఆషాఢం": "గ్రీష్మ ఋతువు",
    "శ్రావణం": "వర్ష ఋతువు",
    "భాద్రపదం": "వర్ష ఋతువు",
    "ఆశ్వయుజం": "శరద్ ఋతువు",
    "కార్తీకం": "శరద్ ఋతువు",
    "మార్గశిరం": "హేమంత ఋతువు",
    "పుష్య": "హేమంత ఋతువు",
    "మాఘం": "శిశిర ఋతువు",
    "ఫాల్గుణం": "శిశిర ఋతువు",
}
from .localization.service import format_panchang_for_profile

LUNAR_MONTH_NAMES = AMANTA_MONTH_NAMES  # For simplicity, using Amanta names as default

# Saka epoch starts March 22, 79 CE in Gregorian calendar (March 21 in leap years)
SAKA_EPOCH_OFFSET = 78 # Saka year = Gregorian year - 78 or 79

def normalize_angle(a):
    return a % 360.0

def dt_to_jd_utc(dt_utc):
    if dt_utc.tzinfo is not None:
        dt_utc = dt_utc.astimezone(pytz.utc).replace(tzinfo=None)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def convert_gregorian_to_saka(greg_date):
    # Simplified conversion based on Indian Civil Calendar rules
    # Chaitra 1 falls on March 22 (or March 21 in leap years)
    saka_year = greg_date.year - SAKA_EPOCH_OFFSET

    # Check if current Gregorian year is a leap year
    is_greg_leap = (greg_date.year % 4 == 0 and greg_date.year % 100 != 0) or (greg_date.year % 400 == 0)

    # Chaitra 1 start date for the current Gregorian year
    chaitra_1_greg = datetime.date(greg_date.year, 3, 21 if is_greg_leap else 22)

    if greg_date < chaitra_1_greg:
        # If date is before Chaitra 1, Saka year is previous year
        saka_year -= 1
        # Compute with previous Gregorian year to find correct Saka month/day
        prev_greg_year_is_leap = ( (greg_date.year - 1) % 4 == 0 and (greg_date.year - 1) % 100 != 0) or ( (greg_date.year - 1) % 400 == 0)
        chaitra_1_prev_greg = datetime.date(greg_date.year - 1, 3, 21 if prev_greg_year_is_leap else 22)
        days_since_chaitra = (greg_date - chaitra_1_prev_greg).days
    else:
        days_since_chaitra = (greg_date - chaitra_1_greg).days

    # Saka months (Chaitra is month 0 in our SAKA_MONTH_NAMES list)
    # First month Chaitra has 30 days in normal year, 31 in leap year
    # Other months have 31 days (Vaisakha to Bhadra), then 30 days (Asvina to Phalguna)
    saka_month_lengths = {
        0: 30 + (1 if is_greg_leap else 0), # Chaitra
        1: 31, # Vaisakha
        2: 31, # Jyaistha
        3: 31, # Asadha
        4: 31, # Sravana
        5: 31, # Bhadra
        6: 30, # Asvina
        7: 30, # Kartika
        8: 30, # Agrahayana
        9: 30, # Pausa
        10: 30, # Magha
        11: 30 # Phalguna
    }

    saka_month = 0
    saka_day = 0

    # Iterate through months to find current Saka month and day
    for i in range(12):
        month_len = saka_month_lengths[i]
        if days_since_chaitra < month_len:
            saka_month = i
            saka_day = days_since_chaitra + 1 # Days are 1-indexed
            break
        days_since_chaitra -= month_len

    return saka_year, SAKA_MONTH_NAMES[saka_month], saka_day

def get_lunar_month_names(greg_date, tithi_no):
    """
    Calculate lunar month names based on Sun's position in the zodiac (sidereal).
    This is the proper astronomical way to determine lunar months.
    """
    # Calculate Sun's longitude at the given date
    from datetime import datetime
    import pytz

    # Get sun's position at noon on the given date
    tz = pytz.timezone(LOCATION["tz"])
    local_midnight = tz.localize(datetime(greg_date.year, greg_date.month, greg_date.day, 12, 0, 0))
    jd_ref = dt_to_jd_utc(local_midnight.astimezone(pytz.utc).replace(tzinfo=None))

    sun_data = swe.calc_ut(jd_ref, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    sun_lon = sun_data[0][0]  # Sun's ecliptic longitude in degrees

    # Lunar months based on Sun's position (sidereal zodiac)
    # Each lunar month corresponds to 30° of Sun's travel
    month_index = int(sun_lon // 30) % 12

    # Lunar month names (Amanta system - starts with Chaitra at 0°)
    lunar_months = [
        "Chaitra",     # 0° - 30° (Aries)
        "Vaisakha",    # 30° - 60° (Taurus)
        "Jyaistha",    # 60° - 90° (Gemini)
        "Asadha",      # 90° - 120° (Cancer)
        "Sravana",     # 120° - 150° (Leo)
        "Bhadra",      # 150° - 180° (Virgo)
        "Asvina",      # 180° - 210° (Libra)
        "Kartika",     # 210° - 240° (Scorpio)
        "Agrahayana",  # 240° - 270° (Sagittarius)
        "Pausa",       # 270° - 300° (Capricorn) - Also called Pushya
        "Magha",       # 300° - 330° (Aquarius)
        "Phalguna"     # 330° - 360° (Pisces)
    ]

    amanta_name = lunar_months[month_index]

    # Purnimanta system is offset by 1 month from Amanta
    purnimanta_month_idx = (month_index + 1) % 12
    purnimanta_name = lunar_months[purnimanta_month_idx]

    return amanta_name, purnimanta_name

def sun_moon_longitudes_jd(jd_ut):
    """Calculates Sun and Moon ecliptic longitudes at a given Julian Day (UT)."""
    # Use swe.FLG_SIDEREAL to indicate that sidereal mode is already set globally
    sun_res = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    moon_res = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    return sun_res, moon_res

def tithi_from_longitudes(sun_lon, moon_lon):
    diff = normalize_angle(moon_lon - sun_lon)
    t_no = int(diff // 12) + 1
    frac = (diff % 12) / 12.0
    return t_no, frac, diff

def nakshatra_from_longitude(moon_lon):
    size = 360.0 / 27.0
    idx = int(math.floor(moon_lon / size)) % 27
    within = (moon_lon - (idx * size)) / size
    return idx + 1, NAKSHATRA_NAMES[idx], within

def karana_from_tithi(tithi_no, tithi_frac):
    # Each tithi has two karanas (half-tithis).
    # There are 11 karanas; 7 'fixed' (repeating) and 4 'non-repeating'
    # The order is: Bava, Balava, Kaulava, Taitila, Garaja, Vanija, Vishti (repeating 8 times)
    # Then Shakuni, Chatushpada, Naga, Kimstughna (non-repeating for 14th/30th tithi halves)

    # Tithi number is 1-30. We need to convert it to 0-29 for array indexing if needed.
    # Tithi halves: First half of Tithi N is 2*N-2, second half is 2*N-1 (0-indexed)

    tithi_half_idx = int(tithi_no * 2 - 2 + (1 if tithi_frac >= 0.5 else 0)) # 0 to 59

    # Fixed karanas repeat 8 times for tithis 1-29. (total 56 halves)
    if tithi_half_idx < 56:
        karan_idx = tithi_half_idx % 7 # 0-6 for Bava to Vishti
    else:
        # Non-repeating karanas for the last few tithi halves (tithi 29 second half, tithi 30 first/second half)
        # Kimstughna (0) for 1st half of tithi 1
        # Shakuni (7) for 1st half of tithi 14
        # Chatushpada (8) for 2nd half of tithi 14
        # Naga (9) for 1st half of tithi 15
        # Kimstughna is special; it's the first half of the first tithi (Shukla Pratipada)
        # Simplified for direct mapping
        if tithi_no == 1 and tithi_frac < 0.5: # Shukla Pratipada 1st half
            karan_idx = 10 # Kimstughna
        elif tithi_no == 14 and tithi_frac < 0.5: # Krishna Chaturdashi 1st half
            karan_idx = 7 # Shakuni
        elif tithi_no == 14 and tithi_frac >= 0.5: # Krishna Chaturdashi 2nd half
            karan_idx = 8 # Chatushpada
        elif tithi_no == 15 and tithi_frac < 0.5: # Amavasya 1st half
            karan_idx = 9 # Naga
        elif tithi_no == 30 and tithi_frac < 0.5: # Amavasya 1st half (Amanta system, t_no 30 is Amavasya)
            karan_idx = 9 # Naga
        elif tithi_no == 30 and tithi_frac >= 0.5: # Amavasya 2nd half (Amanta system)
            karan_idx = 10 # Kimstughna
        else:
            # This else should ideally not be hit with a robust tithi_half_idx mapping
            karan_idx = 0 # Default to Bava or handle error

    return karan_idx + 1, KARANA_NAMES[karan_idx], tithi_frac # Return frac for 'within'

def yoga_from_longitudes(sun_lon, moon_lon):
    # Yoga is based on the sum of the longitudes of the Sun and Moon
    # Sum: (Sun_lon + Moon_lon) % 360
    # Each Yoga spans 13°20' (800 minutes) or 360/27 degrees.

    sum_lon = normalize_angle(sun_lon + moon_lon)
    yoga_size = 360.0 / 27.0
    idx = int(math.floor(sum_lon / yoga_size)) % 27
    within = (sum_lon - (idx * yoga_size)) / yoga_size
    return idx + 1, YOGA_NAMES[idx], within

def _find_next_crossing_time(jd_start, func_angle_deg, target_deg, search_hours=48, tol_seconds=10):
    jd_end = jd_start + (search_hours / 24.0)
    def wrap180(x): return (x + 180) % 360 - 180
    f_start = wrap180(func_angle_deg(jd_start) - target_deg)
    f_end = wrap180(func_angle_deg(jd_end) - target_deg)
    if f_start * f_end > 0:
        samples = 24
        prev_jd, prev_f = jd_start, f_start
        found = None
        for k in range(1, samples+1):
            candidate_jd = jd_start + (k * (jd_end - jd_start) / samples)
            f_c = wrap180(func_angle_deg(candidate_jd) - target_deg)
            if prev_f * f_c < 0:
                found = (prev_jd, candidate_jd)
                break
            prev_jd, prev_f = candidate_jd, f_c
        if not found: return None
        a, b = found
    else:
        a, b = jd_start, jd_end
    while True:
        m = (a + b) / 2.0
        f_a = wrap180(func_angle_deg(a) - target_deg)
        f_m = wrap180(func_angle_deg(m) - target_deg)
        if f_a * f_m <= 0: b = m
        else: a = m
        if abs(b - a) * 24 * 3600 <= tol_seconds:
            return (a + b) / 2.0

# Helper to convert Julian Day to local datetime
def jd_to_local_datetime(jd_ut, tz):
    y, m, d, h = swe.revjul(jd_ut)
    # swe.revjul returns hour as a float (e.g., 14.5 for 2:30 PM)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour) * 60 - minute) * 60)
    dt_utc = datetime.datetime(y, m, int(d), hour, minute, second, tzinfo=pytz.utc)
    return dt_utc.astimezone(tz)

def find_all_crossings(jd_start, func_angle_deg, segment_size, search_window_days=1, tol_seconds=5):
    crossings = []
    jd_current = jd_start
    jd_end_search = jd_start + search_window_days # Search for N days

    # Get initial angle and the current multiple
    initial_angle = func_angle_deg(jd_current)
    current_multiple_idx = int(initial_angle // segment_size)

    # Iterate to find subsequent crossings
    while jd_current < jd_end_search:
        # Target the next multiple of the segment size
        target_deg = (current_multiple_idx + 1) * segment_size
        target_deg = normalize_angle(target_deg) # Ensure it's within 0-360

        # Search for the crossing time within a reasonable window (e.g., 2 days from current JD)
        jd_crossing = _find_next_crossing_time(jd_current, func_angle_deg, target_deg, search_hours=48, tol_seconds=tol_seconds)

        if jd_crossing and jd_crossing < jd_end_search:
            crossings.append(jd_crossing)
            jd_current = jd_crossing + (tol_seconds / (24 * 3600.0)) # Move slightly past the crossing
            current_multiple_idx = int(func_angle_deg(jd_current) // segment_size)
        elif jd_crossing and jd_crossing >= jd_end_search:
            # Crossing found but falls outside the search window
            break
        else:
            # No more crossings found within the search window or something went wrong
            break

    return crossings

def create_event_intervals(jds_transitions, jd_start_window, tz, angle_calc_func, name_list, tol_seconds, initial_t_or_nak_calc_func=None, segment_size=None, kind=None, initial_event_name=None, initial_event_ordinal=None):
    events = []
    # Ensure the start of the window is the first point if it's not already covered
    processed_jds = sorted(list(set(jds_transitions + [jd_start_window])))

    # Filter JDs to only include those that are within or just after the start of the window
    # and within a reasonable range (e.g., up to ~2 days after start_window for full transitions)
    filtered_jds = [jd for jd in processed_jds if jd >= jd_start_window - (2/24.0) and jd < jd_start_window + 2.0 ] # A bit more than 1 day

    # Ensure filtered_jds is sorted and unique again
    filtered_jds = sorted(list(set(filtered_jds)))

    # Ensure we have at least one transition for the day, even if it's just the start of the day
    if not filtered_jds or filtered_jds[0] > jd_start_window + (1/24.0): # If first transition is much later
        filtered_jds.insert(0, jd_start_window)
    # Ensure the end of the day is also considered for the last event's end time
    if filtered_jds[-1] < jd_start_window + 1.0 - (tol_seconds / (24 * 3600.0)): # If last transition is before end of day
        filtered_jds.append(jd_start_window + 1.0)

    # Determine the name and ordinal for the event active at jd_start_window
    initial_jd_point = jd_start_window # Or slightly after if jd_start_window is exactly a transition point

    # If initial_event_name and ordinal are provided, use them directly for the very first segment.
    if initial_event_name is not None and initial_event_ordinal is not None:
        initial_name = initial_event_name
        initial_ordinal = initial_event_ordinal
    else:
        initial_name = "Unknown"
        initial_ordinal = -1

        if kind == 'tithi':
            sun_lon_initial, moon_lon_initial = angle_calc_func(initial_jd_point)
            t_no_val, _, _ = tithi_from_longitudes(sun_lon_initial, moon_lon_initial)
            initial_ordinal = t_no_val
            initial_name = name_list[initial_ordinal-1]
        elif kind == 'nakshatra':
            moon_lon_initial = angle_calc_func(initial_jd_point)
            nak_idx_val, nak_name_val, _ = nakshatra_from_longitude(moon_lon_initial)
            initial_ordinal = nak_idx_val
            initial_name = nak_name_val
        elif kind == 'karana':
            sun_lon_initial, moon_lon_initial = angle_calc_func(initial_jd_point)
            t_no_initial, t_frac_initial, _ = tithi_from_longitudes(sun_lon_initial, moon_lon_initial)
            kar_idx_val, kar_name_val, _ = karana_from_tithi(t_no_initial, t_frac_initial)
            initial_ordinal = kar_idx_val
            initial_name = kar_name_val
        elif kind == 'yoga':
            sun_lon_initial, moon_lon_initial = angle_calc_func(initial_jd_point)
            yog_idx_val, yog_name_val, _ = yoga_from_longitudes(sun_lon_initial, moon_lon_initial)
            initial_ordinal = yog_idx_val
            initial_name = yog_name_val

    # Define the boundaries of the target date for clipping events
    target_date_start = jd_to_local_datetime(jd_start_window, tz) # Local midnight of the target date
    target_date_end = jd_to_local_datetime(jd_start_window + 1.0, tz) # Local midnight of the next day

    # The actual list of intervals we will process
    final_intervals = []

    # Add the initial event starting from target_date_start if it's not already the first transition
    if filtered_jds[0] > jd_start_window + (tol_seconds / (24 * 3600.0)): # If the first transition is after midnight
        final_intervals.append({
            "start_jd": jd_start_window,
            "end_jd": filtered_jds[0],
            "name": initial_name,
            "ordinal": initial_ordinal
        })

    # Now process the rest of the transitions
    for i in range(len(filtered_jds) - 1):
        jd_current_start = filtered_jds[i]
        jd_current_end = filtered_jds[i+1]

        # Use the midpoint of the interval to determine the active Tithi/Nakshatra/Yoga/Karana
        jd_midpoint = (jd_current_start + jd_current_end) / 2.0

        name = "Unknown"
        ordinal = -1
        if kind == 'tithi':
            # For tithi, calculate at midpoint using sun_moon_longitudes_jd from angle_calc_func
            sun_lon_mid, moon_lon_mid = angle_calc_func(jd_midpoint)
            t_no, _, _ = tithi_from_longitudes(sun_lon_mid, moon_lon_mid)
            name = name_list[t_no-1]
            ordinal = t_no
        elif kind == 'nakshatra':
            moon_lon_mid = angle_calc_func(jd_midpoint)
            nak_idx, nak_name, _ = nakshatra_from_longitude(moon_lon_mid)
            name = nak_name
            ordinal = nak_idx
        elif kind == 'karana':
            # Karana needs tithi_no for its calculation. Recompute tithi at midpoint.
            sun_lon_mid, moon_lon_mid = angle_calc_func(jd_midpoint)
            t_no_mid, t_frac_mid, _ = tithi_from_longitudes(sun_lon_mid, moon_lon_mid)
            kar_idx, kar_name, _ = karana_from_tithi(t_no_mid, t_frac_mid)
            name = kar_name
            ordinal = kar_idx
        elif kind == 'yoga':
            # For yoga, calculate at midpoint using sun_moon_longitudes_jd from angle_calc_func
            sun_lon_mid, moon_lon_mid = angle_calc_func(jd_midpoint)
            yog_idx, yog_name, _ = yoga_from_longitudes(sun_lon_mid, moon_lon_mid)
            name = yog_name
            ordinal = yog_idx
        else:
            # Fallback for other types, or error
            pass

        final_intervals.append({
            "start_jd": jd_current_start,
            "end_jd": jd_current_end,
            "name": name,
            "ordinal": ordinal
        })

    # Process final_intervals to create display events
    for interval in final_intervals:
        start_dt = jd_to_local_datetime(interval["start_jd"], tz)
        end_dt = jd_to_local_datetime(interval["end_jd"], tz)

        # Clip events to the target date boundaries
        target_date_start_dt = jd_to_local_datetime(jd_start_window, tz)
        target_date_end_dt = jd_to_local_datetime(jd_start_window + 1.0, tz)

        event_start_dt = max(start_dt, target_date_start_dt)
        event_end_dt = min(end_dt, target_date_end_dt)

        if kind == 'nakshatra':
            pass # Removed debug print

        # Only include event if it falls within the target day (even if clipped)
        if event_start_dt < event_end_dt:
            events.append({
                "name": interval['name'],
                "ordinal": interval['ordinal'],
                "start": fmt_local(event_start_dt, with_date=True),
                "end": fmt_local(event_end_dt, with_date=True)
            })

    return events

# Helper to format datetime to local time string, with optional date
def fmt_local(dt, with_date=False):
    if dt is None: return "N/A"
    if with_date:
        return dt.strftime("%b %d %I:%M %p") # e.g., Nov 06 06:37 AM
    return dt.strftime("%I:%M %p")

# ------------------ Hora Calculations (12 horas) ------------------
def calculate_horas(date, location):
    """
    Calculate 12 day horas and 12 night horas for a given date and location.

    Notes:
    - Planet order follows traditional sequence: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars
    - Starting planet is determined by the day lord (weekday)
    - Day horas: sunrise to sunset (divided into 12 equal parts)
    - Night horas: sunset to next sunrise (divided into 12 equal parts)
    - Timing differences between calculations are expected when sunrise/sunset times differ
      (planet order remains the same, only interval times change)

    Returns lists of hora strings in format: "Planet: HH:MM AM/PM - HH:MM AM/PM"
    """
    tz = pytz.timezone(location["tz"])
    locinfo = LocationInfo(location["name"], location["region"], location["tz"],
                           location["lat"], location["lon"])
    s = sun(locinfo.observer, date=date, tzinfo=tz)
    sunrise, sunset = s["sunrise"], s["sunset"]

    # Get next day sunrise for night duration calculation
    # Note: Using actual next sunrise is more accurate than assuming exactly 24 hours
    next_day = date + datetime.timedelta(days=1)
    s_next = sun(locinfo.observer, date=next_day, tzinfo=tz)
    next_sunrise = s_next["sunrise"]

    # Planetary sequence (Sun to Mars) - traditional hora order
    # This sequence repeats every 7 horas: Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars
    planets = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

    # Day lord order (based on weekday)
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = date.weekday()  # Monday=0, Sunday=6
    day_name = weekday_names[weekday]

    day_lords = {
        "Sunday": "Sun",
        "Monday": "Moon",
        "Tuesday": "Mars",
        "Wednesday": "Mercury",
        "Thursday": "Jupiter",
        "Friday": "Venus",
        "Saturday": "Saturn"
    }

    # Find starting planet index for this weekday
    start_index = planets.index(day_lords[day_name])

    # Calculate day and night durations
    day_duration = (sunset - sunrise).total_seconds()
    # Use actual next sunrise (more accurate than assuming 24-hour day)
    night_duration = (next_sunrise - sunset).total_seconds()

    # Hora durations (12 horas each)
    day_hora_duration = day_duration / 12
    night_hora_duration = night_duration / 12

    day_horas = []
    night_horas = []

    # Helper to format time
    def fmt_time(dt): return dt.strftime("%I:%M %p")

    # --- Day Horas (12 horas) ---
    current_time = sunrise
    for i in range(12):
        planet = planets[(start_index + i) % 7]
        next_time = current_time + datetime.timedelta(seconds=day_hora_duration)
        day_horas.append(f"{planet}: {fmt_time(current_time)} - {fmt_time(next_time)}")
        current_time = next_time

    # --- Night Horas (12 horas) ---
    current_time = sunset
    for i in range(12):
        planet = planets[(start_index + 12 + i) % 7]
        next_time = current_time + datetime.timedelta(seconds=night_hora_duration)
        night_horas.append(f"{planet}: {fmt_time(current_time)} - {fmt_time(next_time)}")
        current_time = next_time

    return day_horas, night_horas

# ------------------ Auspicious Timings ------------------
def compute_auspicious_timings(date, location):
    """
    Calculate all auspicious timings (muhurats) for a given date and location.
    Returns a dictionary with timing strings.
    """
    tz = pytz.timezone(location["tz"])
    locinfo = LocationInfo(location["name"], location["region"], location["tz"],
                           location["lat"], location["lon"])
    s = sun(locinfo.observer, date=date, tzinfo=tz)
    sunrise, sunset = s["sunrise"], s["sunset"]

    # Get next day sunrise for nighttime calculations
    next_day = date + datetime.timedelta(days=1)
    s_next = sun(locinfo.observer, date=next_day, tzinfo=tz)
    next_sunrise = s_next["sunrise"]

    # Helper to format time
    def fmt(dt): return dt.strftime("%I:%M %p")

    # Brahma Muhurta (1h36m to 48m before sunrise)
    brahma_start = sunrise - datetime.timedelta(hours=1, minutes=36)
    brahma_end = sunrise - datetime.timedelta(minutes=48)

    # Pratah Sandhya (~15m before sunrise to 1h after)
    pratah_start = sunrise - datetime.timedelta(minutes=15)
    pratah_end = sunrise + datetime.timedelta(hours=1)

    # Midday (Abhijit Muhurat ±24m)
    midday = sunrise + (sunset - sunrise) / 2
    abhijit_start = midday - datetime.timedelta(minutes=24)
    abhijit_end = midday + datetime.timedelta(minutes=24)

    # Vijaya Muhurat (≈2h24m before sunset, lasting 48m)
    vijaya_start = sunset - datetime.timedelta(hours=2, minutes=24)
    vijaya_end = vijaya_start + datetime.timedelta(minutes=48)

    # Godhuli Muhurat (≈15m before to 15m after sunset)
    godhuli_start = sunset - datetime.timedelta(minutes=15)
    godhuli_end = sunset + datetime.timedelta(minutes=15)

    # Sayahna Sandhya (sunset to +75m)
    sayahna_start = sunset
    sayahna_end = sunset + datetime.timedelta(minutes=75)

    # Midnight-based
    night_midpoint = sunset + (next_sunrise - sunset) / 2
    nishita_start = night_midpoint - datetime.timedelta(minutes=24)
    nishita_end = night_midpoint + datetime.timedelta(minutes=24)

    # Amrit Kalam (example approximation)
    amrit_start = sunset + datetime.timedelta(hours=3, minutes=45)
    amrit_end = amrit_start + datetime.timedelta(hours=1, minutes=25)

    return {
        "Brahma Muhurta": f"{fmt(brahma_start)} - {fmt(brahma_end)}",
        "Pratah Sandhya": f"{fmt(pratah_start)} - {fmt(pratah_end)}",
        "Abhijit": f"{fmt(abhijit_start)} - {fmt(abhijit_end)}",
        "Vijaya Muhurta": f"{fmt(vijaya_start)} - {fmt(vijaya_end)}",
        "Godhuli Muhurta": f"{fmt(godhuli_start)} - {fmt(godhuli_end)}",
        "Sayahna Sandhya": f"{fmt(sayahna_start)} - {fmt(sayahna_end)}",
        "Amrit Kalam": f"{fmt(amrit_start)} - {fmt(amrit_end)}",
        "Nishita Muhurta": f"{fmt(nishita_start)} - {fmt(nishita_end)}"
    }

# ------------------ Festival Detection ------------------
# Festival detection logic removed - festivals are now fetched from database via API

# ------------------ Core Computation ------------------
def compute_panchang_for_date(
    date_str,
    location=LOCATION,
    search_window_hours=48,
    profile_code: str = "en",
    format_profile: bool = False,
    include_raw: bool = False,
):
    tz = pytz.timezone(location["tz"])
    date_local = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    local_midnight = tz.localize(datetime.datetime(date_local.year, date_local.month, date_local.day, 0, 0, 0))
    locinfo = LocationInfo(location["name"], location["region"], location["tz"], location["lat"], location["lon"])
    s = sun(locinfo.observer, date=date_local, tzinfo=tz)
    sunrise, sunset = s["sunrise"], s["sunset"]

    # Calculate Moonrise and Moonset
    # Handle cases where moon doesn't rise/set on a particular date
    try:
        mr = moonrise(locinfo.observer, date=date_local, tzinfo=tz)
        moonrise_time = mr if isinstance(mr, datetime.datetime) else None
    except (ValueError, Exception) as e:
        # Moon doesn't rise on this date (can happen at certain locations/dates)
        moonrise_time = None

    try:
        ms = moonset(locinfo.observer, date=date_local, tzinfo=tz)
        moonset_time = ms if isinstance(ms, datetime.datetime) else None
    except (ValueError, Exception) as e:
        # Moon doesn't set on this date (can happen at certain locations/dates)
        moonset_time = None

    ref_utc = local_midnight.astimezone(pytz.utc).replace(tzinfo=None)
    jd_ref = dt_to_jd_utc(ref_utc)

    jd_start_search_window = jd_ref - 1.0 # 24 hours before local midnight of target date
    # The total search window should cover 2 days from jd_start_search_window
    total_search_days = 2.0

    # --- Tithi Calculations ---
    # Initial Tithi at local midnight
    sun_lon_at_midnight, moon_lon_at_midnight = sun_moon_longitudes_jd(jd_ref)
    initial_t_no, initial_t_frac, initial_diff_deg = tithi_from_longitudes(sun_lon_at_midnight, moon_lon_at_midnight)
    paksha_name = PAKSHA_NAMES[0] if initial_t_no <= 15 else PAKSHA_NAMES[1]

    tithi_segment_size = 12.0 # degrees
    def tithi_func_angle(jd): return normalize_angle(sun_moon_longitudes_jd(jd)[1] - sun_moon_longitudes_jd(jd)[0])

    # Determine initial tithi at the *very start* of our extended search window (jd_start_search_window)
    sun_lon_extended_start, moon_lon_extended_start = sun_moon_longitudes_jd(jd_start_search_window - (1/24.0)) # A bit before for safety
    initial_t_no_extended, _, _ = tithi_from_longitudes(sun_lon_extended_start, moon_lon_extended_start)
    initial_t_name_extended = TITHI_NAMES[initial_t_no_extended-1]

    # Find all Tithi crossings for the day (start from jd_start_search_window)
    all_tithi_jds = find_all_crossings(jd_start_search_window, tithi_func_angle, tithi_segment_size, search_window_days=total_search_days, tol_seconds=5)
    # Ensure we include jd_start_search_window itself as a start point for the first segment
    if not all_tithi_jds or all_tithi_jds[0] > jd_start_search_window:
        all_tithi_jds.insert(0, jd_start_search_window)

    tithi_events = create_event_intervals(
        all_tithi_jds,
        jd_ref, # Pass jd_ref as the target day's midnight for event interval clipping
        tz,
        sun_moon_longitudes_jd, # This function returns (sun_lon, moon_lon) tuples
        TITHI_NAMES,
        tol_seconds=5,
        kind='tithi',
        segment_size=tithi_segment_size,
        initial_event_name=initial_t_name_extended, # Pass the initial event name
        initial_event_ordinal=initial_t_no_extended # Pass the initial event ordinal
    )

    # --- Nakshatra Calculations ---
    # Initial Nakshatra at local midnight
    initial_nak_idx, initial_nak_name, initial_nak_frac = nakshatra_from_longitude(moon_lon_at_midnight)

    nakshatra_segment_size = 360.0 / 27.0 # degrees
    def nakshatra_func_angle(jd): return sun_moon_longitudes_jd(jd)[1]

    # Determine initial nakshatra at the *very start* of our extended search window (jd_start_search_window)
    moon_lon_extended_start = sun_moon_longitudes_jd(jd_start_search_window - (1/24.0))[1] # A bit before for safety
    initial_nak_idx_extended, initial_nak_name_extended, _ = nakshatra_from_longitude(moon_lon_extended_start)

    # Find all Nakshatra crossings for the day
    all_nak_jds = find_all_crossings(jd_start_search_window, nakshatra_func_angle, nakshatra_segment_size, search_window_days=total_search_days, tol_seconds=5)
    # Ensure we include jd_start_search_window itself as a start point for the first segment
    if not all_nak_jds or all_nak_jds[0] > jd_start_search_window:
        all_nak_jds.insert(0, jd_start_search_window)

    nakshatra_events = create_event_intervals(
        all_nak_jds,
        jd_ref,
        tz,
        nakshatra_func_angle, # This function returns moon_lon
        NAKSHATRA_NAMES,
        tol_seconds=5,
        kind='nakshatra',
        segment_size=nakshatra_segment_size,
        initial_event_name=initial_nak_name_extended, # Pass the initial event name
        initial_event_ordinal=initial_nak_idx_extended # Pass the initial event ordinal
    )

    # --- Karana Calculations ---
    # Initial Karana at local midnight
    initial_kar_idx, initial_kar_name, initial_kar_frac = karana_from_tithi(initial_t_no, initial_t_frac)

    karana_segment_size = 6.0 # degrees (half of a tithi)
    def karana_func_angle(jd): return normalize_angle(sun_moon_longitudes_jd(jd)[1] - sun_moon_longitudes_jd(jd)[0])

    # Determine initial karana at the *very start* of our extended search window (jd_start_search_window)
    sun_lon_extended_start_kar, moon_lon_extended_start_kar = sun_moon_longitudes_jd(jd_start_search_window - (1/24.0))
    t_no_extended_kar, t_frac_extended_kar, _ = tithi_from_longitudes(sun_lon_extended_start_kar, moon_lon_extended_start_kar)
    initial_kar_idx_extended, initial_kar_name_extended, _ = karana_from_tithi(t_no_extended_kar, t_frac_extended_kar)

    all_kar_jds = find_all_crossings(jd_start_search_window, karana_func_angle, karana_segment_size, search_window_days=total_search_days, tol_seconds=5)
    if not all_kar_jds or all_kar_jds[0] > jd_start_search_window:
        all_kar_jds.insert(0, jd_start_search_window)

    karana_events = create_event_intervals(
        all_kar_jds,
        jd_ref,
        tz,
        sun_moon_longitudes_jd, # This needs (sun_lon, moon_lon) for tithi_from_longitudes
        KARANA_NAMES,
        tol_seconds=5,
        kind='karana',
        segment_size=karana_segment_size,
        initial_event_name=initial_kar_name_extended,
        initial_event_ordinal=initial_kar_idx_extended
    )

    # --- Yoga Calculations ---
    # Initial Yoga at local midnight
    initial_yog_idx, initial_yog_name, initial_yog_frac = yoga_from_longitudes(sun_lon_at_midnight, moon_lon_at_midnight)

    yoga_segment_size = 360.0 / 27.0 # degrees
    def yoga_func_angle(jd): return normalize_angle(sun_moon_longitudes_jd(jd)[0] + sun_moon_longitudes_jd(jd)[1])

    # Determine initial yoga at the *very start* of our extended search window (jd_start_search_window)
    sun_lon_extended_start_yog, moon_lon_extended_start_yog = sun_moon_longitudes_jd(jd_start_search_window - (1/24.0))
    initial_yog_idx_extended, initial_yog_name_extended, _ = yoga_from_longitudes(sun_lon_extended_start_yog, moon_lon_extended_start_yog)

    all_yog_jds = find_all_crossings(jd_start_search_window, yoga_func_angle, yoga_segment_size, search_window_days=total_search_days, tol_seconds=5)
    if not all_yog_jds or all_yog_jds[0] > jd_start_search_window:
        all_yog_jds.insert(0, jd_start_search_window)

    yoga_events = create_event_intervals(
        all_yog_jds,
        jd_ref,
        tz,
        sun_moon_longitudes_jd, # This needs (sun_lon, moon_lon) for yoga_from_longitudes
        YOGA_NAMES,
        tol_seconds=5,
        kind='yoga',
        segment_size=yoga_segment_size,
        initial_event_name=initial_yog_name_extended,
        initial_event_ordinal=initial_yog_idx_extended
    )

    saka_year, saka_month_name, saka_day = convert_gregorian_to_saka(date_local)

    # Amanta and Purnimanta Months
    amanta_month_name, purnimanta_month_name = get_lunar_month_names(date_local, initial_t_no)

    # Traditional Panchang summary line (always in Telugu)
    traditional_summary = get_traditional_panchang_line(date_local, sun_lon_at_midnight, purnimanta_month_name, "te")

    # All auspicious timings
    auspicious_timings_calculated = compute_auspicious_timings(date_local, location)

    # Format auspicious timings for output
    auspicious = {
        "Abhijit Muhurat": {"value": auspicious_timings_calculated["Abhijit"]},
        "Amrit Kaal": {"value": auspicious_timings_calculated["Amrit Kalam"]},
        "Brahma Muhuratham": {"value": auspicious_timings_calculated["Brahma Muhurta"]},
        "Pratah Sandhya": {"value": auspicious_timings_calculated["Pratah Sandhya"]},
        "Vijaya Muhurta": {"value": auspicious_timings_calculated["Vijaya Muhurta"]},
        "Godhuli Muhurta": {"value": auspicious_timings_calculated["Godhuli Muhurta"]},
        "Sayahna Sandhya": {"value": auspicious_timings_calculated["Sayahna Sandhya"]},
        "Nishita Muhurta": {"value": auspicious_timings_calculated["Nishita Muhurta"]},
    }

    # Calculate Horas (12 day horas and 12 night horas)
    day_horas, night_horas = calculate_horas(date_local, location)

    # ---- Inauspicious: Rahu, Yamaganda, Gulika ----
    weekday = date_local.weekday()  # Monday=0, Tuesday=1, ..., Sunday=6
    RAHU_KALAM_SEGMENTS = [2, 7, 5, 6, 4, 3, 8] # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    YAMAGANDAM_SEGMENTS = [5, 3, 2, 1, 7, 6, 4] # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    GULIKA_KALAM_SEGMENTS = [6, 5, 4, 3, 2, 1, 7] # Mon, Tue, Wed, Thu, Fri, Sat, Sun

    def segment_time(index):
        day_duration = sunset - sunrise
        segment = day_duration / 8
        start = sunrise + segment * (index - 1)
        end = start + segment
        return f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"

    inauspicious = {
        "Rahu Kalam": {"value": segment_time(RAHU_KALAM_SEGMENTS[weekday])},
        "Yamagandam": {"value": segment_time(YAMAGANDAM_SEGMENTS[weekday])},
        "Gulika Kalam": {"value": segment_time(GULIKA_KALAM_SEGMENTS[weekday])}
    }

    result = {
        "date": date_str,
        "Indian Civil Calendar": { "year": saka_year, "month": saka_month_name, "day": saka_day },
        "Amanta Month": { "name": amanta_month_name },
        "Purnimanta Month": { "name": purnimanta_month_name },
        "Paksha": { "name": paksha_name },
        "traditional": {
            "summary": traditional_summary
        },
        "sunrise_moonrise": {
            "Sunrise": {"value": sunrise.strftime("%I:%M %p")},
            "Sunset": {"value": sunset.strftime("%I:%M %p")},
            "Moonrise": {"value": moonrise_time.strftime("%I:%M %p") if moonrise_time else "N/A"},
            "Moonset": {"value": moonset_time.strftime("%I:%M %p") if moonset_time else "N/A"}
        },
        "core_panchang": {
            "Tithulu": tithi_events,
            "Nakshatramulu": nakshatra_events,
            "Karana": karana_events,
            "Yoga": yoga_events
        },
        "auspicious_timings": auspicious,
        "inauspicious_timings": inauspicious,
        "horas": {
            "day": day_horas,
            "night": night_horas
        },
        "festivals": []  # Festivals will be fetched from database via API
    }
    if not format_profile and not include_raw and profile_code == "en":
        return result

    localized = format_panchang_for_profile(result, profile_code)

    if include_raw:
        return {
            "raw": result,
            "localized": localized,
        }

    return localized if format_profile or profile_code != "en" else result

# ------------------ Find Amavasya Dates in a Year (Optimized) ------------------
def find_amavasya_dates_in_year(year: int, location: Dict[str, Any] = LOCATION, optimized: bool = True) -> List[Dict[str, Any]]:
    """
    Find all Amavasya (new moon) dates in a given year.

    Performance: Optimized version uses smart search (checks ~48 days instead of 365).
    Direct calculation is ~7-10x faster than generating full panchang for the year.

    Args:
        year: The year to search (e.g., 2025)
        location: Location dictionary with timezone, lat, lon
        optimized: If True, uses smart search around estimated dates (default: True)

    Returns:
        List of dictionaries with date and time information for each Amavasya
    """
    tz = pytz.timezone(location["tz"])
    amavasya_dates = []

    # Pre-define tithi calculation function (avoid recreating lambda)
    def tithi_func_angle(jd):
        return normalize_angle(sun_moon_longitudes_jd(jd)[1] - sun_moon_longitudes_jd(jd)[0])

    if optimized:
        # OPTIMIZED: Smart search strategy
        # Amavasya occurs approximately every 29.5 days (lunar month)
        # We estimate dates and search in a 4-day window around each estimate
        # This reduces calculations from 365 to ~48 (12 months * 4 days)

        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)

        # Get first Amavasya estimate (start from Jan 1, check first few days)
        first_midnight = tz.localize(datetime.datetime(year, 1, 1, 0, 0, 0))
        first_jd = dt_to_jd_utc(first_midnight.astimezone(pytz.utc).replace(tzinfo=None))
        sun_lon, moon_lon = sun_moon_longitudes_jd(first_jd)
        first_tithi, _, _ = tithi_from_longitudes(sun_lon, moon_lon)

        # Find first Amavasya by searching forward from Jan 1
        search_date = start_date
        days_searched = 0
        max_search = 35  # Max days to find first Amavasya

        while days_searched < max_search and search_date <= end_date:
            local_midnight = tz.localize(datetime.datetime(search_date.year, search_date.month, search_date.day, 0, 0, 0))
            jd_ref = dt_to_jd_utc(local_midnight.astimezone(pytz.utc).replace(tzinfo=None))
            sun_lon, moon_lon = sun_moon_longitudes_jd(jd_ref)
            tithi_no, _, _ = tithi_from_longitudes(sun_lon, moon_lon)

            # Check if Amavasya occurs on this day
            amavasya_time = _check_amavasya_on_date(search_date, jd_ref, tithi_no, tz, tithi_func_angle)
            if amavasya_time:
                amavasya_dates.append({
                    "date": search_date.strftime("%Y-%m-%d"),
                    "time": amavasya_time.strftime("%I:%M %p"),
                    "datetime": amavasya_time.isoformat(),
                })
                break  # Found first Amavasya

            search_date += datetime.timedelta(days=1)
            days_searched += 1

        if not amavasya_dates:
            return []  # No Amavasya found (shouldn't happen)

        # Now search for remaining Amavasya dates using estimated intervals
        # Lunar month = ~29.5 days, search in 4-day window around estimate
        last_amavasya_date = datetime.datetime.strptime(amavasya_dates[0]["date"], "%Y-%m-%d").date()
        lunar_month_days = 29.5
        search_window = 4  # days to search around estimate

        while True:
            # Estimate next Amavasya (add ~29.5 days)
            estimated_date = last_amavasya_date + datetime.timedelta(days=int(lunar_month_days))

            if estimated_date > end_date:
                break

            # Search in window around estimate
            window_start = estimated_date - datetime.timedelta(days=search_window // 2)
            window_end = estimated_date + datetime.timedelta(days=search_window // 2)

            if window_start < start_date:
                window_start = start_date
            if window_end > end_date:
                window_end = end_date

            search_date = window_start
            found_in_window = False

            while search_date <= window_end:
                local_midnight = tz.localize(datetime.datetime(search_date.year, search_date.month, search_date.day, 0, 0, 0))
                jd_ref = dt_to_jd_utc(local_midnight.astimezone(pytz.utc).replace(tzinfo=None))
                sun_lon, moon_lon = sun_moon_longitudes_jd(jd_ref)
                tithi_no, _, _ = tithi_from_longitudes(sun_lon, moon_lon)

                amavasya_time = _check_amavasya_on_date(search_date, jd_ref, tithi_no, tz, tithi_func_angle)
                if amavasya_time:
                    amavasya_dates.append({
                        "date": search_date.strftime("%Y-%m-%d"),
                        "time": amavasya_time.strftime("%I:%M %p"),
                        "datetime": amavasya_time.isoformat(),
                    })
                    last_amavasya_date = search_date
                    found_in_window = True
                    break

                search_date += datetime.timedelta(days=1)

            if not found_in_window:
                # Expand search if not found in window
                search_date = window_start - datetime.timedelta(days=2)
                while search_date <= window_end + datetime.timedelta(days=2):
                    if search_date < start_date or search_date > end_date:
                        search_date += datetime.timedelta(days=1)
                        continue

                    local_midnight = tz.localize(datetime.datetime(search_date.year, search_date.month, search_date.day, 0, 0, 0))
                    jd_ref = dt_to_jd_utc(local_midnight.astimezone(pytz.utc).replace(tzinfo=None))
                    sun_lon, moon_lon = sun_moon_longitudes_jd(jd_ref)
                    tithi_no, _, _ = tithi_from_longitudes(sun_lon, moon_lon)

                    amavasya_time = _check_amavasya_on_date(search_date, jd_ref, tithi_no, tz, tithi_func_angle)
                    if amavasya_time:
                        amavasya_dates.append({
                            "date": search_date.strftime("%Y-%m-%d"),
                            "time": amavasya_time.strftime("%I:%M %p"),
                            "datetime": amavasya_time.isoformat(),
                        })
                        last_amavasya_date = search_date
                        break

                    search_date += datetime.timedelta(days=1)
    else:
        # UNOPTIMIZED: Check every day (slower but more thorough)
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
        current_date = start_date

        while current_date <= end_date:
            local_midnight = tz.localize(datetime.datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0))
            jd_ref = dt_to_jd_utc(local_midnight.astimezone(pytz.utc).replace(tzinfo=None))
            sun_lon, moon_lon = sun_moon_longitudes_jd(jd_ref)
            tithi_no, _, _ = tithi_from_longitudes(sun_lon, moon_lon)

            amavasya_time = _check_amavasya_on_date(current_date, jd_ref, tithi_no, tz, tithi_func_angle)
            if amavasya_time:
                amavasya_dates.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": amavasya_time.strftime("%I:%M %p"),
                    "datetime": amavasya_time.isoformat(),
                })

            current_date += datetime.timedelta(days=1)

    # Sort by date to ensure chronological order
    amavasya_dates.sort(key=lambda x: x["date"])
    return amavasya_dates


def _check_amavasya_on_date(date: datetime.date, jd_ref: float, tithi_no: int, tz: pytz.BaseTzInfo, tithi_func_angle) -> Optional[datetime.datetime]:
    """
    Helper function to check if Amavasya occurs on a given date.
    Returns the datetime if found, None otherwise.
    """
    local_midnight = tz.localize(datetime.datetime(date.year, date.month, date.day, 0, 0, 0))
    amavasya_time = None

    if tithi_no == 30:
        # Amavasya is active - find when it started
        jd_start_search = jd_ref - 1.0
        target_deg = 0.0
        transition_jd = _find_next_crossing_time(jd_start_search, tithi_func_angle, target_deg, search_hours=48, tol_seconds=10)

        if transition_jd:
            transition_time = jd_to_local_datetime(transition_jd, tz)
            if transition_time.date() == date:
                amavasya_time = transition_time
            elif transition_time.date() == date - datetime.timedelta(days=1):
                amavasya_time = local_midnight
        else:
            amavasya_time = local_midnight
    elif tithi_no == 29:
        # Check if tithi transitions to 30 (Amavasya) during this day
        target_deg = 0.0
        transition_jd = _find_next_crossing_time(jd_ref, tithi_func_angle, target_deg, search_hours=24, tol_seconds=10)

        if transition_jd:
            transition_time = jd_to_local_datetime(transition_jd, tz)
            if transition_time.date() == date:
                amavasya_time = transition_time

    return amavasya_time

# ------------------ Traditional Panchang Helpers ------------------
def get_samvatsara(greg_year: int) -> str:
    """
    Calculate the Samvatsara (Jovian year) for a given Gregorian year.
    Prabhava year started in 1987-88, cycle repeats every 60 years.
    """
    base_year = 1987  # Prabhava
    index = (greg_year - base_year) % 60
    return SAMVATSARA_NAMES[index]

def get_ayana(sun_lon: float) -> str:
    """
    Determine Ayana (Solstice period) based on Sun's longitude.
    Uttarayana: 0°-180° (Northern solstice)
    Dakshinayana: 180°-360° (Southern solstice)
    """
    return "ఉత్తరాయనం" if sun_lon < 180 else "దక్షిణాయనం"

def get_traditional_panchang_line(date_local, sun_lon: float, amanta_month: str, profile_code: str = "te") -> str:
    """
    Generate the traditional Panchang summary line in Telugu format.
    Format: "శ్రీ [Samvatsara] నామ సంవత్సరం; [Ayana]; [Ritu]; [Masa]"
    """
    from .localization.service import _map_name
    from .localization.profiles import get_profile_assets

    # Get Telugu profile for proper localization
    profile = get_profile_assets(profile_code)

    # Map English month name to Telugu
    telugu_month = _map_name(amanta_month, AMANTA_MONTH_NAMES, profile.amanta_month)

    samvatsara = get_samvatsara(date_local.year)
    ayana = get_ayana(sun_lon)
    ritu = RITU_MAP.get(telugu_month, "")
    masa = f"{telugu_month} మాసం"

    return f"శ్రీ {samvatsara} నామ సంవత్సరం; {ayana}; {ritu}; {masa}"

# ------------------ Run Example ------------------
if __name__ == "__main__":
    import sys

    # Check if user wants to find Amavasya dates
    if len(sys.argv) > 1 and sys.argv[1] == "amavasya":
        year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
        print(f"\nFinding all Amavasya dates for year {year}...\n")
        amavasya_list = find_amavasya_dates_in_year(year, LOCATION)
        print(f"Found {len(amavasya_list)} Amavasya dates in {year}:\n")
        for amavasya in amavasya_list:
            print(f"  {amavasya['date']} at {amavasya['time']}")
        print("\n" + json.dumps(amavasya_list, indent=2, ensure_ascii=False))
    else:
        # Regular Panchang output
        # Change profile_code to switch languages:
        # "en"=English, "te"=Telugu, "hi"=Hindi, "ta"=Tamil, "kn"=Kannada, "bn"=Bengali, "gu"=Gujarati
        localized_output = compute_panchang_for_date(
            DATE_STR,
            LOCATION,
            profile_code="en",  # <-- Change this to your preferred language code
            format_profile=True,
            include_raw=False,
        )
        print(json.dumps(localized_output, indent=2, ensure_ascii=False))
