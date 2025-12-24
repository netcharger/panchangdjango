from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model
from django.urls import reverse
from ckeditor.fields import RichTextField
from django.conf import settings
from django.core.files import File
import os
from django.utils.html import format_html

from .utils import (
    calculate_image_hash, 
    convert_and_optimize_uploaded_image, 
    create_image_sizes,
    category_image_upload_to,
    post_image_upload_to,
    post_gallery_image_upload_to
)

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    category_image = models.ImageField(upload_to=category_image_upload_to, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="The order in which the category should be displayed.")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def _process_category_image(self, old_image):
        # This method is called during save, before super().save() is called for the second time.
        # self.category_image will be the newly uploaded file or the existing one.
        # old_image is the image that was present before the current save operation.

        if self.category_image:
            image_path = self.category_image.path
            
            # Convert to WebP and optimize if it's not already WebP
            _, ext = os.path.splitext(image_path)
            if ext.lower() != '.webp':
                webp_path = convert_and_optimize_uploaded_image(self.category_image, image_path, quality=88)
                if webp_path and os.path.exists(webp_path):
                    # At this point, self.category_image.name has been updated to the .webp filename
                    # and the .webp file is in the temporary location.
                    # The original non-webp file might still be there on disk if its a new upload or old image.

                    # If a new image was uploaded and converted, or an old one was converted:
                    # Delete the original non-WebP file if it was different and existed.
                    # This applies if an existing JPG was replaced by a new WebP, or if a new JPG was uploaded and converted.
                    if old_image and old_image.path != webp_path and os.path.exists(old_image.path) and os.path.splitext(old_image.name)[1].lower() != '.webp':
                        try:
                            os.remove(old_image.path)
                            print(f"Deleted old non-WebP category image file: {old_image.path}")
                        except Exception as e:
                            print(f"Error deleting old non-WebP category image file {old_image.path}: {e}")
                    
                    # Also delete old sizes if they existed before this save and the image itself changed.
                    if old_image and old_image.name != self.category_image.name:
                        # Delete all size folders (small, thumb, medium, large)
                        old_filename = os.path.basename(old_image.path)
                        old_base_dir = os.path.dirname(old_image.path)
                        for size_name in settings.IMAGE_SIZES.keys():
                            old_size_path = os.path.join(old_base_dir, size_name, old_filename)
                            if os.path.exists(old_size_path):
                                try:
                                    os.remove(old_size_path)
                                    print(f"Deleted old size file: {old_size_path}")
                                except Exception as e:
                                    print(f"Error deleting old size file {old_size_path}: {e}")

            # Create all image sizes (small, thumb, medium, large) - saved on disk only
            create_image_sizes(self.category_image, self.category_image.path, settings.MEDIA_ROOT)

        elif old_image: # If category_image was cleared
            self.delete_category_image_files()


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        old_category_image = None
        if self.pk:
            try:
                old_instance = Category.objects.get(pk=self.pk)
                old_category_image = old_instance.category_image
            except Category.DoesNotExist:
                pass

        # Process the image before the initial save, so self.category_image has the correct WebP file
        self._process_category_image(old_category_image)

        super().save(*args, **kwargs) # This save will now correctly store the .webp path if converted

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Get full hierarchical path like 'Parent > Child'"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('posts:category-detail', kwargs={'slug': self.slug})

    def delete_category_image_files(self):
        """Delete the category image file and all its size variants"""
        if self.category_image:
            try:
                # Get the path and filename before deletion
                # Wrap in try-except in case path is not accessible
                try:
                    original_path = self.category_image.path
                    base_dir = os.path.dirname(original_path)
                    original_filename = os.path.basename(original_path)
                    
                    # Delete all size folders (thumb, medium, large) first
                    for size_name in settings.IMAGE_SIZES.keys():
                        size_dir = os.path.join(base_dir, size_name)
                        size_path = os.path.join(size_dir, original_filename)
                        if os.path.exists(size_path):
                            try:
                                os.remove(size_path)
                                print(f"Deleted size file: {size_path}")
                            except Exception as e:
                                print(f"Error deleting size file {size_path}: {e}")
                    
                    # Delete the original image file
                    if os.path.exists(original_path):
                        try:
                            os.remove(original_path)
                            print(f"Deleted original category image file: {original_path}")
                        except Exception as e:
                            print(f"Error deleting original category image file {original_path}: {e}")
                except Exception as path_error:
                    print(f"Could not access image path, trying ImageField delete method: {path_error}")
                
                # Always try to use ImageField's delete method to ensure proper cleanup
                # This handles storage backends properly
                try:
                    self.category_image.delete(save=False)
                except Exception as e:
                    print(f"Error using ImageField delete method: {e}")
            except Exception as e:
                print(f"Error deleting category image files: {e}")
                import traceback
                traceback.print_exc()

    def delete(self, *args, **kwargs):
        """Delete associated image files before deleting the model instance"""
        # Delete image files before model deletion
        self.delete_category_image_files()
        
        # Call parent delete
        super().delete(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Post(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    content = RichTextField(blank=True, null=True)
    featured_image = models.ImageField(upload_to=post_image_upload_to, blank=True, null=True)
    featured_image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="The order in which the post should be displayed.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date']

    def _process_featured_image(self, old_image):
        if self.featured_image and os.path.exists(self.featured_image.path):
            image_path = self.featured_image.path
            current_hash = calculate_image_hash(image_path)

            # If image changed or no hash, process it
            if old_image != self.featured_image or not self.featured_image_hash or self.featured_image_hash != current_hash:
                self.featured_image_hash = current_hash

                # Convert original image to WebP and optimize
                _, ext = os.path.splitext(image_path)
                if ext.lower() != '.webp':
                    webp_path = convert_and_optimize_uploaded_image(self.featured_image, image_path, quality=88)
                    if webp_path and os.path.exists(webp_path):
                        # Replace original file with WebP version
                        with open(webp_path, 'rb') as f:
                            self.featured_image.save(os.path.basename(webp_path), File(f), save=False)
                        # Delete original non-WebP file if different
                        if webp_path != image_path and os.path.exists(image_path):
                            try:
                                os.remove(image_path)
                            except Exception as e:
                                print(f"Error deleting original image file: {e}")
                        image_path = webp_path  # Update image_path for thumbnail generation
                        # Recalculate hash for WebP version
                        self.featured_image_hash = calculate_image_hash(image_path)

                # Create all image sizes (small, thumb, medium, large) - saved on disk only
                create_image_sizes(self.featured_image, image_path, settings.MEDIA_ROOT)

            # Delete old image and all sizes if replaced
            if old_image and old_image != self.featured_image:
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
        if not self.slug:
            self.slug = slugify(self.title)
        
        old_featured_image = None
        if self.pk:
            try:
                old_instance = Post.objects.get(pk=self.pk)
                old_featured_image = old_instance.featured_image
            except Post.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        self._process_featured_image(old_featured_image)
        super().save(update_fields=['featured_image_hash'])

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:posts-detail', kwargs={'slug': self.slug})
    
    def featured_image_thumb_display(self):
        if self.featured_image:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.featured_image.url)
        return "No Image"
    featured_image_thumb_display.short_description = "Featured Image Thumbnail"

    def delete_featured_image_files(self):
        """Delete the featured image file and all its size variants"""
        if self.featured_image:
            original_path = self.featured_image.path
            if os.path.exists(original_path):
                try:
                    os.remove(original_path)
                    print(f"Deleted original featured image file: {original_path}")
                except Exception as e:
                    print(f"Error deleting original featured image file {original_path}: {e}")

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
        # Delete featured image and all its size variants
        self.delete_featured_image_files()
        
        # PostImage instances will be deleted via CASCADE, and their delete() methods
        # will handle deleting their own image files and size variants
        
        super().delete(*args, **kwargs)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image_file = models.ImageField(upload_to=post_gallery_image_upload_to)
    image_file_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def _process_image_file(self, old_image):
        if self.image_file and os.path.exists(self.image_file.path):
            image_path = self.image_file.path
            current_hash = calculate_image_hash(image_path)

            if old_image != self.image_file or not self.image_file_hash or self.image_file_hash != current_hash:
                self.image_file_hash = current_hash

                _, ext = os.path.splitext(image_path)
                if ext.lower() != '.webp':
                    webp_path = convert_and_optimize_uploaded_image(self.image_file, image_path, quality=88)
                    if webp_path and os.path.exists(webp_path):
                        with open(webp_path, 'rb') as f:
                            self.image_file.save(os.path.basename(webp_path), File(f), save=False)
                        if webp_path != image_path and os.path.exists(image_path):
                            try:
                                os.remove(image_path)
                            except Exception as e:
                                print(f"Error deleting original image file: {e}")
                        image_path = webp_path
                        self.image_file_hash = calculate_image_hash(image_path)

                # Create all image sizes (small, thumb, medium, large) - saved on disk only
                create_image_sizes(self.image_file, image_path, settings.MEDIA_ROOT)
            
            if old_image and old_image != self.image_file:
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
        old_image_file = None
        if self.pk:
            try:
                old_instance = PostImage.objects.get(pk=self.pk)
                old_image_file = old_instance.image_file
            except PostImage.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        self._process_image_file(old_image_file)
        super().save(update_fields=['image_file_hash'])

    def __str__(self):
        return f"Image for {self.post.title} - {self.caption or self.image_file.name}"
    
    def image_file_thumb_display(self):
        if self.image_file:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image_file.url)
        return "No Image"

    def delete_image_file_files(self):
        """Delete the image file and all its size variants"""
        if self.image_file:
            original_path = self.image_file.path
            if os.path.exists(original_path):
                try:
                    os.remove(original_path)
                    print(f"Deleted original post image file: {original_path}")
                except Exception as e:
                    print(f"Error deleting original post image file {original_path}: {e}")

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
        self.delete_image_file_files()
        super().delete(*args, **kwargs)
