"""
Models for Panchang API - Festivals and Important Days
"""
import os
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.html import format_html
from django.utils.text import slugify
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from .utils import (
    festival_image_upload_path,
    important_day_image_upload_path,
    create_image_sizes,
    gallery_image_upload_path,
    convert_and_optimize_uploaded_image,
    calculate_image_hash,
    find_duplicate_image
)
from .tasks import process_festival_image_task, delete_related_images_task


class Festival(models.Model):
    """Model for Hindu festivals based on lunar calendar"""

    CALCULATION_TYPES = [
        ('lunar', 'Lunar'),
        ('solar', 'Solar'),
        ('unspecified', 'Unspecified'),
    ]

    IMPORTANCE_LEVELS = [
        ('Major', 'Major'),
        ('Moderate', 'Moderate'),
        ('Minor', 'Minor'),
    ]

    festival_name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, db_index=True, help_text="URL-friendly version of the name")
    type = models.CharField(max_length=100)
    importance = models.CharField(max_length=20, choices=IMPORTANCE_LEVELS, default='Minor')
    description = models.TextField(blank=True)
    content = RichTextUploadingField(blank=True, null=True, help_text="Rich text content with image upload support")
    image = models.ImageField(upload_to=festival_image_upload_path, blank=True, null=True, help_text="Main image for the festival")
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    month = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    paksha = models.CharField(max_length=20, blank=True, null=True)
    tithi = models.CharField(max_length=50, blank=True, null=True)
    nakshatra = models.CharField(max_length=50, blank=True, null=True)
    solar_event = models.CharField(max_length=200, blank=True, null=True)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES, default='lunar')

    # JSON field for regions (stored as JSON string, can be parsed)
    regions = models.JSONField(default=list, help_text="List of regions where festival is observed")
    
    # JSON field to store calculated festival dates (4 years before, current year, next 5 years = 10 years total)
    festival_dates = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="JSON object storing festival dates: {year: [{'date': 'YYYY-MM-DD', 'time': 'HH:MM AM/PM', 'datetime': 'ISO'}]}"
    )
    
    # Observation field for admin notes
    observation = models.TextField(blank=True, null=True, help_text="Admin observation/notes about this festival")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from festival_name if not provided"""
        if not self.slug:
            base_slug = slugify(self.festival_name)
            self.slug = base_slug
            # Ensure uniqueness by appending number if needed
            counter = 1
            while Festival.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Store original image path before save
        old_image = None
        if self.pk:
            try:
                old_instance = Festival.objects.get(pk=self.pk)
                old_image = old_instance.image
            except Festival.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Enqueue image processing task
        if self.image:
            old_image_path = old_image.path if old_image and hasattr(old_image, 'path') else None
            process_festival_image_task.delay(self.pk, 'Festival', old_image_path=old_image_path)

    class Meta:
        db_table = 'festivals'
        indexes = [
            models.Index(fields=['festival_name']),
            models.Index(fields=['slug']),
            models.Index(fields=['month', 'tithi', 'paksha']),
            models.Index(fields=['calculation_type']),
        ]
        ordering = ['festival_name']

    def __str__(self):
        return self.festival_name
    
    def image_thumb_display(self):
        """Display thumbnail in admin"""
        if self.image:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image.url)
        return "No image"
    image_thumb_display.short_description = "Thumbnail"


class ImportantDay(models.Model):
    """Model for important days based on Gregorian calendar"""

    IMPORTANCE_LEVELS = [
        ('Major', 'Major'),
        ('Moderate', 'Moderate'),
        ('Minor', 'Minor'),
    ]

    HOLIDAY_TYPES = [
        ('india_holiday', 'India Holiday'),
        ('state_holiday', 'State Holiday'),
        ('multi_state_holiday', 'Multi-State Holiday'),
        ('observance_only', 'Observance Only'),
    ]

    sequence_id = models.IntegerField(default=0, db_index=True, help_text="Sequential ID for sorting from first to last record")
    date = models.CharField(max_length=20, db_index=True, help_text="Format: DD Month, e.g., '01 January'")
    day_name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, db_index=True, help_text="URL-friendly version of the name")
    type_of = models.CharField(max_length=100)
    importance = models.CharField(max_length=20, choices=IMPORTANCE_LEVELS, default='Minor')
    description = models.TextField(blank=True)
    content = RichTextUploadingField(blank=True, null=True, help_text="Rich text content with image upload support")
    image = models.ImageField(upload_to=important_day_image_upload_path, blank=True, null=True, help_text="Main image for the important day")
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    is_holiday = models.CharField(max_length=30, choices=HOLIDAY_TYPES, blank=True, null=True)
    regions = models.JSONField(default=list, help_text="List of regions where day is observed")
    calendar_type = models.CharField(max_length=20, default='gregorian')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from day_name if not provided"""
        if not self.slug:
            slug_base = f"{self.day_name} {self.date}"
            base_slug = slugify(slug_base)
            self.slug = base_slug
            counter = 1
            while ImportantDay.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        old_image = None
        if self.pk:
            try:
                old_instance = ImportantDay.objects.get(pk=self.pk)
                old_image = old_instance.image
            except ImportantDay.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Enqueue image processing task
        if self.image:
            old_image_path = old_image.path if old_image and hasattr(old_image, 'path') else None
            process_festival_image_task.delay(self.pk, 'ImportantDay', old_image_path=old_image_path)

    class Meta:
        db_table = 'important_days'
        indexes = [
            models.Index(fields=['sequence_id']),
            models.Index(fields=['slug']),
            models.Index(fields=['date']),
            models.Index(fields=['day_name']),
            models.Index(fields=['is_holiday']),
        ]
        ordering = ['sequence_id', 'date', 'day_name']

    def __str__(self):
        return f"{self.date} - {self.day_name}"
    
    def image_thumb_display(self):
        """Display thumbnail in admin"""
        if self.image:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image.url)
        return "No image"
    image_thumb_display.short_description = "Thumbnail"


