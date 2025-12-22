from django.db import models
from django.conf import settings
import os
from django.core.files import File
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
        if self.image and os.path.exists(self.image.path):
            image_path = self.image.path
            current_hash = calculate_image_hash(image_path)

            # If image changed or no hash, process it
            if old_image != self.image or not self.image_hash or self.image_hash != current_hash:
                self.image_hash = current_hash

                # Convert original image to WebP and optimize
                _, ext = os.path.splitext(image_path)
                if ext.lower() != '.webp':
                    webp_path = convert_and_optimize_uploaded_image(self.image, image_path, quality=88)
                    if webp_path and os.path.exists(webp_path):
                        # Replace original file with WebP version
                        with open(webp_path, 'rb') as f:
                            self.image.save(os.path.basename(webp_path), File(f), save=False)
                        # Delete original non-WebP file if different
                        if webp_path != image_path and os.path.exists(image_path):
                            try:
                                os.remove(image_path)
                            except Exception as e:
                                print(f"Error deleting original image file: {e}")
                        image_path = webp_path
                        # Recalculate hash for WebP version
                        self.image_hash = calculate_image_hash(image_path)

                # Create all image sizes (small, thumb, medium, large) - saved on disk only
                create_image_sizes(self.image, image_path, settings.MEDIA_ROOT)

            # Delete old image and all sizes if replaced
            if old_image and old_image != self.image:
                try:
                    old_image.delete(save=False)
                    # Delete all size folders (small, thumb, medium, large)
                    old_filename = os.path.basename(old_image.path)
                    old_base_dir = os.path.dirname(old_image.path)
                    for size_name in settings.IMAGE_SIZES.keys():
                        old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                        if os.path.exists(old_size_path):
                            os.remove(old_size_path)
                except Exception as e:
                    print(f"Error deleting old image/sizes: {e}")
        elif old_image:
            # If image was removed, delete old image and all sizes
            try:
                old_image.delete(save=False)
                # Delete all size folders (small, thumb, medium, large)
                old_filename = os.path.basename(old_image.path)
                old_base_dir = os.path.dirname(old_image.path)
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                    if os.path.exists(old_size_path):
                        os.remove(old_size_path)
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

        super().save(*args, **kwargs)
        self._process_image(old_image)
        super().save(update_fields=['image_hash'])

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        if self.image:
            original_path = self.image.path
            if os.path.exists(original_path):
                try:
                    os.remove(original_path)
                    print(f"Deleted original carousel image file: {original_path}")
                except Exception as e:
                    print(f"Error deleting original carousel image file {original_path}: {e}")

            # Delete all size folders (thumb, medium, large)
            base_dir = os.path.dirname(original_path)
            original_filename = os.path.basename(original_path)

            for size_name in settings.IMAGE_SIZES.keys():
                size_dir = os.path.join(base_dir, size_name)
                size_path = os.path.join(size_dir, original_filename)
                if os.path.exists(size_path):
                    try:
                        os.remove(size_path)
                        print(f"Deleted size file: {size_path}")
                    except Exception as e:
                        print(f"Error deleting size file {size_path}: {e}")

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
        """Process image: convert to WebP and create sizes"""
        if self.image_value and os.path.exists(self.image_value.path):
            image_path = self.image_value.path

            # Convert original image to WebP and optimize
            _, ext = os.path.splitext(image_path)
            if ext.lower() != '.webp':
                webp_path = convert_and_optimize_uploaded_image(self.image_value, image_path, quality=88)
                if webp_path and os.path.exists(webp_path):
                    # Replace original file with WebP version
                    with open(webp_path, 'rb') as f:
                        self.image_value.save(os.path.basename(webp_path), File(f), save=False)
                    # Delete original non-WebP file if different
                    if webp_path != image_path and os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"Error deleting original image file: {e}")
                    image_path = webp_path

            # Create all image sizes (small, thumb, medium, large) - saved on disk only
            create_image_sizes(self.image_value, image_path, settings.MEDIA_ROOT)

        # Delete old image and all sizes if replaced
        if old_image and old_image != self.image_value:
            try:
                old_image.delete(save=False)
                # Delete all size folders (small, thumb, medium, large)
                old_filename = os.path.basename(old_image.path)
                old_base_dir = os.path.dirname(old_image.path)
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                    if os.path.exists(old_size_path):
                        os.remove(old_size_path)
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

        super().save(*args, **kwargs)

        # Process image if one is provided
        if self.image_value:
            self._process_image(old_image)

    def delete_image_files(self):
        """Delete the image file and all its size variants"""
        if self.pk:
            try:
                old_instance = SiteSetting.objects.get(pk=self.pk)
                if old_instance.image_value:
                    original_path = old_instance.image_value.path
                    if os.path.exists(original_path):
                        try:
                            os.remove(original_path)
                        except Exception as e:
                            print(f"Error deleting original site setting image file {original_path}: {e}")

                    # Delete all size folders (thumb, medium, large)
                    base_dir = os.path.dirname(original_path)
                    original_filename = os.path.basename(original_path)

                    for size_name in settings.IMAGE_SIZES.keys():
                        size_dir = os.path.join(base_dir, size_name)
                        size_path = os.path.join(size_dir, original_filename)
                        if os.path.exists(size_path):
                            try:
                                os.remove(size_path)
                            except Exception as e:
                                print(f"Error deleting size file {size_path}: {e}")
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