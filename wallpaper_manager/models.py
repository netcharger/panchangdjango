"""
Models for Wallpaper Manager App
"""
import os
from django.db import models
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse
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
            image_path = self.image.path
            
            # Convert to WebP and optimize if it's not already WebP
            _, ext = os.path.splitext(image_path)
            if ext.lower() != '.webp':
                webp_file = convert_and_optimize_uploaded_image(self.image, image_path, quality=88)
                if webp_file:
                    self.image.save(webp_file.name, webp_file, save=True)
                    # Update image_path after conversion
                    image_path = self.image.path
                
                # Delete old non-WebP file if it exists and is different
                if old_image and old_image.path != image_path and os.path.exists(old_image.path) and os.path.splitext(old_image.name)[1].lower() != '.webp':
                    try:
                        os.remove(old_image.path)
                    except Exception as e:
                        print(f"Error deleting old non-WebP category image file {old_image.path}: {e}")
            
            # Delete old size folders if image changed
            if old_image and old_image.name != self.image.name and os.path.exists(old_image.path):
                old_filename = os.path.basename(old_image.path)
                old_base_dir = os.path.dirname(old_image.path)
                from django.conf import settings
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                    if os.path.exists(old_size_path):
                        try:
                            os.remove(old_size_path)
                        except Exception as e:
                            print(f"Error deleting old size file {old_size_path}: {e}")
            
            # Create all image sizes (thumb, medium, large) - saved on disk only
            if os.path.exists(self.image.path):
                from django.conf import settings
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
        
        from django.conf import settings
        if size not in settings.IMAGE_SIZES:
            return self.image.url
        
        # Construct URL for the size variant
        image_name = os.path.basename(self.image.name)
        image_dir = os.path.dirname(self.image.name)
        size_url = f"{image_dir}/{size}/{image_name}"
        
        from django.conf import settings
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
            image_path = self.image.path
            
            # Calculate hash for duplicate detection
            if os.path.exists(image_path):
                self.image_hash = calculate_image_hash(image_path)
                # Save again to store the hash
                super().save(update_fields=['image_hash'])
            
            # Convert to JPG and optimize if it's not already JPG
            _, ext = os.path.splitext(image_path)
            if ext.lower() not in ['.jpg', '.jpeg']:
                jpg_file = convert_and_optimize_to_jpg(self.image, image_path, quality=88)
                if jpg_file:
                    self.image.save(jpg_file.name, jpg_file, save=True)
                    # Update image_path after conversion
                    image_path = self.image.path
                
                # Delete old non-JPG file if it exists and is different
                if old_image and old_image.path != image_path and os.path.exists(old_image.path) and os.path.splitext(old_image.name)[1].lower() not in ['.jpg', '.jpeg']:
                    try:
                        os.remove(old_image.path)
                    except Exception as e:
                        print(f"Error deleting old non-JPG wallpaper image file {old_image.path}: {e}")
            
            # Delete old size folders if image changed
            if old_image and old_image.name != self.image.name and os.path.exists(old_image.path):
                old_filename = os.path.basename(old_image.path)
                old_base_dir = os.path.dirname(old_image.path)
                from django.conf import settings
                for size_name in settings.IMAGE_SIZES.keys():
                    old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                    if os.path.exists(old_size_path):
                        try:
                            os.remove(old_size_path)
                        except Exception as e:
                            print(f"Error deleting old size file {old_size_path}: {e}")
            
            # Create all image sizes (thumb, medium, large) as WebP - saved on disk only
            if os.path.exists(self.image.path):
                from django.conf import settings
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
        
        from django.conf import settings
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
        
        from django.conf import settings
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
