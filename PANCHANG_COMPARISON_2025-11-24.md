# Panchang Data Comparison: 2025-11-24
## Our API vs Drikpanchang.com

### ✅ **MATCHING VALUES**

| Field | Our API | Drikpanchang | Status |
|-------|---------|---------------|--------|
| **Sunrise** | 06:12 AM | 06:12 AM | ✅ Match |
| **Sunset** | 05:39 PM | 05:39 PM | ✅ Match |
| **Tithi** | Chaturthi upto 09:22 PM, then Panchami | Chaturthi upto 09:22 PM, then Panchami | ✅ Match |
| **Paksha** | Shukla Paksha | Shukla Paksha | ✅ Match |
| **Amanta Month** | Magha | Magha (Margashirsha - Amanta) | ✅ Match |
| **Purnimanta Month** | Magha | Magha (Margashirsha - Purnimanta) | ✅ Match |

---

### ⚠️ **MINOR DIFFERENCES** (1-2 minutes)

| Field | Our API | Drikpanchang | Difference |
|-------|---------|---------------|------------|
| **Moonrise** | 09:29 AM | 09:28 AM | +1 minute |
| **Moonset** | 08:58 PM | 08:59 PM | -1 minute |

**Note:** These minor differences are acceptable and likely due to:
- Different calculation libraries (Astral vs Swiss Ephemeris)
- Location precision differences
- Rounding methods

---

### ❌ **MAJOR DISCREPANCIES**

#### 1. **Nakshatra Timing** ⚠️ CRITICAL
| Our API | Drikpanchang | Difference |
|---------|---------------|------------|
| Purva Ashadha upto **11:38 PM** | Purva Ashadha upto **09:53 PM** | **~1 hour 45 minutes** |
| Uttara Ashadha starts at 11:38 PM | Uttara Ashadha starts at 09:53 PM | |

**Impact:** This is a significant difference that affects festival matching and auspicious timing calculations.

**Possible Causes:**
- Different nakshatra calculation methods
- Different reference points (midnight vs sunrise)
- Different tolerance settings in crossing detection
- Different ephemeris data sources

---

#### 2. **Yoga Timing** ⚠️ CRITICAL
| Our API | Drikpanchang | Difference |
|---------|---------------|------------|
| Shula upto **03:50 PM** | Shula upto **12:37 PM** | **~3 hours 13 minutes** |
| Ganda starts at 03:50 PM | Ganda starts at 12:37 PM | |

**Impact:** Major discrepancy affecting yoga-based calculations and auspicious timings.

**Possible Causes:**
- Different yoga calculation algorithms
- Different sun+moon longitude sum calculations
- Different segment size or rounding methods

---

#### 3. **Karana Sequence** ⚠️ IMPORTANT
| Our API | Drikpanchang |
|---------|---------------|
| Vishti upto 08:26 AM | Vanija upto 08:25 AM |
| Bava upto 09:22 PM | Vishti upto 09:22 PM |
| Balava after 09:22 PM | Bava after 09:22 PM |

**Impact:** Different starting karana affects the entire sequence.

**Possible Causes:**
- Different karana calculation methods
- Different tithi fraction calculations
- Different handling of karana transitions
- Different reference times for initial karana

**Note:** Drikpanchang shows "Vanija" as the first karana, which suggests they might be using a different starting point or calculation method.

---

### 📊 **Auspicious Timings Comparison**

| Timing | Our API | Drikpanchang | Difference |
|--------|---------|---------------|------------|
| **Brahma Muhurta** | 04:36 AM - 05:24 AM | 04:32 AM - 05:22 AM | ~4 minutes earlier |
| **Pratah Sandhya** | 05:57 AM - 07:12 AM | 04:57 AM - 06:12 AM | 1 hour earlier start |
| **Abhijit Muhurat** | 11:31 AM - 12:19 PM | 11:33 AM - 12:18 PM | ~2 minutes difference |
| **Vijaya Muhurta** | 03:15 PM - 04:03 PM | 01:50 PM - 02:36 PM | ~1.5 hours earlier |
| **Godhuli Muhurta** | 05:24 PM - 05:54 PM | 05:37 PM - 06:02 PM | Different times |
| **Sayahna Sandhya** | 05:39 PM - 06:54 PM | 05:39 PM - 06:55 PM | ~1 minute difference |
| **Amrit Kaal** | 09:24 PM - 10:49 PM | 04:36 PM - 06:22 PM | **Completely different** |
| **Nishita Muhurta** | 11:31 PM - 12:19 AM | 11:31 PM - 12:21 AM | ~2 minutes difference |

**Note:** Some auspicious timings show significant differences, especially:
- Pratah Sandhya (1 hour difference)
- Vijaya Muhurta (1.5 hours difference)
- Amrit Kaal (completely different times)

---

### 🔍 **Root Cause Analysis**

The major discrepancies suggest:

1. **Different Calculation Methods:**
   - Our API uses Swiss Ephemeris (swisseph) with Lahiri ayanamsha
   - Drikpanchang may use different ephemeris or calculation methods

2. **Different Reference Points:**
   - Our calculations start from local midnight
   - Drikpanchang might use sunrise or a different reference point

3. **Different Tolerance Settings:**
   - Our `tol_seconds=5` might be too lenient
   - Different tolerance can affect crossing detection

4. **Different Rounding/Precision:**
   - Time formatting and rounding differences
   - Different precision in angle calculations

---

### 🛠️ **Recommendations**

1. **Verify Nakshatra Calculations:**
   - Check if moon longitude calculations match Drikpanchang
   - Verify nakshatra crossing detection algorithm
   - Compare with multiple reference sources

2. **Verify Yoga Calculations:**
   - Check sun+moon longitude sum calculations
   - Verify yoga segment size (should be 360/27 = 13.333... degrees)
   - Compare yoga transition times

3. **Verify Karana Calculations:**
   - Check tithi fraction calculations
   - Verify karana sequence logic
   - Compare initial karana determination

4. **Verify Auspicious Timings:**
   - Check calculation formulas for each muhurat
   - Verify reference points (sunrise/sunset/midnight)
   - Compare with traditional panchang sources

5. **Add Validation:**
   - Cross-reference with multiple panchang sources
   - Add unit tests comparing with known good data
   - Implement validation against Drikpanchang for critical dates

---

### 📝 **Next Steps**

1. Investigate nakshatra calculation timing discrepancy (~1h 45m)
2. Investigate yoga calculation timing discrepancy (~3h 13m)
3. Investigate karana sequence difference
4. Review auspicious timing calculation formulas
5. Consider adding configuration for different calculation methods
6. Add comparison/validation endpoints for testing

---

**Generated:** 2025-11-24
**Comparison Date:** 2025-11-24
**Location:** Chennai, India (13.0827°N, 80.2707°E)