class FestivalGallery(models.Model):
    """Gallery model for festival wallpapers"""
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to=gallery_image_upload_path, help_text="Wallpaper image")
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    image_alt = models.CharField(max_length=255, blank=True, help_text="Alt text for image")
    caption = models.CharField(max_length=500, blank=True, help_text="Image caption")
    display_order = models.IntegerField(default=0, help_text="Order for displaying images")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'festival_gallery'
        ordering = ['display_order', '-created_at']
        verbose_name_plural = 'Festival Gallery Images'
    
    def __str__(self):
        return f"{self.festival.festival_name} - {self.image_alt or 'Gallery Image'}"
    
    def image_thumb_display(self):
        """Display thumbnail in admin"""
        if self.image:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image.url)
        return "No image"
    image_thumb_display.short_description = "Thumbnail"
    
    def save(self, *args, **kwargs):
        old_image = None
        if self.pk:
            try:
                old_instance = FestivalGallery.objects.get(pk=self.pk)
                old_image = old_instance.image
            except FestivalGallery.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Enqueue image processing task
        if self.image:
            old_image_path = old_image.path if old_image and hasattr(old_image, 'path') else None
            process_festival_image_task.delay(self.pk, 'FestivalGallery', old_image_path=old_image_path)


class ImportantDayGallery(models.Model):
    """Gallery model for important day wallpapers"""
    important_day = models.ForeignKey(ImportantDay, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to=gallery_image_upload_path, help_text="Wallpaper image")
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="MD5 hash of image content for duplicate detection")
    image_alt = models.CharField(max_length=255, blank=True, help_text="Alt text for image")
    caption = models.CharField(max_length=500, blank=True, help_text="Image caption")
    display_order = models.IntegerField(default=0, help_text="Order for displaying images")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'important_day_gallery'
        ordering = ['display_order', '-created_at']
        verbose_name_plural = 'Important Day Gallery Images'
    
    def __str__(self):
        return f"{self.important_day.day_name} - {self.image_alt or 'Gallery Image'}"
    
    def image_thumb_display(self):
        """Display thumbnail in admin"""
        if self.image:
            return format_html('<img src="{}" width="100" height="67" style="object-fit: cover;" />', self.image.url)
        return "No image"
    image_thumb_display.short_description = "Thumbnail"
    
    def save(self, *args, **kwargs):
        old_image = None
        if self.pk:
            try:
                old_instance = ImportantDayGallery.objects.get(pk=self.pk)
                old_image = old_instance.image
            except ImportantDayGallery.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Enqueue image processing task
        if self.image:
            old_image_path = old_image.path if old_image and hasattr(old_image, 'path') else None
            process_festival_image_task.delay(self.pk, 'ImportantDayGallery', old_image_path=old_image_path)


