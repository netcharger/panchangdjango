"""
URL configuration for panchang_api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('silk/', include('silk.urls')),
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('api/', include('panchang.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/audio-manager/', include('audio_manager.urls')),
    path('api/mobile-settings/', include('mobileapp_settings.urls')),
    path('api/wallpapers/', include('wallpaper_manager.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.PANCHANG_FILES_URL, document_root=settings.PANCHANG_FILES_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

