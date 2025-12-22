# Generated manually to add new fields to existing tables

from django.db import migrations, models
import django.db.models.deletion
import panchang.utils


class Migration(migrations.Migration):

    dependencies = [
        ('panchang', '0001_initial'),
    ]

    operations = [
        # Add thumbnail fields to Festival
        migrations.AddField(
            model_name='festival',
            name='image_thumb',
            field=models.CharField(blank=True, help_text='Path to thumbnail (300x200)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='festival',
            name='image_medium',
            field=models.CharField(blank=True, help_text='Path to medium size (800x600)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='festival',
            name='image_large',
            field=models.CharField(blank=True, help_text='Path to large size (1600x900)', max_length=500, null=True),
        ),
        # Add thumbnail fields to ImportantDay
        migrations.AddField(
            model_name='importantday',
            name='image_thumb',
            field=models.CharField(blank=True, help_text='Path to thumbnail (300x200)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='importantday',
            name='image_medium',
            field=models.CharField(blank=True, help_text='Path to medium size (800x600)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='importantday',
            name='image_large',
            field=models.CharField(blank=True, help_text='Path to large size (1600x900)', max_length=500, null=True),
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




