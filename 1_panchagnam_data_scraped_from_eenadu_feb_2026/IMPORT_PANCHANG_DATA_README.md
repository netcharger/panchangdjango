# Importing Panchang Data

This guide explains how to import Panchang data from the generated JSON files into the `PanchangData` model.

## Prerequisites

- Ensure the JSON files are generated in `e:\DAILYCALENDAR\1_panchang_calculations_v2_2026\panchang_files`.
- The `PanchangData` model should have the necessary fields (Sunrise, Sunset, Moonrise, Moonset, Auspicious Timings, etc.).

## Import from Excel

To import/update basic Panchang data (Tithi, Nakshatra, etc.) from the merged Excel file:

```bash
python manage.py import_excel_panchang_data "e:\DAILYCALENDAR\panchang_api\1_panchagnam_data_scraped_from_eenadu_feb_2026\Merged_Data.xlsx"
```

This command will update existing records (by date) or create new ones, populating fields such as:
- Tithi, Tithi End
- Nakshatra, Nakshatra End
- Paksha, Lunar Month
- Durmuhurtham, Varjyam

## Import from JSON (Detailed Timings)

Use `import_json_panchang` to enrich the data with specific timings (Sunrise, Moonrise, Auspicious/Good Times only).

```bash
python manage.py import_json_panchang "e:\DAILYCALENDAR\1_panchang_calculations_v2_2026\panchang_files"
```

## How it Works

1.  **Iterates through JSON files**: The command looks for all `.json` files in the specified directory.
2.  **Extracts Data**: checks for `date` in the JSON.
3.  **Strict Filtering**: Imports **ONLY** the following fields relative to Sun/Moon and Auspicious timings:
    *   **Sun/Moon**: `sunrise`, `sunset`, `moonrise`, `moonset`
    *   **Auspicious**: `abhijit_muhurtham`, `amrita_kalam`, `brahma_muhurtham`, `pratah_sandhya`, `vijaya_muhurtham`, `godhuli_muhurtham`, `sayam_sandhya`, `nishita_muhurtham`
4.  **Database Update**:
    *   Uses `date` as the unique identifier.
    *   It performs an `update_or_create` (or `get_or_create` + update depending on version) to ensure no duplicates are created.
    *   Existing records for the same date will be updated with the new values.
    *   **Note**: Tithi, Nakshatra, and Inauspicious timings are **SKIPPED** in this import process as per configuration.

## Troubleshooting

-   **"Date already exists"**: The model enforces `unique=True` on the `date` field. The script handles this by updating the existing record instead of failing.
-   **Missing Fields**: If new fields are added to the JSON, the script needs to be updated to parse them.

## Verification

Check the Django Admin panel under `Panchang Data` to verify the imported records.
