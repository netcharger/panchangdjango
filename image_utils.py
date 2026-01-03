"""
Universal Image Deletion and Processing Utility
This module provides functions to delete, convert to WebP, and create size variants for images across all apps.
"""
import os
from io import BytesIO
from PIL import Image
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings
import hashlib
from django.utils.text import slugify

def calculate_image_hash(image_path):
    """Calculates MD5 hash of an image file."""
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def optimize_image_for_web(img, quality=88):
    """
    Optimizes an image for web usage by converting to RGB, stripping metadata,
    and ensuring it's in the correct format.
    """
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    return img

def convert_to_webp(image_field_or_path, quality=88, verbose=True):
    """
    Converts an image to WebP format and optimizes it.

    Args:
        image_field_or_path: A Django ImageField instance or a full path to an image file.
        quality (int): WebP quality (0-100). Default: 88.
        verbose (bool): If True, prints detailed conversion logs. Default: True.

    Returns:
        django.core.files.File or None: A new File object for the WebP image,
                                        or None if conversion fails.
    """
    image_path = None
    if hasattr(image_field_or_path, 'path'):
        image_path = image_field_or_path.path
    elif isinstance(image_field_or_path, str):
        image_path = image_field_or_path

    if not image_path:
        if verbose: print("[CONVERT] Invalid image_field_or_path provided.")
        return None

    if verbose: print(f"[CONVERT] Attempting to convert {image_path} to WebP...")

    try:
        img = Image.open(image_path)
        img = optimize_image_for_web(img, quality=quality)

        webp_io = BytesIO()
        img.save(webp_io, format='WEBP', quality=quality, method=6, optimize=True)
        webp_io.seek(0)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        new_filename = f"{base_name}.webp"

        webp_file = File(webp_io, name=new_filename)
        if verbose: print(f"[CONVERT] Successfully converted to WebP: {new_filename}")
        return webp_file
    except Exception as e:
        if verbose: print(f"[CONVERT] Error converting or optimizing image {image_path}: {e}")
        import traceback
        if verbose: traceback.print_exc()
        return None

def create_image_sizes(image_field, media_root=None, verbose=True):
    """
    Creates all defined image sizes (thumb, medium, large) for a given image.

    Args:
        image_field: Django ImageField instance (expected to be a WebP file already).
                         Its .path and .name attributes are used.
        media_root (str): MEDIA_ROOT path.
        verbose (bool): If True, prints detailed creation logs. Default: True.
    """
    if not image_field or not image_field.path:
        if verbose: print("[RESIZE] Invalid ImageField or image_field.path provided for size creation.")
        return

    if verbose: print(f"[RESIZE] Starting creation of sizes for: {image_field.name}")

    try:
        if not media_root: media_root = settings.MEDIA_ROOT
        image_sizes = getattr(settings, 'IMAGE_SIZES', {
            'thumb': 200,
            'medium': 600,
            'large': 800
        })

        img = Image.open(image_field.path) # Open the already converted WebP image
        img = optimize_image_for_web(img) # Ensure optimized colorspace

        # Get base directory from the ImageField's relative name
        # e.g., 'categories/myimage.webp' -> 'categories'
        base_dir_relative = os.path.dirname(image_field.name).replace('\\', '/')
        original_filename_webp = os.path.basename(image_field.name)

        for size_name, width in image_sizes.items():
            img_copy = img.copy()
            # Calculate height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)
            img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Construct full path for the sized image
            size_dir_full = os.path.join(media_root, base_dir_relative, size_name)
            os.makedirs(size_dir_full, exist_ok=True)

            size_path_full = os.path.join(size_dir_full, original_filename_webp)

            img_copy.save(size_path_full, 'WEBP', quality=88, method=6, optimize=True)
            if verbose: print(f"[RESIZE] Created size '{size_name}' at: {size_path_full}")

    except Exception as e:
        if verbose: print(f"[RESIZE] Error creating image sizes for {image_field.name}: {e}")
        import traceback
        if verbose: traceback.print_exc()


