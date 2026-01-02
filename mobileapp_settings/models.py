from django.db import models
from django.conf import settings
import os
from django.core.files import File
from django.core.files.storage import default_storage # Import default_storage
from panchang.utils import (
    carousel_image_upload_path,
    convert_and_optimize_uploaded_image,
    calculate_image_hash,
    create_image_sizes,
    site_setting_image_upload_path
)

class CarouselImage(models.Model):
    heading = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=carousel_image_upload_path)
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    link = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="The order in which the image should be displayed.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = "Carousel Images"

    def _process_image(self, old_image):
        # Ensure target directory exists for all images
        # This is for local storage. For remote, storage backends usually handle this.
        if settings.MEDIA_ROOT: # Only if MEDIA_ROOT is defined (i.e. local storage)
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "carousel_images"), exist_ok=True)

        if self.image and default_storage.exists(self.image.name):
            # For hash calculation, we temporarily need a local path if using remote storage
            # This is a limitation if calculate_image_hash doesn't support file-like objects
            # For now, we proceed assuming self.image.path is accessible locally.
            image_path = self.image.path
            image_name = self.image.name
            current_hash = calculate_image_hash(image_path)

            # If image changed or no hash, process it
            if old_image != self.image or not self.image_hash or self.image_hash != current_hash:
                self.image_hash = current_hash

                # Convert original image to WebP and optimize
                _, ext = os.path.splitext(image_name)
                if ext.lower() != '.webp':
                    webp_file = convert_and_optimize_uploaded_image(self.image, image_path, quality=88)
                    if webp_file: # webp_file is a File object, check if it was created
                        # Replace original file with WebP version. This will also update self.image.name
                        self.image.save(webp_file.name, webp_file, save=False) # save=False as it's part of main model save

                        # Delete original non-WebP file if different and exists in storage
                        if old_image and old_image.name != self.image.name and default_storage.exists(old_image.name):
                            default_storage.delete(old_image.name)

                        # Recalculate hash for WebP version
                        if default_storage.exists(self.image.name): # Check if the new image exists in storage
                             self.image_hash = calculate_image_hash(self.image.path) # Still relies on .path being local

                # Create all image sizes (small, thumb, medium, large) - saved on disk only
                # create_image_sizes handles saving to disk based on MEDIA_ROOT
                if default_storage.exists(self.image.name):
                    create_image_sizes(self.image, self.image.path, settings.MEDIA_ROOT)

            # Delete old image and all sizes if replaced and storage is the same
            if old_image and old_image.name != self.image.name and old_image.storage == self.image.storage:
                try:
                    # Delete the original old image
                    if default_storage.exists(old_image.name):
                        default_storage.delete(old_image.name)

                    # Delete all size variants of the old image
                    old_filename_base = os.path.splitext(os.path.basename(old_image.name))[0]
                    old_image_dir = os.path.dirname(old_image.name) # e.g., 'carousel_images'

                    for size_name in settings.IMAGE_SIZES.keys():
                        old_size_name = f"{old_image_dir}/{size_name}/{old_filename_base}.webp" # Size variants are WebP
                        if default_storage.exists(old_size_name):
                            default_storage.delete(old_size_name)
                except Exception as e:
                    print(f"Error deleting old image/sizes: {e}")
        elif old_image and not self.image: # If image was removed entirely
            try:
                # Delete the original old image
                if default_storage.exists(old_image.name):
                    default_storage.delete(old_image.name)

                old_filename_base = os.path.splitext(os.path.basename(old_image.name))[0]
                old_image_dir = os.path.dirname(old_image.name)

                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_name = f"{old_image_dir}/{size_name}/{old_filename_base}.webp"
                    if default_storage.exists(old_size_name):
                        default_storage.delete(old_size_name)
            except Exception as e:
                print(f"Error deleting old image/sizes on removal: {e}")

    def save(self, *args, **kwargs):
        old_image = None
        if self.pk:
            try:
                old_instance = CarouselImage.objects.get(pk=self.pk)
                old_image = old_instance.image
            except CarouselImage.DoesNotExist:
                pass

        # Ensure the media root directory exists before Django tries to save anything
        if settings.MEDIA_ROOT and not os.path.exists(settings.MEDIA_ROOT):
             os.makedirs(settings.MEDIA_ROOT, exist_ok=True)


        super().save(*args, **kwargs)
        self._process_image(old_image)
        super().save(update_fields=['image_hash'])

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        if self.image and default_storage.exists(self.image.name):
            try:
                default_storage.delete(self.image.name) # Delete original image
                print(f"Deleted original carousel image file: {self.image.name}")
            except Exception as e:
                print(f"Error deleting original carousel image file {self.image.name}: {e}")

            # Delete all size variants
            image_name_base = os.path.splitext(os.path.basename(self.image.name))[0]
            image_dir = os.path.dirname(self.image.name)

            for size_name in settings.IMAGE_SIZES.keys():
                size_variant_name = f"{image_dir}/{size_name}/{image_name_base}.webp"
                if default_storage.exists(size_variant_name):
                    try:
                        default_storage.delete(size_variant_name)
                        print(f"Deleted size file: {size_variant_name}")
                    except Exception as e:
                        print(f"Error deleting size file {size_variant_name}: {e}")

    def delete(self, *args, **kwargs):
        """Delete associated image files before deleting the model instance"""
        self.delete_image_files()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.heading


