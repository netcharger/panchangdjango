import os
from celery import shared_task
from django.conf import settings
from django.core.files import File

from .utils import calculate_image_hash, convert_and_optimize_uploaded_image, create_image_sizes, find_duplicate_image


@shared_task
def process_festival_image_task(instance_pk, model_name, old_image_path=None):
    # Local import to avoid circular dependency
    from .models import Festival, ImportantDay, FestivalGallery, ImportantDayGallery

    try:
        if model_name == 'Festival':
            instance = Festival.objects.get(pk=instance_pk)
            image_field = instance.image
            image_hash_field = 'image_hash'
        elif model_name == 'ImportantDay':
            instance = ImportantDay.objects.get(pk=instance_pk)
            image_field = instance.image
            image_hash_field = 'image_hash'
        elif model_name == 'FestivalGallery':
            instance = FestivalGallery.objects.get(pk=instance_pk)
            image_field = instance.image
            image_hash_field = 'image_hash'
        elif model_name == 'ImportantDayGallery':
            instance = ImportantDayGallery.objects.get(pk=instance_pk)
            image_field = instance.image
            image_hash_field = 'image_hash'
        else:
            return

        if not image_field or not hasattr(image_field, 'path') or not os.path.exists(image_field.path):
            # If no image or image file does not exist, delete old sizes if they exist and return
            if old_image_path and os.path.exists(old_image_path):
                try:
                    old_filename = os.path.basename(old_image_path)
                    old_base_dir = os.path.dirname(old_image_path)
                    for size_name in settings.IMAGE_SIZES.keys():
                        old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                        if os.path.exists(old_size_path):
                            os.remove(old_size_path)
                except Exception as e:
                    print(f"Error deleting old image/sizes on removal: {e}")
            
            # Clear hash field on instance and save
            setattr(instance, image_hash_field, '')
            instance.save(update_fields=[image_hash_field])
            return

        image_path = image_field.path
        current_hash = calculate_image_hash(image_path)

        # If old_image_path is provided, and it's different from the current image_path,
        # then a new image has been uploaded or an old one removed. We need to re-process.
        # Also, re-process if hashes don't match or no hash exists.
        re_process = False
        if old_image_path and os.path.exists(old_image_path) and old_image_path != image_path:
            re_process = True
            # Delete old image and all sizes
            try:
                old_filename = os.path.basename(old_image_path)
                old_base_dir = os.path.dirname(old_image_path)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                    if os.path.exists(old_size_path):
                        os.remove(old_size_path)
            except Exception as e:
                print(f"Error deleting old image/sizes: {e}")

        if not getattr(instance, image_hash_field) or getattr(instance, image_hash_field) != current_hash:
            re_process = True
        
        if re_process:
            setattr(instance, image_hash_field, current_hash)

            # Check for duplicate images across all models
            duplicate_info = find_duplicate_image(current_hash, instance.__class__, exclude_pk=instance.pk)
            if duplicate_info:
                # Duplicate found - reuse existing image
                setattr(instance, 'image', duplicate_info['image'])
                # Delete the newly uploaded duplicate file
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting newly uploaded duplicate image file: {e}")
            else:
                # No duplicate found, process normally
                _, ext = os.path.splitext(image_path)
                if ext.lower() != '.webp':
                    webp_path = convert_and_optimize_uploaded_image(image_field, image_path, quality=88)
                    if webp_path and os.path.exists(webp_path):
                        with open(webp_path, 'rb') as f:
                            image_field.save(os.path.basename(webp_path), File(f), save=False)
                        if webp_path != image_path and os.path.exists(image_path):
                            try:
                                os.remove(image_path)
                            except Exception as e:
                                print(f"Error deleting original image file: {e}")
                        image_path = webp_path
                        setattr(instance, image_hash_field, calculate_image_hash(image_path))

                # Create all image sizes (small, thumb, medium, large) - saved on disk only
                create_image_sizes(image_field, image_path, settings.MEDIA_ROOT)
            
            instance.save(update_fields=[image_hash_field])

    except Exception as e:
        print(f"Error processing image for {model_name} (PK: {instance_pk}): {e}")


@shared_task
def delete_related_images_task(image_path):
    # Local import to avoid circular dependency
    from .models import Festival, ImportantDay, FestivalGallery, ImportantDayGallery

    # Ensure we only delete if this is a relative path, not full URL
    if image_path and not image_path.startswith('http'):
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                print(f"Error deleting main image: {e}")
            
            # Delete all size folders (small, thumb, medium, large)
            image_filename = os.path.basename(full_path)
            base_dir = os.path.dirname(full_path)
            for size_name in settings.IMAGE_SIZES.keys():
                size_path = os.path.join(base_dir, size_name, image_filename)
                if os.path.exists(size_path):
                    try:
                        os.remove(size_path)
                    except Exception as e:
                        print(f"Error deleting {size_name} image: {e}")
                    # Also try to remove the directory if it's empty
                    size_dir = os.path.dirname(size_path)
                    if os.path.exists(size_dir) and not os.listdir(size_dir):
                        try:
                            os.rmdir(size_dir)
                        except Exception as e:
                            print(f"Error deleting empty {size_name} directory: {e}")
