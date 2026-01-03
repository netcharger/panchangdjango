import os
from django.utils.text import slugify

def category_image_upload_to(instance, filename):
    """
    Custom upload_to function for category images.
    Preserves original filename, only adds hash if duplicate exists in database.
    """
    # Clean filename but preserve original extension for initial upload
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    original_filename = f"{clean_name}{ext}"
    
    upload_path = f'categories/{original_filename}'
    
    # Check if another category instance is using this filename
    from .models import Category
    existing_category = Category.objects.filter(category_image=upload_path).exclude(pk=instance.pk if instance.pk else None).first()
    
    if existing_category:
        # Another instance is using this filename, add hash to make it unique
        import time
        import hashlib
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        original_filename = f"{clean_name}_{hash_suffix}{ext}"
        upload_path = f'categories/{original_filename}'
    
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
        import hashlib
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
        import hashlib
        hash_suffix = hashlib.md5(f"{filename}{time.time()}{instance.pk if instance.pk else 'new'}".encode()).hexdigest()[:8]
        webp_filename = f"{clean_name}_{hash_suffix}.webp"
        upload_path = f'post_images/{webp_filename}'
    
    return upload_path