def delete_image_and_versions(image_path, verbose=True):
    """
    Universal function to delete an image and all its size variants (thumb, medium, large).

    This function can be used across all apps in the project to delete images
    and their automatically generated size variants.

    Args:
        image_path (str or ImageField): The relative path to the image from MEDIA_ROOT or an ImageField instance.
        verbose (bool): If True, prints detailed deletion logs. Default: True

    Returns:
        dict: A dictionary with deletion results:
              {
                  'main_image_deleted': bool,
                  'size_variants_deleted': list of deleted paths,
                  'size_variants_not_found': list of paths that didn't exist,
                  'errors': list of error messages
              }
    """
    result = {
        'main_image_deleted': False,
        'size_variants_deleted': [],
        'size_variants_not_found': [],
        'errors': []
    }

    # Extract path from ImageField if needed
    original_image_name_in_db = None
    if hasattr(image_path, 'name'):
        original_image_name_in_db = image_path.name
    elif isinstance(image_path, str):
        original_image_name_in_db = image_path

    if not original_image_name_in_db:
        if verbose:
            print(f"[DELETE] No image path provided for deletion")
        return result

    # Normalize path separators (ensure forward slashes for Django storage)
    original_image_name_in_db = original_image_name_in_db.replace('\\', '/')

    if verbose:
        print(f"=== DELETION START: {original_image_name_in_db} ===")

    # Delete the main image file
    if default_storage.exists(original_image_name_in_db):
        try:
            default_storage.delete(original_image_name_in_db)
            result['main_image_deleted'] = True
            if verbose:
                print(f"✓ Deleted main image: {original_image_name_in_db}")
        except Exception as e:
            error_msg = f"Error deleting main image {original_image_name_in_db}: {e}"
            result['errors'].append(error_msg)
            if verbose:
                print(f"✗ {error_msg}")
                import traceback
                traceback.print_exc()

    # Delete all size variants
    base_filename = os.path.basename(original_image_name_in_db)
    image_dir = os.path.dirname(original_image_name_in_db)

    # Get image sizes from settings
    image_sizes = getattr(settings, 'IMAGE_SIZES', {
        'thumb': 200,
        'medium': 600,
        'large': 800
    })

    if verbose:
        print(f"Checking for size variants in directory: {image_dir} with base name: {base_filename}")

    for size_name in image_sizes.keys():
        size_variant_name_relative = f"{image_dir}/{size_name}/{base_filename}"
        # Ensure forward slashes
        size_variant_name_relative = size_variant_name_relative.replace('\\', '/')

        if default_storage.exists(size_variant_name_relative):
            try:
                default_storage.delete(size_variant_name_relative)
                result['size_variants_deleted'].append(size_variant_name_relative)
                if verbose:
                    print(f"✓ Deleted size variant: {size_variant_name_relative}")
            except Exception as e:
                error_msg = f"Error deleting size variant {size_variant_name_relative}: {e}"
                result['errors'].append(error_msg)
                if verbose:
                    print(f"✗ {error_msg}")
                    import traceback
                    traceback.print_exc()
        else:
            result['size_variants_not_found'].append(size_variant_name_relative)
            if verbose:
                # Only print warning if we expected it to be there, but for now just debug
                # print(f"⚠ Size variant does not exist: {size_variant_name_relative}")
                pass

    if verbose:
        print(f"=== DELETION END: {original_image_name_in_db} ===")
        print(f"Summary: Main image: {'✓' if result['main_image_deleted'] else '✗'}, "
              f"Size variants deleted: {len(result['size_variants_deleted'])}, "
              f"Errors: {len(result['errors'])}")

    return result


def delete_multiple_images(image_paths, verbose=True):
    """
    Delete multiple images and their size variants.

    Args:
        image_paths (list): List of image paths (strings or ImageField instances)
        verbose (bool): If True, prints detailed deletion logs. Default: True

    Returns:
        dict: Summary of all deletions with overall statistics
    """
    results = []
    total_main_deleted = 0
    total_sizes_deleted = 0
    total_errors = 0

    for image_path in image_paths:
        result = delete_image_and_versions(image_path, verbose=verbose)
        results.append(result)
        if result['main_image_deleted']:
            total_main_deleted += 1
        total_sizes_deleted += len(result['size_variants_deleted'])
        total_errors += len(result['errors'])

    summary = {
        'total_images_processed': len(image_paths),
        'main_images_deleted': total_main_deleted,
        'total_size_variants_deleted': total_sizes_deleted,
        'total_errors': total_errors,
        'detailed_results': results
    }

    if verbose:
        print(f"\n=== BATCH DELETION SUMMARY ===")
        print(f"Total images processed: {len(image_paths)}")
        print(f"Main images deleted: {total_main_deleted}/{len(image_paths)}")
        print(f"Total size variants deleted: {total_sizes_deleted}")
        print(f"Total errors: {total_errors}")

    return summary
