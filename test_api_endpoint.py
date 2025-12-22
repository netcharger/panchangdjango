"""
Test script to verify API endpoint detection is working.
Run this to diagnose issues.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panchang_api.settings')
django.setup()

from admin_utils import get_endpoint_builder
from panchang.models import Festival, ImportantDay
from posts.models import Category, Tag, Post
from audio_manager.models import Category as AudioCategory, AudioFile
from mobileapp_settings.models import CarouselImage
from wallpaper_manager.models import Category as WallpaperCategory, Wallpaper

print("=" * 60)
print("Testing API Endpoint Detection")
print("=" * 60)

# Test models
test_models = [
    (Festival, "Festival"),
    (ImportantDay, "ImportantDay"),
    (Category, "Posts.Category"),
    (Tag, "Posts.Tag"),
    (Post, "Post"),
    (AudioCategory, "Audio.Category"),
    (AudioFile, "AudioFile"),
    (CarouselImage, "CarouselImage"),
    (WallpaperCategory, "Wallpaper.Category"),
    (Wallpaper, "Wallpaper"),
]

builder = get_endpoint_builder()

print("\nDetected API Endpoints:\n")
for model, name in test_models:
    endpoint_info = builder._endpoint_map.get(model)
    if endpoint_info:
        url_prefix = endpoint_info['url_prefix']
        router_prefix = endpoint_info['router_prefix']
        print(f"✅ {name:25} → {url_prefix}{router_prefix}/")
    else:
        print(f"❌ {name:25} → No endpoint found")

print("\n" + "=" * 60)
print("Testing URL Generation (with dummy instances):")
print("=" * 60)

# Try to get a real instance
try:
    festival = Festival.objects.first()
    if festival:
        from admin_utils import get_api_endpoint_url
        url = get_api_endpoint_url(festival)
        print(f"\n✅ Festival URL: {url}")
    else:
        print("\n⚠️  No Festival records found. Create one first to test URLs.")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("If all endpoints show ✅, the detection is working!")
print("If you see ❌, check your URL configurations.")
print("=" * 60)