@receiver(pre_delete, sender=Festival)
@receiver(pre_delete, sender=ImportantDay)
@receiver(pre_delete, sender=FestivalGallery)
@receiver(pre_delete, sender=ImportantDayGallery)
def delete_images_on_delete(sender, instance, **kwargs):
    if instance.image:
        # Enqueue image deletion task (only original image path needed - sizes are in folders)
        delete_related_images_task.delay(instance.image.name)


class PanchangData(models.Model):
    """Model to store daily Panchang data"""
    date = models.CharField(max_length=50, unique=True, help_text="Date in YYYY-MM-DD format usually")
    lunar_month = models.CharField(max_length=100, help_text="Lunar Month (e.g., Pushya)")
    paksha = models.CharField(max_length=50, help_text="Paksha (e.g., Shuddha)")
    thithi = models.CharField(max_length=100, help_text="Thithi (e.g., Trayodashi)")
    thithi_end = models.CharField(max_length=50, help_text="Thithi End Time")
    nakshatram = models.CharField(max_length=100, help_text="Nakshatram (e.g., Rohini)")
    nakshatram_end = models.CharField(max_length=50, help_text="Nakshatram End Time")
    varjyam_time = models.CharField(max_length=100, help_text="Varjyam Time Range")
    durmuhurtham_1 = models.CharField(max_length=100, help_text="Durmuhurtham 1 Time Range")
    durmuhurtham_2 = models.CharField(max_length=100, blank=True, null=True, help_text="Durmuhurtham 2 Time Range")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'panchang_data'
        ordering = ['date']
        verbose_name_plural = 'Panchang Data'

    def __str__(self):
        return f"{self.date} - {self.thithi}"

    # Sunrise/Sunset/Moonrise/Moonset
    sunrise = models.CharField(max_length=50, blank=True, null=True, help_text="Sunrise Time")
    sunset = models.CharField(max_length=50, blank=True, null=True, help_text="Sunset Time")
    moonrise = models.CharField(max_length=50, blank=True, null=True, help_text="Moonrise Time")
    moonset = models.CharField(max_length=50, blank=True, null=True, help_text="Moonset Time")

    # Auspicious Timings
    abhijit_muhurtham = models.CharField(max_length=50, blank=True, null=True, help_text="Abhijit Muhurtham")
    amrita_kalam = models.CharField(max_length=50, blank=True, null=True, help_text="Amrita Kalam")
    brahma_muhurtham = models.CharField(max_length=50, blank=True, null=True, help_text="Brahma Muhurtham")
    pratah_sandhya = models.CharField(max_length=50, blank=True, null=True, help_text="Pratah Sandhya")
    vijaya_muhurtham = models.CharField(max_length=50, blank=True, null=True, help_text="Vijaya Muhurtham")
    godhuli_muhurtham = models.CharField(max_length=50, blank=True, null=True, help_text="Godhuli Muhurtham")
    sayam_sandhya = models.CharField(max_length=50, blank=True, null=True, help_text="Sayam Sandhya")
    nishita_muhurtham = models.CharField(max_length=50, blank=True, null=True, help_text="Nishita Muhurtham")


