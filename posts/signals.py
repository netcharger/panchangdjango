from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Category, Post, PostImage

@receiver(post_delete, sender=Category)
def delete_category_images(sender, instance, **kwargs):
    """
    Signal to delete image files when a Category is deleted.
    This works for both instance.delete() and queryset.delete().
    """
    print(f"[SIGNAL] post_delete triggered for Category: {instance.name}")
    # We call the helper method on the instance to keep the logic in one place
    # Note: instance.id is None here, but the instance data is still in memory
    instance.delete_category_image_files()

@receiver(post_delete, sender=Post)
def delete_post_images(sender, instance, **kwargs):
    """
    Signal to delete image files when a Post is deleted.
    """
    print(f"[SIGNAL] post_delete triggered for Post: {instance.title}")
    instance.delete_featured_image_files()

@receiver(post_delete, sender=PostImage)
def delete_post_gallery_images(sender, instance, **kwargs):
    """
    Signal to delete image files when a PostImage is deleted.
    """
    print(f"[SIGNAL] post_delete triggered for PostImage: {instance.id}")
    instance.delete_image_file_files()