class SiteSetting(models.Model):
    """
    Flexible site settings model that stores key-value pairs with different types.
    Allows adding new settings without modifying the model structure.
    """
    VALUE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('url', 'URL'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
    ]

    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for this setting (e.g., 'site_title', 'hero_image')"
    )
    value_type = models.CharField(
        max_length=50,
        choices=VALUE_TYPE_CHOICES,
        default='text',
        help_text='Type of value stored in this setting'
    )

    # Value fields - only one should be populated based on value_type
    text_value = models.TextField(blank=True, null=True, help_text="Text value")
    image_value = models.ImageField(
        upload_to=site_setting_image_upload_path,
        blank=True,
        null=True,
        help_text="Image value"
    )
    number_value = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        blank=True,
        null=True,
        help_text="Numeric value"
    )
    boolean_value = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        help_text="Boolean value"
    )
    url_value = models.URLField(blank=True, null=True, help_text="URL value")

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description or help text for this setting"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this setting is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Site Settings"

    def get_value(self):
        """Return the appropriate value based on value_type"""
        if self.text_value:
            return self.text_value
        elif self.image_value:
            return self.image_value.url if self.image_value else None
        elif self.url_value:
            return self.url_value
        return None

    def set_value(self, value, value_type=None):
        """Set the appropriate value field based on value_type"""
        # This method might need to be re-evaluated if there's no single 'value_type'
        # For now, we'll try to set the most appropriate field.
        if value_type == 'text':
            self.text_value = str(value) if value is not None else None
        elif value_type == 'image':
            self.image_value = value
        elif value_type == 'url':
            self.url_value = str(value) if value is not None else None
        # If no specific type is given, try to infer or set text
        else:
            self.text_value = str(value) if value is not None else None

    def _process_image(self, old_image):
        # Ensure target directory exists for all images
        if settings.MEDIA_ROOT: # Only if MEDIA_ROOT is defined (i.e. local storage)
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "site_settings"), exist_ok=True) # Assuming 'site_settings' is the upload_to for this.

        if self.image_value and default_storage.exists(self.image_value.name):
            image_path = self.image_value.path
            image_name = self.image_value.name

            # Convert original image to WebP and optimize
            _, ext = os.path.splitext(image_name)
            if ext.lower() != '.webp':
                webp_file = convert_and_optimize_uploaded_image(self.image_value, image_path, quality=88)
                if webp_file: # webp_file is a File object
                    self.image_value.save(webp_file.name, webp_file, save=False)

                    if old_image and old_image.name != self.image_value.name and default_storage.exists(old_image.name):
                        default_storage.delete(old_image.name)
                    image_name = self.image_value.name # Update image_name after save

            # Create all image sizes (small, thumb, medium, large) - saved on disk only
            if default_storage.exists(self.image_value.name):
                create_image_sizes(self.image_value, self.image_value.path, settings.MEDIA_ROOT)

        # Delete old image and all sizes if replaced and storage is the same
        if old_image and old_image.name != self.image_value.name and old_image.storage == self.image_value.storage:
            try:
                if default_storage.exists(old_image.name):
                    default_storage.delete(old_image.name)

                old_filename_base = os.path.splitext(os.path.basename(old_image.name))[0]
                old_image_dir = os.path.dirname(old_image.name)

                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_name = f"{old_image_dir}/{size_name}/{old_filename_base}.webp"
                    if default_storage.exists(old_size_name):
                        default_storage.delete(old_size_name)
            except Exception as e:
                print(f"Error deleting old image/sizes: {e}")

    def save(self, *args, **kwargs):
        """Override save to process images"""
        old_image = None
        if self.pk:
            try:
                old_instance = SiteSetting.objects.get(pk=self.pk)
                old_image = old_instance.image_value
            except SiteSetting.DoesNotExist:
                pass

        # Ensure the media root directory exists before Django tries to save anything
        if settings.MEDIA_ROOT and not os.path.exists(settings.MEDIA_ROOT):
             os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        super().save(*args, **kwargs)

        # Process image if one is provided
        if self.image_value:
            self._process_image(old_image)

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        if self.pk:
            try:
                old_instance = SiteSetting.objects.get(pk=self.pk)
                if old_instance.image_value and default_storage.exists(old_instance.image_value.name):
                    try:
                        default_storage.delete(old_instance.image_value.name)
                        print(f"Deleted original site setting image file: {old_instance.image_value.name}")
                    except Exception as e:
                        print(f"Error deleting original site setting image file {old_instance.image_value.name}: {e}")

                    # Delete all size variants
                    image_name_base = os.path.splitext(os.path.basename(old_instance.image_value.name))[0]
                    image_dir = os.path.dirname(old_instance.image_value.name)

                    for size_name in settings.IMAGE_SIZES.keys():
                        size_variant_name = f"{image_dir}/{size_name}/{image_name_base}.webp"
                        if default_storage.exists(size_variant_name):
                            try:
                                default_storage.delete(size_variant_name)
                                print(f"Deleted size file: {size_variant_name}")
                            except Exception as e:
                                print(f"Error deleting size file {size_variant_name}: {e}")
            except SiteSetting.DoesNotExist:
                pass

    def delete(self, *args, **kwargs):
        """Delete associated image files before deleting the model instance"""
        self.delete_image_files()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.key}: {self.value}"

    @property
    def value(self):
        """Expose the currently active setting value (used by admin/model repr)."""
        return self.get_value()
        return f"{self.key}: {self.value}"