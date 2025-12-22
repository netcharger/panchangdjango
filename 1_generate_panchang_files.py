import requests
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


import sys

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
# -------- SETTINGS ----------
API_URL = "http://127.0.0.1:8000/api/panchang/today/?date="
OUTPUT_FOLDER = "panchang_files"
MAX_THREADS = 10
MAX_RETRIES = 3  # Number of retries for failed requests
RETRY_DELAY = 2  # Seconds to wait between retries
# ----------------------------


def ask_delete_folder(path):
    """Ask user if they want to delete the folder."""
    if os.path.exists(path):
        while True:
            response = input(f"📁 Folder '{path}' already exists. Delete it? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                print(f"🗑 Deleting existing folder: {path}")
                shutil.rmtree(path)
                os.makedirs(path)
                print(f"📁 Created new folder: {path}")
                return True
            elif response in ['n', 'no']:
                print(f"📁 Keeping existing folder: {path}")
                # Create folder if it doesn't exist
                if not os.path.exists(path):
                    os.makedirs(path)
                return False
            else:
                print("Please enter 'y' or 'n'")
    else:
        os.makedirs(path)
        print(f"📁 Created new folder: {path}")
        return False


def save_json(date_str, data):
    filename = f"{date_str}.json"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✔ Saved: {filename}")


def fetch_and_save(date_str, skip_existing=True, retry_count=0):
    """Fetch JSON from API and save it. Skip if file already exists.

    Returns:
        tuple: (status, message, error_msg) where status is 'saved', 'skipped', or 'error'
    """
    filename = f"{date_str}.json"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    # Check if file already exists
    if skip_existing and os.path.exists(filepath):
        print(f"⏭ Skipped: {filename} (already exists)")
        return ('skipped', filename, None)

    url = API_URL + date_str+"&language=te"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check if API returned an error message in the JSON response
        if isinstance(data, dict) and 'error' in data:
            error_msg = f"API Error: {data.get('error')}"
            print(f"❌ Error fetching {date_str}: {error_msg}")
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
            print(f"❌ Calculation error for {date_str}: {error_msg}")
            return ('error', filename, error_msg)

        if retry_count < MAX_RETRIES:
            print(f"⚠️  Error fetching {date_str}: {error_msg}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            return fetch_and_save(date_str, skip_existing, retry_count + 1)
        else:
            print(f"❌ Error fetching {date_str} after {MAX_RETRIES} retries: {error_msg}")
            return ('error', filename, error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request Error: {str(e)}"
        if retry_count < MAX_RETRIES:
            print(f"⚠️  Network error fetching {date_str}: {error_msg}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            return fetch_and_save(date_str, skip_existing, retry_count + 1)
        else:
            print(f"❌ Error fetching {date_str} after {MAX_RETRIES} retries: {error_msg}")
            return ('error', filename, error_msg)

    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        print(f"❌ Unexpected error fetching {date_str}: {error_msg}")
        return ('error', filename, error_msg)


def generate_files(from_date, to_date):
    """Generate panchang JSON files between two dates."""
    # Ask user if they want to delete the folder
    folder_deleted = ask_delete_folder(OUTPUT_FOLDER)

    print(f"\n📅 Generating Panchang files from {from_date} to {to_date}\n")

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
        print(f"ℹ️  Found {existing_count} existing files. They will be skipped.\n")

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
    print(f"✅ Summary:")
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
        print(f"\n   💾 Failed dates saved to: {failed_file}")
    print(f"{'='*50}")


def retry_failed_dates():
    """Retry only the dates that failed (from failed_dates.txt)."""
    failed_file = os.path.join(OUTPUT_FOLDER, "failed_dates.txt")

    if not os.path.exists(failed_file):
        print("❌ No failed_dates.txt file found. Nothing to retry.")
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
        print("✅ No failed dates to retry!")
        return

    print(f"\n🔄 Retrying {len(failed_dates)} failed dates...\n")
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
    print(f"🔄 Retry Summary:")
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
        print(f"\n   💾 Updated failed_dates.txt")
    else:
        # All succeeded, delete the failed_dates.txt file
        if os.path.exists(failed_file):
            os.remove(failed_file)
            print(f"\n   ✅ All dates succeeded! Removed failed_dates.txt")
    print(f"{'='*50}")


if __name__ == "__main__":
    import sys

    # Check if user wants to retry failed dates
    if len(sys.argv) > 1 and sys.argv[1] == "--retry-failed":
        retry_failed_dates()
    else:
        # 👉 CHANGE THESE DATES HERE
        FROM_DATE = "2025-10-01"
        TO_DATE   = "2026-12-31"

        generate_files(FROM_DATE, TO_DATE)
