# Generated manually to add new fields to existing tables

git afrom django.db import migrations, models, connection
import django.db.models.deletion
import panchang.utils





def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
        """, [table_name, column_name])
        return cursor.fetchone()[0] > 0


def add_field_if_not_exists(apps, schema_editor):
    """Add fields only if they don't already exist"""
    db_alias = schema_editor.connection.alias

    # Check and add Festival fields
    if not check_column_exists('festivals', 'image_thumb'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE festivals
                ADD COLUMN image_thumb VARCHAR(500) NULL
            """)

    if not check_column_exists('festivals', 'image_medium'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE festivals
                ADD COLUMN image_medium VARCHAR(500) NULL
            """)

    if not check_column_exists('festivals', 'image_large'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE festivals
                ADD COLUMN image_large VARCHAR(500) NULL
            """)

    # Check and add ImportantDay fields
    if not check_column_exists('important_days', 'image_thumb'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE important_days
                ADD COLUMN image_thumb VARCHAR(500) NULL
            """)

    if not check_column_exists('important_days', 'image_medium'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE important_days
                ADD COLUMN image_medium VARCHAR(500) NULL
            """)

    if not check_column_exists('important_days', 'image_large'):
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE important_days
                ADD COLUMN image_large VARCHAR(500) NULL
            """)


def reverse_add_field_if_not_exists(apps, schema_editor):
    """Reverse migration - remove fields if they exist"""
    # This is handled by migration 0006, so we don't need to do anything here
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('panchang', '0001_initial'),
    ]

    operations = [
        # Add thumbnail fields to Festival and ImportantDay (with existence check)
        migrations.RunPython(
            add_field_if_not_exists,
            reverse_add_field_if_not_exists,
        ),
        # Create FestivalGallery table if it doesn't exist
        migrations.CreateModel(
            name='FestivalGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Wallpaper image', upload_to=panchang.utils.gallery_image_upload_path)),
                ('image_alt', models.CharField(blank=True, help_text='Alt text for image', max_length=255)),
                ('caption', models.CharField(blank=True, help_text='Image caption', max_length=500)),
                ('image_thumb', models.CharField(blank=True, help_text='Path to thumbnail (300x200)', max_length=500, null=True)),
                ('image_medium', models.CharField(blank=True, help_text='Path to medium size (800x600)', max_length=500, null=True)),
                ('image_large', models.CharField(blank=True, help_text='Path to large size (1600x900)', max_length=500, null=True)),
                ('display_order', models.IntegerField(default=0, help_text='Order for displaying images')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('festival', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='panchang.festival')),
            ],
            options={
                'db_table': 'festival_gallery',
                'ordering': ['display_order', '-created_at'],
                'verbose_name_plural': 'Festival Gallery Images',
            },
        ),
        # Create ImportantDayGallery table if it doesn't exist
        migrations.CreateModel(
            name='ImportantDayGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Wallpaper image', upload_to=panchang.utils.gallery_image_upload_path)),
                ('image_alt', models.CharField(blank=True, help_text='Alt text for image', max_length=255)),
                ('caption', models.CharField(blank=True, help_text='Image caption', max_length=500)),
                ('image_thumb', models.CharField(blank=True, help_text='Path to thumbnail (300x200)', max_length=500, null=True)),
                ('image_medium', models.CharField(blank=True, help_text='Path to medium size (800x600)', max_length=500, null=True)),
                ('image_large', models.CharField(blank=True, help_text='Path to large size (1600x900)', max_length=500, null=True)),
                ('display_order', models.IntegerField(default=0, help_text='Order for displaying images')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('important_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='panchang.importantday')),
            ],
            options={
                'db_table': 'important_day_gallery',
                'ordering': ['display_order', '-created_at'],
                'verbose_name_plural': 'Important Day Gallery Images',
            },
        ),
    ]




