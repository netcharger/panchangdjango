"""
URL configuration for wallpaper_manager app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, WallpaperViewSet, bulk_upload_wallpapers, bulk_upload_page

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'wallpapers', WallpaperViewSet, basename='wallpaper')

urlpatterns = [
    path('', include(router.urls)),
    path('bulk-upload/', bulk_upload_page, name='bulk-upload-page'),
    path('bulk-upload/api/', bulk_upload_wallpapers, name='bulk-upload-wallpapers'),
]