class PanchangDailyFestival(models.Model):
    """Model to link specific festivals to a Panchang date with a display name"""
    panchang_data = models.ForeignKey(PanchangData, on_delete=models.CASCADE, related_name='daily_festivals')
    festival_name = models.CharField(max_length=200, help_text="Display name for the festival on this day")
    festival_reference = models.ForeignKey(Festival, on_delete=models.SET_NULL, blank=True, null=True, help_text="Reference to the master Festival record")

    class Meta:
        db_table = 'panchang_data_daily_festivals'
        verbose_name = 'Panchang Daily Festival'
        verbose_name_plural = 'Panchang Daily Festivals'

    def __str__(self):
        return self.festival_name



class PanchangJSONExport(models.Model):
    """Model to trigger JSON generation for a specific year"""
    YEAR_CHOICES = [(y, str(y)) for y in range(2024, 2031)]
    
    year = models.IntegerField(choices=YEAR_CHOICES, unique=True, help_text="Select year to generate JSON for")
    file = models.FileField(upload_to='panchang_files/', blank=True, null=True, help_text="Generated JSON file")
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'panchang_json_export'
        verbose_name = 'Panchang JSON Export'
        verbose_name_plural = 'Panchang JSON Exports'

    def __str__(self):
        return f"Panchang JSON {self.year}"

    def save(self, *args, **kwargs):
        # Always generate JSON on save
        if self.year:
            # Filter by date string containing the year (e.g., 'YYYY-MM-DD')
            # Using __startswith assuming date format YYYY-MM-DD or DD-MM-YYYY if we changed it?
            # User format is DD-MM-YYYY now. So contains is safer or endswith?
            # The date format is DD-MM-YYYY (e.g., 01-01-2026). So year is at the end.
            
            # Let's try to filter by regex or contains.
            # actually better to just filter date__icontains=str(self.year)
            
            queryset = PanchangData.objects.filter(date__icontains=str(self.year))
            # Exclude created_at and updated_at by explicitly selecting other fields
            data = list(queryset.values(
                'id', 'date', 'lunar_month', 'paksha', 'thithi', 'thithi_end',
                'nakshatram', 'nakshatram_end', 'varjyam_time', 'durmuhurtham_1', 'durmuhurtham_2',
                # Sun/Moon
                'sunrise', 'sunset', 'moonrise', 'moonset',
                # Auspicious
                'abhijit_muhurtham', 'amrita_kalam', 'brahma_muhurtham', 
                'pratah_sandhya', 'vijaya_muhurtham', 'godhuli_muhurtham', 
                'sayam_sandhya', 'nishita_muhurtham'
            ))
            
            # Add related festivals to each day
            for day_data in data:
                day_obj = PanchangData.objects.get(id=day_data['id'])
                enriched_festivals = []
                for df in day_obj.daily_festivals.select_related('festival_reference').all():
                    fest_data = {
                        'festival_name': df.festival_name,
                        'festival_reference_id': df.festival_reference_id,
                        'slug': df.festival_reference.slug if df.festival_reference else None,
                        'image': df.festival_reference.image.url if df.festival_reference and df.festival_reference.image else None
                    }
                    enriched_festivals.append(fest_data)
                day_data['festivals'] = enriched_festivals
            
            if data:
                json_content = json.dumps(data, indent=4, ensure_ascii=False, cls=DjangoJSONEncoder)
                file_name = f"{self.year}_total_panchangam.json"
                
                # Save file without saving instance to avoid recursion loop if we called save again, 
                # but here we are setting the file field which needs a save.
                # ContentFile allows saving in memory content.
                
                # We need to manually assign the file content
                if self.file:
                    self.file.delete(save=False) # Delete old file if exists
                
                self.file.save(file_name, ContentFile(json_content.encode('utf-8')), save=False)
            
        super().save(*args, **kwargs)


@receiver(post_delete, sender=PanchangJSONExport)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `PanchangJSONExport` object is deleted.
    """
    if instance.file:
        try:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
        except Exception:
            pass
