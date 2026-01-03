from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model
from django.urls import reverse
from ckeditor.fields import RichTextField
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
import os
from django.utils.html import format_html

from .utils import (
    category_image_upload_to,
    post_image_upload_to,
    post_gallery_image_upload_to
)
# Import universal image processing utility
import sys
from pathlib import Path
# Add project root to path to import image_utils
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from image_utils import (
    delete_image_and_versions,
    convert_to_webp,
    create_image_sizes,
    calculate_image_hash,
    optimize_image_for_web
)
from .mixins import ImageProcessingMixin

User = get_user_model()

class Category(ImageProcessingMixin, models.Model):
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




    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        old_category_image = None
        if self.pk:
            try:
                old_instance = Category.objects.get(pk=self.pk)
                old_category_image = old_instance.category_image
                if old_category_image:
                    print(f"[SAVE] Found old image for category {self.name}: {old_category_image.name}")
                else:
                    print(f"[SAVE] No old image found for category {self.name}")
            except Category.DoesNotExist:
                pass

        current_image_before_save = self.category_image
        if current_image_before_save:
            print(f"[SAVE] Current image before save: {current_image_before_save.name}")
        else:
            print(f"[SAVE] Current image before save: None/Empty")
            if old_category_image:
                print(f"[SAVE] Image is being cleared! Old image was: {old_category_image.name}")

        super().save(*args, **kwargs) # Save the instance first to ensure file is on disk
        # Process the image after the initial save, so self.category_image has been written to disk.
        self.process_image_change('category_image', old_category_image)


    def __str__(self):
        return self.name

    def get_full_path(self):
        """Get full hierarchical path like 'Parent > Child'"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('posts:category-detail', kwargs={'slug': self.slug})

    def delete_category_image_files(self, image_field_to_delete=None):
        """
        Delete the category image file and all its size variants.
        Uses the universal delete_image_and_versions function via mixin.
        """
        print(f"[Category.delete_category_image_files] Category: {self.name}")
        image_to_delete = image_field_to_delete if image_field_to_delete else self.category_image
        self.delete_image_files(image_to_delete)
        return # Mixin method doesn't return result, but that's fine for now




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

class Post(ImageProcessingMixin, models.Model):
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
        self.process_image_change('featured_image', old_featured_image, hash_field_name='featured_image_hash')


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
        """Delete the featured image file and all its size variants using the universal utility."""
        if self.featured_image:
            self.delete_image_files(self.featured_image)




class PostImage(ImageProcessingMixin, models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image_file = models.ImageField(upload_to=post_gallery_image_upload_to)
    image_file_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']



    def save(self, *args, **kwargs):
        old_image_file = None
        if self.pk:
            try:
                old_instance = PostImage.objects.get(pk=self.pk)
                old_image_file = old_instance.image_file
            except PostImage.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        self.process_image_change('image_file', old_image_file, hash_field_name='image_file_hash')


    def __str__(self):
        return f"Image for {self.post.title} - {self.caption or self.image_file.name}"

    def image_file_thumb_display(self):
        if self.image_file:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image_file.url)
        return "No Image"

    def delete_image_file_files(self):
        """Delete the image file and all its size variants using the universal utility."""
        if self.image_file:
            self.delete_image_files(self.image_file)


