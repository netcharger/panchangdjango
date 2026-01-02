import requests
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import django
from django.conf import settings
from django.db import transaction

import sys

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panchang_api.settings')
django.setup()

# -------- SETTINGS ----------
API_BASE=os.getenv("PANCHANG_API_BASE", "http://127.0.0.1:8000")
API_URL = f"{API_BASE}/api/panchang/today/?date="
OUTPUT_FOLDER = "media/panchang_files"
MAX_THREADS = 10
MAX_RETRIES = 3  # Number of retries for failed requests
RETRY_DELAY = 2  # Seconds to wait between retries
# ----------------------------


def auto_delete_and_create_folder(path):
    """Automatically delete existing folder and create new one."""
    if os.path.exists(path):
        print(f"[DELETE] Deleting existing folder: {path}")
        shutil.rmtree(path)

    os.makedirs(path)
    print(f"[CREATE] Created new folder: {path}")
    return True


def save_panchang_generation_info(from_date, to_date):
    """Save panchang generation metadata to site settings."""
    try:
        from mobileapp_settings.models import SiteSetting

        generation_info = {
            "date_generated": datetime.now().strftime("%d-%m-%Y"),
            "from_date": from_date,
            "to_date": to_date,
            "generated_at": datetime.now().isoformat()
        }

        # Convert to JSON string for storage
        json_info = json.dumps(generation_info, indent=2, ensure_ascii=False)

        # Update or create the site setting
        setting, created = SiteSetting.objects.update_or_create(
            key='panchang_generation_info',
            defaults={
                'value_type': 'text',
                'text_value': json_info,
                'description': 'Information about the last panchang files generation'
            }
        )

        action = "Created" if created else "Updated"
        print(f"[OK] {action} panchang generation info in site settings")
        print(f"   Key: panchang_generation_info")
        print(f"   Generated: {generation_info['date_generated']}")
        print(f"   Date range: {from_date} to {to_date}")

        return True

    except Exception as e:
        print(f"[ERROR] Error saving generation info: {str(e)}")
        return False


def save_json(date_str, data):
    filename = f"{date_str}.json"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] Saved: {filename}")


