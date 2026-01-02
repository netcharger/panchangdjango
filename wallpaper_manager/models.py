"""
Models for Wallpaper Manager App
"""
import os
import logging
from django.db import models
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse
from django.core.files.storage import default_storage # Import default_storage
from django.conf import settings # Import settings

logger = logging.getLogger(__name__)
from .utils import (
    wallpaper_image_upload_to,
    category_image_upload_to,
    convert_and_optimize_to_jpg,
    convert_and_optimize_uploaded_image,
    create_image_sizes,
    calculate_image_hash,
)


class Category(models.Model):
    """Hierarchical category for wallpapers (like audio_manager)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', help_text="Parent category (null for main categories)")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=category_image_upload_to, blank=True, null=True, help_text="Category thumbnail image")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def get_full_path(self):
        """Get full hierarchical path like audio_manager"""
        if self.parent:
            return f"{self.parent.name} --> {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        # Ensure target directory exists for local storage
        if settings.MEDIA_ROOT:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "wallpaper_categories"), exist_ok=True)

        if not self.slug:
            self.slug = slugify(self.name)

        # Handle image conversion to WebP and old image deletion
        old_image = None
        if self.pk:
            try:
                old_instance = Category.objects.get(pk=self.pk)
                old_image = old_instance.image
            except Category.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Process image after save
        if self.image:
            image_name = self.image.name
            image_path = self.image.path # This still relies on .path being local.

            # Convert to WebP and optimize if it's not already WebP
            _, ext = os.path.splitext(image_name)
            if ext.lower() != '.webp':
                webp_file = convert_and_optimize_uploaded_image(self.image, image_path, quality=88)
                if webp_file:
                    self.image.save(webp_file.name, webp_file, save=True)
                    image_name = self.image.name # Update image_name after conversion

                # Delete old non-WebP file if it exists and is different and storage is the same
                if old_image and old_image.name != image_name and default_storage.exists(old_image.name) and os.path.splitext(old_image.name)[1].lower() != '.webp' and old_image.storage == self.image.storage:
                    try:
                        default_storage.delete(old_image.name)
                    except Exception as e:
                        print(f"Error deleting old non-WebP category image file {old_image.name}: {e}")

            # Delete old size folders if image changed and storage is the same
            if old_image and old_image.name != self.image.name and old_image.storage == self.image.storage:
                old_filename_base = os.path.splitext(os.path.basename(old_image.name))[0]
                old_image_dir = os.path.dirname(old_image.name)
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_name = f"{old_image_dir}/{size_name}/{old_filename_base}.webp" # Size variants are WebP
                    if default_storage.exists(old_size_name):
                        try:
                            default_storage.delete(old_size_name)
                        except Exception as e:
                            print(f"Error deleting old size file {old_size_name}: {e}")

            # Create all image sizes (thumb, medium, large) - saved on disk only
            if default_storage.exists(self.image.name):
                create_image_sizes(self.image, self.image.path, settings.MEDIA_ROOT)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('wallpaper_category_detail', kwargs={'slug': self.slug})

    def get_image_url(self, size=None):
        """
        Get URL for the category image in specified size.
        Available sizes: 'thumb', 'medium', 'large'
        If size is None, returns original image URL.
        """
        if not self.image:
            return None

        if size is None:
            return self.image.url

        if size not in settings.IMAGE_SIZES:
            return self.image.url

        # Construct URL for the size variant
        image_name = os.path.basename(self.image.name)
        image_dir = os.path.dirname(self.image.name)
        size_url = f"{image_dir}/{size}/{image_name}"

        return f"{settings.MEDIA_URL}{size_url}"

    def get_thumb_url(self):
        """Get thumbnail URL (200px width)"""
        return self.get_image_url('thumb')

    def get_medium_url(self):
        """Get medium size URL (600px width)"""
        return self.get_image_url('medium')

    def get_large_url(self):
        """Get large size URL (800px width)"""
        return self.get_image_url('large')

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        logger.info(f"[Category.delete_image_files] Starting deletion for Category ID: {self.pk}, Name: {self.name}")

        # Store image name before any operations that might clear it
        image_name = None
        if self.image:
            try:
                image_name = self.image.name
                logger.info(f"[Category.delete_image_files] Image found: {image_name}")
            except (AttributeError, ValueError) as e:
                logger.warning(f"[Category.delete_image_files] Could not get image name: {e}")
                pass
        else:
            logger.info(f"[Category.delete_image_files] No image field set for Category ID: {self.pk}")

        if image_name:
            if default_storage.exists(image_name):
                try:
                    default_storage.delete(image_name)
                    logger.info(f"[Category.delete_image_files] ✓ Deleted original category image file: {image_name}")
                except Exception as e:
                    logger.error(f"[Category.delete_image_files] ✗ Error deleting original category image file {image_name}: {e}")
            else:
                logger.warning(f"[Category.delete_image_files] Image file does not exist in storage: {image_name}")

            # Delete all size variants
            image_name_base = os.path.splitext(os.path.basename(image_name))[0]
            image_dir = os.path.dirname(image_name)
            logger.info(f"[Category.delete_image_files] Looking for size variants in: {image_dir}, base name: {image_name_base}")

            for size_name in settings.IMAGE_SIZES.keys():
                size_variant_name = f"{image_dir}/{size_name}/{image_name_base}.webp"
                if default_storage.exists(size_variant_name):
                    try:
                        default_storage.delete(size_variant_name)
                        logger.info(f"[Category.delete_image_files] ✓ Deleted size file: {size_variant_name}")
                    except Exception as e:
                        logger.error(f"[Category.delete_image_files] ✗ Error deleting size file {size_variant_name}: {e}")
                else:
                    logger.debug(f"[Category.delete_image_files] Size variant does not exist: {size_variant_name}")

        # Also try using ImageField's delete method as a fallback
        if self.image:
            try:
                self.image.delete(save=False)
                logger.info(f"[Category.delete_image_files] ✓ Used ImageField.delete() as fallback")
            except Exception as e:
                logger.warning(f"[Category.delete_image_files] ImageField.delete() failed: {e}")

    def delete(self, *args, **kwargs):
        """Delete associated image files before deleting the model instance"""
        logger.info(f"[Category.delete] Starting deletion for Category ID: {self.pk}, Name: {self.name}")
        # Delete image files BEFORE calling super().delete()
        # This ensures we have access to self.image before Django clears it
        self.delete_image_files()
        super().delete(*args, **kwargs)
        logger.info(f"[Category.delete] ✓ Completed deletion for Category ID: {self.pk}")




class Wallpaper(models.Model):
    """Wallpaper model - requires a category (subcategory is a category with parent)"""
    title = models.CharField(max_length=200, blank=True, help_text="Optional title for the wallpaper")
    image = models.ImageField(upload_to=wallpaper_image_upload_to, help_text="Wallpaper image file")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='wallpapers', help_text="Category (must be a subcategory - category with parent)")
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash for duplicate detection")
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0, help_text="Number of times viewed")
    download_count = models.PositiveIntegerField(default=0, help_text="Number of times downloaded")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Ensure target directory exists for local storage
        if settings.MEDIA_ROOT:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "wallpapers"), exist_ok=True)

        # Validate that category is set and it's a subcategory (has parent)
        if not self.category:
            raise ValueError("Category is required for wallpaper")

        # Ensure category is a subcategory (has a parent)
        if not self.category.parent:
            raise ValueError(f"Category '{self.category.name}' must be a subcategory (must have a parent category)")

        # Handle old image deletion
        old_image = None
        if self.pk:
            try:
                old_instance = Wallpaper.objects.get(pk=self.pk)
                old_image = old_instance.image
            except Wallpaper.DoesNotExist:
                pass

        # Process image after save
        super().save(*args, **kwargs)

        if self.image:
            image_name = self.image.name
            image_path = self.image.path # This still relies on .path being local.

            # Calculate hash for duplicate detection
            if default_storage.exists(image_name):
                self.image_hash = calculate_image_hash(image_path)
                # Save again to store the hash
                super().save(update_fields=['image_hash'])

            # Convert to JPG and optimize if it's not already JPG
            _, ext = os.path.splitext(image_name)
            if ext.lower() not in ['.jpg', '.jpeg']:
                jpg_file = convert_and_optimize_to_jpg(self.image, image_path, quality=88)
                if jpg_file:
                    self.image.save(jpg_file.name, jpg_file, save=True)
                    image_name = self.image.name # Update image_name after conversion

                # Delete old non-JPG file if it exists and is different and storage is the same
                if old_image and old_image.name != image_name and default_storage.exists(old_image.name) and os.path.splitext(old_image.name)[1].lower() not in ['.jpg', '.jpeg'] and old_image.storage == self.image.storage:
                    try:
                        default_storage.delete(old_image.name)
                    except Exception as e:
                        print(f"Error deleting old non-JPG wallpaper image file {old_image.name}: {e}")

            # Delete old size folders if image changed and storage is the same
            if old_image and old_image.name != self.image.name and old_image.storage == self.image.storage:
                old_filename_base = os.path.splitext(os.path.basename(old_image.name))[0]
                old_image_dir = os.path.dirname(old_image.name)
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_name = f"{old_image_dir}/{size_name}/{old_filename_base}.webp" # Size variants are WebP
                    if default_storage.exists(old_size_name):
                        try:
                            default_storage.delete(old_size_name)
                        except Exception as e:
                            print(f"Error deleting old size file {old_size_name}: {e}")

            # Create all image sizes (thumb, medium, large) as WebP - saved on disk only
            if default_storage.exists(self.image.name):
                create_image_sizes(self.image, self.image.path, settings.MEDIA_ROOT)

    def __str__(self):
        if self.title:
            return self.title
        return f"Wallpaper {self.id}"

    def get_absolute_url(self):
        return reverse('wallpaper_detail', kwargs={'pk': self.pk})

    def image_preview(self):
        """Admin preview of the image"""
        if self.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', self.image.url)
        return "No image"
    image_preview.short_description = "Preview"

    def get_image_url(self, size=None):
        """
        Get URL for the image in specified size.
        Available sizes: 'thumb', 'medium', 'large'
        If size is None, returns original image URL (JPG).
        Size variants are saved as WebP format.
        """
        if not self.image:
            return None

        if size is None:
            return self.image.url

        if size not in settings.IMAGE_SIZES:
            return self.image.url

        # Construct URL for the size variant
        # Original: media/wallpapers/image.jpg
        # Size variant: media/wallpapers/{size}/image.webp (WebP format)
        image_name = os.path.basename(self.image.name)
        image_dir = os.path.dirname(self.image.name)
        # Change extension from .jpg to .webp for size variants
        name_without_ext = os.path.splitext(image_name)[0]
        webp_filename = f"{name_without_ext}.webp"
        size_url = f"{image_dir}/{size}/{webp_filename}"

        return f"{settings.MEDIA_URL}{size_url}"

    def get_thumb_url(self):
        """Get thumbnail URL (200px width)"""
        return self.get_image_url('thumb')

    def get_medium_url(self):
        """Get medium size URL (600px width)"""
        return self.get_image_url('medium')

    def get_large_url(self):
        """Get large size URL (800px width)"""
        return self.get_image_url('large')

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        logger.info(f"[Wallpaper.delete_image_files] Starting deletion for Wallpaper ID: {self.pk}, Title: {self.title}")

        # Store image name before any operations that might clear it
        image_name = None
        image_path = None
        if self.image:
            try:
                image_name = self.image.name
                image_path = self.image.path if hasattr(self.image, 'path') else None
                logger.info(f"[Wallpaper.delete_image_files] Image found - name: {image_name}, path: {image_path}")
                logger.info(f"[Wallpaper.delete_image_files] MEDIA_ROOT: {settings.MEDIA_ROOT}")
            except (AttributeError, ValueError) as e:
                logger.warning(f"[Wallpaper.delete_image_files] Could not get image name: {e}")
                pass
        else:
            logger.info(f"[Wallpaper.delete_image_files] No image field set for Wallpaper ID: {self.pk}")

        if image_name:
            # Try deleting using storage first (relative path from MEDIA_ROOT)
            if default_storage.exists(image_name):
                try:
                    default_storage.delete(image_name)
                    logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted original wallpaper image file (via storage): {image_name}")
                except Exception as e:
                    logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting via storage {image_name}: {e}")
            else:
                logger.warning(f"[Wallpaper.delete_image_files] Image file does not exist in storage: {image_name}")

            # Also try direct file path deletion if available (for local storage)
            # Try image_path first (if available)
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted original wallpaper image file (via os.remove): {image_path}")
                except Exception as e:
                    logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting via os.remove {image_path}: {e}")
            # Fallback: construct path from MEDIA_ROOT + image_name
            elif settings.MEDIA_ROOT:
                full_path = os.path.join(settings.MEDIA_ROOT, image_name)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted original wallpaper image file (via os.remove with MEDIA_ROOT): {full_path}")
                    except Exception as e:
                        logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting via os.remove {full_path}: {e}")

            # Delete all size variants
            image_name_base = os.path.splitext(os.path.basename(image_name))[0]
            image_dir = os.path.dirname(image_name)
            logger.info(f"[Wallpaper.delete_image_files] Looking for size variants in: {image_dir}, base name: {image_name_base}")

            for size_name in settings.IMAGE_SIZES.keys():
                # Try storage path first
                size_variant_name = f"{image_dir}/{size_name}/{image_name_base}.webp"
                if default_storage.exists(size_variant_name):
                    try:
                        default_storage.delete(size_variant_name)
                        logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted size file (via storage): {size_variant_name}")
                    except Exception as e:
                        logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting size file {size_variant_name}: {e}")
                else:
                    logger.debug(f"[Wallpaper.delete_image_files] Size variant does not exist in storage: {size_variant_name}")

                # Also try direct file path deletion
                # Try constructing from image_path first
                if image_path:
                    size_variant_path = os.path.join(os.path.dirname(image_path), size_name, f"{image_name_base}.webp")
                    if os.path.exists(size_variant_path):
                        try:
                            os.remove(size_variant_path)
                            logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted size file (via os.remove): {size_variant_path}")
                        except Exception as e:
                            logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting size file via os.remove {size_variant_path}: {e}")
                # Fallback: construct from MEDIA_ROOT + size_variant_name
                elif settings.MEDIA_ROOT:
                    size_variant_full_path = os.path.join(settings.MEDIA_ROOT, size_variant_name)
                    if os.path.exists(size_variant_full_path):
                        try:
                            os.remove(size_variant_full_path)
                            logger.info(f"[Wallpaper.delete_image_files] ✓ Deleted size file (via os.remove with MEDIA_ROOT): {size_variant_full_path}")
                        except Exception as e:
                            logger.error(f"[Wallpaper.delete_image_files] ✗ Error deleting size file via os.remove {size_variant_full_path}: {e}")

        # Also try using ImageField's delete method as a fallback
        if self.image:
            try:
                self.image.delete(save=False)
                logger.info(f"[Wallpaper.delete_image_files] ✓ Used ImageField.delete() as fallback")
            except Exception as e:
                logger.warning(f"[Wallpaper.delete_image_files] ImageField.delete() failed: {e}")

    def delete(self, *args, **kwargs):
        """Delete associated image files before deleting the model instance"""
        logger.info(f"[Wallpaper.delete] Starting deletion for Wallpaper ID: {self.pk}, Title: {self.title}")
        # Delete image files BEFORE calling super().delete()
        # This ensures we have access to self.image before Django clears it
        self.delete_image_files()
        super().delete(*args, **kwargs)
        logger.info(f"[Wallpaper.delete] ✓ Completed deletion for Wallpaper ID: {self.pk}")