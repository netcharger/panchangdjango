import os
import sys
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage

# Import universal image processing utility
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from image_utils import (
    delete_image_and_versions,
    convert_to_webp,
    create_image_sizes,
    calculate_image_hash,
)

class ImageProcessingMixin:
    """
    Mixin to handle common image processing tasks:
    - WebP conversion
    - Hash calculation
    - Creating image sizes
    - Deleting old images on update
    - Deleting images on model deletion
    """

    def process_image_change(self, field_name, old_image, hash_field_name=None):
        """
        Process changes for a single image field.
        """
        current_image = getattr(self, field_name)

        # Helper to safely get image name
        def get_image_name(img):
            return img.name if img and hasattr(img, 'name') else None

        current_image_name = get_image_name(current_image)
        old_image_name = get_image_name(old_image)

        # Case 1: Image was cleared or is empty
        if not current_image or not current_image_name:
            if old_image_name:
                print(f"[_PROCESS] {field_name} cleared! Old image was: {old_image_name}")
                self.delete_image_files(old_image)
            return

        # Case 2: Image is present (new or existing)
        image_path = current_image.path
        
        # Calculate hash if needed
        current_hash = None
        if hash_field_name:
            current_hash = calculate_image_hash(image_path)
            # Update hash if changed
            old_hash = getattr(self, hash_field_name)
            if old_hash != current_hash:
                 setattr(self, hash_field_name, current_hash)

        # Check if we need to process (New upload OR hash changed OR content changed)
        # For simplicity, if names are different or hash is different, we process.
        should_process = (
            old_image != current_image or 
            (hash_field_name and getattr(self, hash_field_name) != current_hash)
        )
        
        # If it's the exact same file object and name, we might skip, 
        # but logic often relies on "process every save" if checking needed.
        # We'll use the check logic from original models which was granular.
        
        # Logic from models: if old != new OR (hash_field and hash_changed)
        
        if should_process:
             # webp conversion
            _, ext = os.path.splitext(image_path)
            if ext.lower() != '.webp':
                print(f"Image is not WebP ({ext}), attempting conversion for: {image_path}")
                webp_file_obj = convert_to_webp(image_path, quality=88)
                if webp_file_obj:
                    # Delete original
                    if default_storage.exists(image_path):
                        try:
                            default_storage.delete(image_path)
                            print(f"Deleted original non-WebP file after conversion: {image_path}")
                        except Exception as e:
                            print(f"Error deleting original non-WebP file {image_path}: {e}")

                    # Save new WebP to the field
                    # Note: save=False is important to avoid recursion loop in model.save()
                    # IMPORTANT: We must call save on the field of the INSTANCE to update it in memory
                    getattr(self, field_name).save(webp_file_obj.name, webp_file_obj, save=False)
                    current_image = getattr(self, field_name) # Refresh local ref
                    print(f"Updated {field_name} field to WebP: {current_image.name}")
                    
                    # Update hash for the new WebP file
                    if hash_field_name:
                        new_hash = calculate_image_hash(current_image.path)
                        setattr(self, hash_field_name, new_hash)
                else:
                    print(f"Failed to convert image to WebP: {image_path}")
            
            # Create sizes
            # Refresh current_image to be sure
            current_image = getattr(self, field_name)
            print(f"Creating image sizes for: {current_image.name}")
            create_image_sizes(current_image, media_root=settings.MEDIA_ROOT)
            
            # IMPORTANT: Since this mixin is usually called AFTER super().save(), 
            # we must explicitly save the instance again to persist the new filename/hash to the DB.
            update_fields = [field_name]
            if hash_field_name:
                update_fields.append(hash_field_name)
            
            # Avoid recursion if possible, or use save(update_fields=...)
            print(f"[{self.__class__.__name__}] Saving updated fields to DB: {update_fields}")
            self.save(update_fields=update_fields)


        # Case 3: Delete old image if it was replaced
        # We compare old_image_name with the CURRENT (possibly updated to webp) image name
        new_current_image_name = get_image_name(getattr(self, field_name))
        if old_image_name and old_image_name != new_current_image_name:
             # Ensure we are deleting a file that was on the same storage and actually replaced
             print(f"Image changed from {old_image_name} to {new_current_image_name}, deleting old image and its sizes")
             delete_image_and_versions(old_image, verbose=True)


    def delete_image_files(self, image_field):
        """
        Generic method to delete image files for a specific field.
        """
        if image_field:
            print(f"[{self.__class__.__name__}.delete_image_files] Deleting image: {image_field.name}")
            delete_image_and_versions(image_field, verbose=True)
