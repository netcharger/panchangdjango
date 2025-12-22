import os
from io import BytesIO
from PIL import Image
from django.core.files import File
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


def convert_and_optimize_to_jpg(image_field, image_path, quality=88):
    """Converts an uploaded image to JPG and optimizes it."""
    if not image_field:
        return None

    try:
        img = Image.open(image_path)
        img = optimize_image_for_web(img, quality=quality)

        # Convert RGBA to RGB if needed (JPG doesn't support transparency)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Save the optimized JPG image to a BytesIO object
        jpg_io = BytesIO()
        img.save(jpg_io, format='JPEG', quality=quality, optimize=True)
        jpg_io.seek(0)

        # Get the original filename without extension
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        new_filename = f"{base_name}.jpg"

        # Create a new File object for the JPG image
        jpg_file = File(jpg_io, name=new_filename)
        return jpg_file
    except Exception as e:
        print(f"Error converting or optimizing image to JPG: {e}")
        return None


def convert_and_optimize_uploaded_image(image_field, image_path, quality=88):
    """Converts an uploaded image to WebP and optimizes it. Used for categories."""
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
        return webp_file
    except Exception as e:
        print(f"Error converting or optimizing image: {e}")
        return None


def optimize_image_for_web(img, quality=88, format='WEBP'):
    """
    Optimizes an image for web usage by converting to RGB, stripping metadata,
    and ensuring it's in the correct format.
    """
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    return img


def wallpaper_image_upload_to(instance, filename):
    """
    Custom upload_to function for wallpaper images.
    Saves all wallpapers in the 'wallpapers' folder.
    Original image is saved as JPG format.
    """
    # Clean filename and convert to JPG extension
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    jpg_filename = f"{clean_name}.jpg"
    
    # Save directly in wallpapers folder
    upload_path = f'wallpapers/{jpg_filename}'
    
    # Check if another wallpaper instance is using this filename
    from .models import Wallpaper
    existing_wallpaper = Wallpaper.objects.filter(image=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_wallpaper:
        # Another instance is using this filename, add hash to make it unique
        import time
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        jpg_filename = f"{clean_name}_{hash_suffix}.jpg"
        upload_path = f'wallpapers/{jpg_filename}'
    
    return upload_path


def category_image_upload_to(instance, filename):
    """
    Custom upload_to function for category images.
    """
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    webp_filename = f"{clean_name}.webp"
    upload_path = f'wallpaper_categories/{webp_filename}'
    
    from .models import Category
    existing_category = Category.objects.filter(image=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_category:
        import time
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        webp_filename = f"{clean_name}_{hash_suffix}.webp"
        upload_path = f'wallpaper_categories/{webp_filename}'
    
    return upload_path


def create_image_sizes(image_field, base_path, media_root=None):
    """
    Creates all image sizes (thumb, medium, large) as WebP format.
    Original image should be JPG, but size variants are saved as WebP.
    Creates folders like: base_dir/thumb/, base_dir/medium/, base_dir/large/
    """
    if not image_field or not base_path:
        return {}

    try:
        if not media_root:
            from django.conf import settings
            media_root = settings.MEDIA_ROOT
            image_sizes = settings.IMAGE_SIZES
        else:
            from django.conf import settings
            image_sizes = settings.IMAGE_SIZES

        img = Image.open(image_field)
        img = optimize_image_for_web(img, quality=88)

        # Convert RGBA to RGB if needed (for WebP conversion)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        base_dir = os.path.dirname(base_path)
        original_filename = os.path.basename(base_path)
        # Change extension to .webp for size variants
        name_without_ext = os.path.splitext(original_filename)[0]
        webp_filename = f"{name_without_ext}.webp"

        for size_name, width in image_sizes.items():
            img_copy = img.copy()
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)
            img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)

            size_dir = os.path.join(base_dir, size_name)
            os.makedirs(size_dir, exist_ok=True)

            size_path = os.path.join(size_dir, webp_filename)
            img_copy.save(size_path, 'WEBP', quality=88, method=6, optimize=True)

        return {}
    except Exception as e:
        print(f"Error creating image sizes: {e}")
        return {}

