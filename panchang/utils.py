"""
Utility functions for image processing and file uploads
"""
import os
import hashlib
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import slugify


def calculate_image_hash(image_file):
    """
    Calculate MD5 hash of image content for duplicate detection
    Returns hash string
    Handles file paths, file-like objects, and Django ImageField
    """
    hash_md5 = hashlib.md5()

    # Handle Django ImageField
    if hasattr(image_file, 'path'):
        # It's a Django ImageField - use the path
        image_path = image_file.path
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

    # Handle file path string
    if isinstance(image_file, str) and os.path.exists(image_file):
        with open(image_file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    # Handle file-like object
    if hasattr(image_file, 'read'):
        try:
            image_file.seek(0)  # Reset to beginning
            for chunk in iter(lambda: image_file.read(4096), b""):
                hash_md5.update(chunk)
            image_file.seek(0)  # Reset again for later use
            return hash_md5.hexdigest()
        except:
            pass

    # Fallback: try to read as bytes
    try:
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        hash_md5.update(image_file.read() if hasattr(image_file, 'read') else bytes(image_file))
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating image hash: {e}")
        return ""


def find_duplicate_image(image_hash, model_class, exclude_pk=None):
    """
    Find if an image with the same hash already exists across all models
    Returns the existing image path if found, None otherwise
    """
    try:
        from .models import Festival, ImportantDay, FestivalGallery, ImportantDayGallery

        # Check all models that have images
        for model in [Festival, ImportantDay, FestivalGallery, ImportantDayGallery]:
            # Skip checking the same model with same pk (to avoid matching itself)
            if model == model_class and exclude_pk:
                queryset = model.objects.filter(image_hash=image_hash).exclude(pk=exclude_pk)
            else:
                queryset = model.objects.filter(image_hash=image_hash)

            existing = queryset.first()
            if existing and existing.image:
                # Return the path to existing image
                if hasattr(existing.image, 'path'):
                    return existing.image.path
                elif hasattr(existing.image, 'url'):
                    return existing.image.url
    except Exception as e:
        print(f"Error finding duplicate image: {e}")
        import traceback
        traceback.print_exc()
    return None


def clean_filename(filename, use_webp=True):
    """Remove spaces and special characters from filename, optionally convert to WebP"""
    name, ext = os.path.splitext(filename)
    # Replace spaces with hyphens and slugify
    name = slugify(name.replace(' ', '-'))
    # Convert to WebP for better SEO and optimization
    if use_webp:
        ext = '.webp'
    return f"{name}{ext}"


def festival_image_upload_path(instance, filename):
    """Generate upload path for festival images (converted to WebP)"""
    if not instance.slug:
        # Generate slug if not exists
        slug = slugify(instance.festival_name)
    else:
        slug = instance.slug
    filename = clean_filename(filename, use_webp=True)
    return f'uploads/festivals/{slug}/{filename}'


def important_day_image_upload_path(instance, filename):
    """Generate upload path for important day images (converted to WebP)"""
    if not instance.slug:
        # Generate slug if not exists
        slug = slugify(f"{instance.day_name} {instance.date}")
    else:
        slug = instance.slug
    filename = clean_filename(filename, use_webp=True)
    return f'uploads/important-days/{slug}/{filename}'


def optimize_image_for_web(img, quality=88, format='WEBP'):
    """
    Optimize image for web with compression without losing quality
    Uses WebP format for better SEO and smaller file sizes

    Quality settings:
    - 85-90: Excellent quality with good compression (recommended)
    - 80-85: Very good quality with better compression
    - 75-80: Good quality with high compression

    WebP provides 25-35% better compression than JPEG at the same quality level
    """
    # Convert RGBA to RGB if needed (WebP supports transparency, but we'll use RGB for consistency)
    if img.mode in ('RGBA', 'LA'):
        # Create white background for transparency
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
        else:
            rgb_img.paste(img)
        img = rgb_img
    elif img.mode == 'P':
        # Convert palette mode to RGB
        img = img.convert('RGBA')
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = rgb_img
    elif img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    return img


def create_image_sizes(image_field, base_path, media_root=None):
    """
    Unified function to create all image sizes (small, thumb, medium, large) for mobile view.
    Creates folders like: base_dir/small/, base_dir/thumb/, base_dir/medium/, base_dir/large/
    Uses the same filename in all size folders.
    Only saves original image URL in DB - sizes are created on disk only.
    
    Args:
        image_field: Django ImageField instance
        base_path: Full path to the original image file
        media_root: MEDIA_ROOT path (optional, will get from settings if not provided)
    
    Returns:
        dict: Empty dict (sizes are created on disk, not returned for DB storage)
    """
    if not image_field or not base_path:
        return {}

    try:
        # Get media root if not provided
        if not media_root:
            from django.conf import settings
            media_root = settings.MEDIA_ROOT
            image_sizes = settings.IMAGE_SIZES
        else:
            from django.conf import settings
            image_sizes = settings.IMAGE_SIZES

        # Open the original image
        img = Image.open(image_field)
        # Optimize image for web
        img = optimize_image_for_web(img, quality=88)

        # Get base directory and filename
        base_dir = os.path.dirname(base_path)
        original_filename = os.path.basename(base_path)
        
        # Use the exact same filename for all sizes
        webp_filename = original_filename

        # Create all sizes: small, thumb, medium, large
        for size_name, width in image_sizes.items():
            # Create thumbnail maintaining aspect ratio (width only, height auto)
            img_copy = img.copy()
            # Calculate height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)
            img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Create size directory (e.g., festivals/small/, festivals/thumb/, etc.)
            size_dir = os.path.join(base_dir, size_name)
            os.makedirs(size_dir, exist_ok=True)

            # Save thumbnail as WebP with optimization
            size_path = os.path.join(size_dir, webp_filename)
            # WebP quality: 85-90 provides excellent quality with good compression
            img_copy.save(size_path, 'WEBP', quality=88, method=6, optimize=True)

        return {}
    except Exception as e:
        print(f"Error creating image sizes: {e}")
        import traceback
        traceback.print_exc()
        return {}


def create_image_thumbnails(image_field, base_path, media_root=None):
    """
    DEPRECATED: Use create_image_sizes instead.
    Kept for backward compatibility.
    Create thumbnails (thumb, medium, large) for an image in WebP format
    Returns dict with relative paths to thumbnails (from MEDIA_ROOT)
    Uses WebP format for better SEO and optimization
    """
    # Call the new unified function
    create_image_sizes(image_field, base_path, media_root)
    # Return empty dict as we don't store paths in DB anymore
    return {}


def convert_and_optimize_uploaded_image(image_field, output_path, quality=88):
    """
    Convert uploaded image to WebP format and optimize it
    Returns the path to the optimized image
    """
    try:
        # Open the original image
        img = Image.open(image_field)
        # Optimize image for web
        img = optimize_image_for_web(img, quality=quality)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # Convert filename to WebP
        name, _ = os.path.splitext(output_path)
        webp_path = f"{name}.webp"

        # Save as WebP with optimization
        img.save(webp_path, 'WEBP', quality=quality, method=6, optimize=True)

        return webp_path
    except Exception as e:
        print(f"Error converting image to WebP: {e}")
        import traceback
        traceback.print_exc()
        return None


def gallery_image_upload_path(instance, filename):
    """Generate upload path for gallery images (converted to WebP)"""
    if instance.festival:
        slug = instance.festival.slug or slugify(instance.festival.festival_name)
        base_path = f'uploads/festivals/{slug}/wallpapers'
    elif instance.important_day:
        slug = instance.important_day.slug or slugify(f"{instance.important_day.day_name} {instance.important_day.date}")
        base_path = f'uploads/important-days/{slug}/wallpapers'
    else:
        base_path = 'uploads/gallery'

    filename = clean_filename(filename, use_webp=True)
    return f'{base_path}/{filename}'


def carousel_image_upload_path(instance, filename):
    """Generate upload path for carousel images (converted to WebP)"""
    filename = clean_filename(filename, use_webp=True)
    return f'carousel_images/{filename}'


def site_setting_image_upload_path(instance, filename):
    """Generate upload path for site setting images (converted to WebP)"""
    # Assuming 'key' is a unique identifier for the site setting
    slug = slugify(instance.key)
    filename = clean_filename(filename, use_webp=True)
    return f'uploads/site_settings/{slug}/{filename}'


def calculate_future_festival_dates(
    tithi: str,
    paksha: str,
    month: Optional[str] = None,
    nakshatra: Optional[str] = None,
    start_date: Optional[date] = None,
    years_ahead: int = 2,
    max_results: int = 5,
    location: Optional[Dict] = None
) -> List[Dict[str, str]]:
    """
    Calculate future dates when a festival will occur based on tithi, paksha, month, and optionally nakshatra.

    Args:
        tithi: Tithi name (e.g., "Amavasya", "Purnima", "Ekadashi")
        paksha: Paksha name (e.g., "Krishna", "Shukla")
        month: Optional month name (e.g., "Kartika", "Chaitra")
        nakshatra: Optional nakshatra name
        start_date: Start date for search (defaults to today)
        years_ahead: Number of years to search ahead (default: 2)
        max_results: Maximum number of dates to return (default: 5)
        location: Location dict for panchang calculation (defaults to Chennai, India)

    Returns:
        List of dicts with 'date' and 'time' keys for matching dates
    """
    try:
        from panchang.calculations.panchangam_calculation_v2 import compute_panchang_for_date, LOCATION

        if start_date is None:
            start_date = date.today()

        if location is None:
            location = LOCATION

        # Normalize paksha name (remove "Paksha" suffix if present)
        paksha_normalized = paksha.replace('Paksha', '').strip() if paksha else None

        results = []
        current_date = start_date
        end_date = date(current_date.year + years_ahead, 12, 31)

        # Optimize: Search approximately every 29 days (lunar month cycle)
        # But also check adjacent days to catch exact matches
        search_interval = 29  # days
        days_checked = 0
        max_days_to_check = 365 * years_ahead  # Safety limit

        while current_date <= end_date and len(results) < max_results and days_checked < max_days_to_check:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                # Calculate panchang for this date
                panchang_result = compute_panchang_for_date(
                    date_str,
                    location=location,
                    profile_code='en',
                    format_profile=False,
                    include_raw=False,
                )

                if not isinstance(panchang_result, dict):
                    current_date += timedelta(days=1)
                    days_checked += 1
                    continue

                # Extract panchang data
                core_panchang = panchang_result.get('core_panchang', {})
                tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                paksha_info = panchang_result.get('Paksha', {})
                amanta_month = panchang_result.get('Amanta Month', {})
                purnimanta_month = panchang_result.get('Purnimanta Month', {})

                # Check if tithi matches
                tithi_matches = False
                if tithi_events:
                    tithi_names = [t.get('name') for t in tithi_events if t.get('name')]
                    tithi_matches = tithi in tithi_names

                # Check if paksha matches
                paksha_matches = False
                if paksha_info:
                    paksha_name = paksha_info.get('name', '')
                    paksha_name_normalized = paksha_name.replace('Paksha', '').strip()
                    paksha_matches = (
                        paksha.lower() == paksha_name.lower() or
                        paksha_normalized and paksha_normalized.lower() == paksha_name_normalized.lower()
                    )

                # Check if month matches (optional)
                month_matches = True  # Default to True if month not specified
                if month:
                    amanta_month_name = amanta_month.get('name', '') if amanta_month else ''
                    purnimanta_month_name = purnimanta_month.get('name', '') if purnimanta_month else ''
                    month_matches = (
                        month.lower() == amanta_month_name.lower() or
                        month.lower() == purnimanta_month_name.lower()
                    )

                # Check if nakshatra matches (optional)
                nakshatra_matches = True  # Default to True if nakshatra not specified
                if nakshatra and nakshatra_events:
                    nakshatra_names = [n.get('name') for n in nakshatra_events if n.get('name')]
                    nakshatra_matches = nakshatra in nakshatra_names

                # If all criteria match, add to results
                if tithi_matches and paksha_matches and month_matches and nakshatra_matches:
                    # Find the exact time when tithi occurs
                    tithi_time = None
                    for t_event in tithi_events:
                        if t_event.get('name') == tithi:
                            # Get the start time of the tithi
                            start_time = t_event.get('start')
                            if start_time:
                                tithi_time = start_time
                            break

                    results.append({
                        'date': date_str,
                        'time': tithi_time.strftime('%I:%M %p') if tithi_time else 'N/A',
                        'datetime': tithi_time.isoformat() if tithi_time else date_str
                    })

                # Move to next search point (optimized: skip ahead by lunar month, but check nearby days)
                if tithi_matches and paksha_matches:
                    # If we found a match, check next few days more carefully
                    current_date += timedelta(days=1)
                else:
                    # Otherwise, skip ahead by approximate lunar month
                    current_date += timedelta(days=search_interval)

                days_checked += 1

            except Exception as e:
                # If calculation fails for a date, skip it
                current_date += timedelta(days=1)
                days_checked += 1
                continue

        return results[:max_results]

    except ImportError:
        # If panchang calculation module is not available
        return []
    except Exception as e:
        print(f"Error calculating future festival dates: {e}")
        import traceback
        traceback.print_exc()
        return []
