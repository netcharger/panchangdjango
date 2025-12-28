"""
URL configuration for panchang_api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Import the new views file

urlpatterns = [
    path('', views.welcome_view, name='welcome'),  # Root URL
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('api/', include('panchang.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/audio-manager/', include('audio_manager.urls')),
    path('api/mobile-settings/', include('mobileapp_settings.urls')),
    path('api/wallpapers/', include('wallpaper_manager.urls')),
]

# Add debugging tool URLs only on localhost
if getattr(settings, 'IS_LOCALHOST', False):
    urlpatterns.insert(0, path('silk/', include('silk.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.PANCHANG_FILES_URL, document_root=settings.PANCHANG_FILES_ROOT)
    
    # Debug Toolbar URLs (only on localhost)
    if getattr(settings, 'IS_LOCALHOST', False):
        urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

