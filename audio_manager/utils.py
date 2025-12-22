import os
from io import BytesIO
from PIL import Image
from django.core.files import File
from django.conf import settings
import hashlib

def calculate_image_hash(image_path):
    """Calculates MD5 hash of an image file."""
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def convert_and_optimize_uploaded_image(image_field, image_path, quality=88):
    """Converts an uploaded image to WebP and optimizes it."""
    if not image_field:
        return None

    try:
        img = Image.open(image_path)
        img = optimize_image_for_web(img, quality=quality)

        # Save the optimized WebP image to a BytesIO object
        webp_io = BytesIO()
        img.save(webp_io, format='WEBP', quality=quality, method=6, optimize=True)
        webp_io.seek(0)

        # Get the original filename without extension
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        new_filename = f"{base_name}.webp"

        # Create a new File object for the WebP image
        webp_file = File(webp_io, name=new_filename)

        # Update the image field with the new WebP file (without saving the model instance yet)
        image_field.save(new_filename, webp_file, save=False)
        
        # Return the path to the newly saved WebP file (in the temporary storage for now)
        return image_field.path
    except Exception as e:
        print(f"Error converting or optimizing image: {e}")
        return None

def optimize_image_for_web(img, quality=88, format='WEBP'):
    """
    Optimizes an image for web usage by converting to RGB, stripping metadata,
    and ensuring it's in the correct format.
    """
    # Convert to RGB if not already to avoid issues with transparency or different modes
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    return img

def create_image_thumbnails(image_field, base_path, media_root=None):
    """
    Create thumbnails (thumb, medium, large) for an image in WebP format
    Returns dict with relative paths to thumbnails (from MEDIA_ROOT)
    Uses WebP format for better SEO and optimization
    """
    if not image_field or not base_path:
        return {}

    try:
        # Get media root if not provided
        if not media_root:
            from django.conf import settings
            media_root = settings.MEDIA_ROOT

        # Open the original image
        img = Image.open(image_field)
        # Optimize image for web
        img = optimize_image_for_web(img, quality=88)

        # Get base directory and filename
        base_dir = os.path.dirname(base_path)
        original_filename = os.path.basename(base_path)
        name, _ = os.path.splitext(original_filename)
        # Use WebP extension for thumbnails
        webp_filename = f"{name}.webp"

        # Define sizes
        sizes = {
            'thumb': (300, 200),
            'medium': (800, 600),
            'large': (1600, 900),
        }

        thumbnail_paths = {}

        for size_name, (width, height) in sizes.items():
            # Create thumbnail maintaining aspect ratio
            img_copy = img.copy()
            img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Create size directory
            size_dir = os.path.join(base_dir, size_name)
            os.makedirs(size_dir, exist_ok=True)

            # Save thumbnail as WebP with optimization
            thumb_path = os.path.join(size_dir, webp_filename)
            # WebP quality: 85-90 provides excellent quality with good compression
            img_copy.save(thumb_path, 'WEBP', quality=88, method=6, optimize=True)

            # Get relative path from MEDIA_ROOT
            rel_path = os.path.relpath(thumb_path, media_root).replace('\\', '/')
            thumbnail_paths[size_name] = rel_path

        return thumbnail_paths
    except Exception as e:
        print(f"Error creating thumbnails: {e}")
        return {}
