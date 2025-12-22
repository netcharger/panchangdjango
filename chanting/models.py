from django.db import models
from django.template.defaultfilters import slugify
from taggit.managers import TaggableManager


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    # Parent enables nested categories (Vishnu → Namo Narayana)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    
    description = models.TextField(blank=True)

    # SEO Fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order.")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Chant(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chants'
    )

    # Built-in tag system (useful for search)
    tags = TaggableManager(blank=True)

    # Chant Main Fields
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    description = models.TextField(blank=True)

    # Audio + Image
    mp3_file = models.FileField(upload_to='chanting/audio/')
    image = models.ImageField(upload_to='chanting/images/', blank=True, null=True)

    # Chant-specific fields
    language = models.CharField(max_length=50, default="telugu")
    recommended_count = models.PositiveIntegerField(default=108)
    audio_duration = models.FloatField(blank=True, null=True)   # in seconds

    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)

    # Publishing
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(blank=True, null=True)

    order = models.IntegerField(default=0, help_text="Display position.")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-published_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



