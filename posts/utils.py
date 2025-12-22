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
        # image_field.save(new_filename, webp_file, save=False)
        
        # Return the new webp_file object instead of the path
        return webp_file
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

def category_image_upload_to(instance, filename):
    """
    Custom upload_to function for category images.
    Preserves original filename, only adds hash if duplicate exists in database.
    """
    # Clean filename and convert to WebP extension
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    webp_filename = f"{clean_name}.webp"
    
    upload_path = f'categories/{webp_filename}'
    
    # Check if another category instance is using this filename
    from .models import Category
    existing_category = Category.objects.filter(category_image=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_category:
        # Another instance is using this filename, add hash to make it unique
        import time
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        webp_filename = f"{clean_name}_{hash_suffix}.webp"
        upload_path = f'categories/{webp_filename}'
    
    return upload_path


def post_image_upload_to(instance, filename):
    """
    Custom upload_to function for post featured images.
    Preserves original filename, only adds hash if duplicate exists in database.
    """
    # Clean filename and convert to WebP extension
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    webp_filename = f"{clean_name}.webp"
    
    upload_path = f'posts/{webp_filename}'
    
    # Check if another post instance is using this filename
    from .models import Post
    existing_post = Post.objects.filter(featured_image=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_post:
        # Another instance is using this filename, add hash to make it unique
        import time
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        webp_filename = f"{clean_name}_{hash_suffix}.webp"
        upload_path = f'posts/{webp_filename}'
    
    return upload_path


def post_gallery_image_upload_to(instance, filename):
    """
    Custom upload_to function for post gallery images.
    Preserves original filename, only adds hash if duplicate exists in database.
    """
    # Clean filename and convert to WebP extension
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    webp_filename = f"{clean_name}.webp"
    
    upload_path = f'post_images/{webp_filename}'
    
    # Check if another PostImage instance is using this filename
    from .models import PostImage
    existing_image = PostImage.objects.filter(image_file=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_image:
        # Another instance is using this filename, add hash to make it unique
        import time
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        webp_filename = f"{clean_name}_{hash_suffix}.webp"
        upload_path = f'post_images/{webp_filename}'
    
    return upload_path


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

            # Create size directory (e.g., categories/small/, categories/thumb/, etc.)
            size_dir = os.path.join(base_dir, size_name)
            os.makedirs(size_dir, exist_ok=True)

            # Save thumbnail as WebP with optimization
            size_path = os.path.join(size_dir, webp_filename)
            # WebP quality: 85-90 provides excellent quality with good compression
            img_copy.save(size_path, 'WEBP', quality=88, method=6, optimize=True)

        return {}
    except Exception as e:
        print(f"Error creating image sizes: {e}")
        return {}


def create_image_thumbnails(image_field, base_path, media_root=None):
    """
    DEPRECATED: Use create_image_sizes instead.
    Kept for backward compatibility.
    Create thumbnails (thumb, medium, large) for an image in WebP format
    Returns dict with relative paths to thumbnails (from MEDIA_ROOT)
    Uses WebP format for better SEO and optimization
    Uses the same filename (without hash) in thumb, medium, and large folders
    """
    # Call the new unified function
    create_image_sizes(image_field, base_path, media_root)
    # Return empty dict as we don't store paths in DB anymore
    return {}