def fetch_and_save(date_str, skip_existing=True, retry_count=0):
    """Fetch JSON from API and save it. Skip if file already exists.

    Returns:
        tuple: (status, message, error_msg) where status is 'saved', 'skipped', or 'error'
    """
    filename = f"{date_str}.json"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    # Check if file already exists
    if skip_existing and os.path.exists(filepath):
        print(f"[SKIP] Skipped: {filename} (already exists)")
        return ('skipped', filename, None)

    url = API_URL + date_str+"&language=te"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check if API returned an error message in the JSON response
        if isinstance(data, dict) and 'error' in data:
            error_msg = f"API Error: {data.get('error')}"
            print(f"[ERROR] Error fetching {date_str}: {error_msg}")
            return ('error', filename, error_msg)

        save_json(date_str, data)
        return ('saved', filename, None)

    except requests.exceptions.HTTPError as e:
        # Get error details from response if available
        error_msg = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                # Try to get error message from JSON response
                error_data = e.response.json()
                if isinstance(error_data, dict) and 'error' in error_data:
                    error_msg = f"{e.response.status_code} Server Error: {error_data.get('error')}"
            except:
                pass

            if not error_msg:
                error_msg = f"{e.response.status_code} Server Error: {e.response.reason}"
        else:
            error_msg = f"HTTP Error: {str(e)}"

        # Don't retry on specific calculation errors (like "Unable to find a dawn time")
        if error_msg and "Unable to find a dawn time" in error_msg:
            print(f"[ERROR] Calculation error for {date_str}: {error_msg}")
            return ('error', filename, error_msg)

        if retry_count < MAX_RETRIES:
            print(f"[WARN]  Error fetching {date_str}: {error_msg}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            return fetch_and_save(date_str, skip_existing, retry_count + 1)
        else:
            print(f"[ERROR] Error fetching {date_str} after {MAX_RETRIES} retries: {error_msg}")
            return ('error', filename, error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request Error: {str(e)}"
        if retry_count < MAX_RETRIES:
            print(f"[WARN]  Network error fetching {date_str}: {error_msg}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            return fetch_and_save(date_str, skip_existing, retry_count + 1)
        else:
            print(f"[ERROR] Error fetching {date_str} after {MAX_RETRIES} retries: {error_msg}")
            return ('error', filename, error_msg)

    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        print(f"[ERROR] Unexpected error fetching {date_str}: {error_msg}")
        return ('error', filename, error_msg)


def generate_files(from_date, to_date):
    """Generate panchang JSON files between two dates."""
    # Automatically delete existing folder and create new one
    folder_deleted = auto_delete_and_create_folder(OUTPUT_FOLDER)

    print(f"\n[GENERATE] Generating Panchang files from {from_date} to {to_date}\n")

    # Build date list
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")

    date_list = []
    cur = start
    while cur <= end:
        date_list.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    print(f"Total dates: {len(date_list)}\n")

    # Count existing files
    existing_count = 0
    for date_str in date_list:
        filename = f"{date_str}.json"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(filepath):
            existing_count += 1

    if existing_count > 0:
        print(f"[INFO]  Found {existing_count} existing files. They will be skipped.\n")

    # Multi-threading
    success_count = 0
    skip_count = 0
    error_count = 0
    failed_dates = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(fetch_and_save, d, skip_existing=True): d for d in date_list}
        for future in as_completed(futures):
            result = future.result()
            status = result[0]
            filename = result[1]
            error_msg = result[2] if len(result) > 2 else None

            if status == 'saved':
                success_count += 1
            elif status == 'skipped':
                skip_count += 1
            elif status == 'error':
                error_count += 1
                date_str = futures[future]
                failed_dates.append((date_str, error_msg))

    print(f"\n{'='*50}")
    print(f"[SUCCESS] Summary:")
    print(f"   • Saved: {success_count} files")
    if skip_count > 0:
        print(f"   • Skipped: {skip_count} existing files")
    if error_count > 0:
        print(f"   • Errors: {error_count} files")
        print(f"\n   Failed dates:")
        for date_str, error_msg in failed_dates[:10]:  # Show first 10 errors
            print(f"      • {date_str}: {error_msg}")
        if len(failed_dates) > 10:
            print(f"      ... and {len(failed_dates) - 10} more")

        # Save failed dates to a file for retry
        failed_file = os.path.join(OUTPUT_FOLDER, "failed_dates.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for date_str, error_msg in failed_dates:
                f.write(f"{date_str} - {error_msg}\n")
        print(f"\n   [SAVE] Failed dates saved to: {failed_file}")
    print(f"{'='*50}")

    # Save generation metadata to site settings (only if generation was successful)
    if success_count > 0:
        print("\n[SAVE] Saving generation metadata...")
        save_panchang_generation_info(from_date, to_date)


def retry_failed_dates():
    """Retry only the dates that failed (from failed_dates.txt)."""
    failed_file = os.path.join(OUTPUT_FOLDER, "failed_dates.txt")

    if not os.path.exists(failed_file):
        print("[ERROR] No failed_dates.txt file found. Nothing to retry.")
        return

    # Read failed dates
    failed_dates = []
    with open(failed_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and ' - ' in line:
                date_str = line.split(' - ')[0].strip()
                failed_dates.append(date_str)

    if not failed_dates:
        print("[SUCCESS] No failed dates to retry!")
        return

    print(f"\n[RETRY] Retrying {len(failed_dates)} failed dates...\n")
    print(f"Dates to retry: {', '.join(failed_dates)}\n")

    # Retry with skip_existing=False to force re-fetch
    success_count = 0
    error_count = 0
    still_failed = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(fetch_and_save, d, skip_existing=False): d for d in failed_dates}
        for future in as_completed(futures):
            result = future.result()
            status = result[0]
            filename = result[1]
            error_msg = result[2] if len(result) > 2 else None

            if status == 'saved':
                success_count += 1
            elif status == 'error':
                error_count += 1
                date_str = futures[future]
                still_failed.append((date_str, error_msg))

    print(f"\n{'='*50}")
    print(f"[RETRY] Retry Summary:")
    print(f"   • Successfully saved: {success_count} files")
    if error_count > 0:
        print(f"   • Still failing: {error_count} files")
        print(f"\n   Still failed dates:")
        for date_str, error_msg in still_failed:
            print(f"      • {date_str}: {error_msg}")

        # Update failed_dates.txt with remaining failures
        failed_file = os.path.join(OUTPUT_FOLDER, "failed_dates.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for date_str, error_msg in still_failed:
                f.write(f"{date_str} - {error_msg}\n")
        print(f"\n   [SAVE] Updated failed_dates.txt")

        # Update generation metadata since some files were updated
        if success_count > 0:
            print("\n[SAVE] Updating generation metadata...")
            # Get the original date range from the existing generation info
            try:
                from mobileapp_settings.models import SiteSetting
                existing_setting = SiteSetting.objects.filter(key='panchang_generation_info').first()
                if existing_setting and existing_setting.text_value:
                    existing_info = json.loads(existing_setting.text_value)
                    from_date = existing_info.get('from_date', FROM_DATE)
                    to_date = existing_info.get('to_date', TO_DATE)
                else:
                    from_date = FROM_DATE
                    to_date = TO_DATE
                save_panchang_generation_info(from_date, to_date)
            except Exception as e:
                print(f"[ERROR] Error updating generation metadata: {str(e)}")
    else:
        # All succeeded, delete the failed_dates.txt file
        if os.path.exists(failed_file):
            os.remove(failed_file)
            print(f"\n   [SUCCESS] All dates succeeded! Removed failed_dates.txt")

        # Update generation metadata since all files were successfully generated
        if success_count > 0:
            print("\n[SAVE] Updating generation metadata...")
            # Get the original date range from the existing generation info
            try:
                from mobileapp_settings.models import SiteSetting
                existing_setting = SiteSetting.objects.filter(key='panchang_generation_info').first()
                if existing_setting and existing_setting.text_value:
                    existing_info = json.loads(existing_setting.text_value)
                    from_date = existing_info.get('from_date', FROM_DATE)
                    to_date = existing_info.get('to_date', TO_DATE)
                else:
                    from_date = FROM_DATE
                    to_date = TO_DATE
                save_panchang_generation_info(from_date, to_date)
            except Exception as e:
                print(f"[ERROR] Error updating generation metadata: {str(e)}")

    print(f"{'='*50}")


if __name__ == "__main__":
    import sys

    # Check if user wants to retry failed dates
    if len(sys.argv) > 1 and sys.argv[1] == "--retry-failed":
        retry_failed_dates()
    else:
        # 👉 CHANGE THESE DATES HERE
        FROM_DATE = "2025-12-01"
        TO_DATE   = "2026-12-31"

        generate_files(FROM_DATE, TO_DATE)
