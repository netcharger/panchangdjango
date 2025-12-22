# API Endpoint Implementation in Django Admin

## Overview

This implementation adds dynamic API endpoint links to all Django Admin detail pages. The system automatically detects API endpoints for models registered with DRF viewsets and displays clickable links in the admin interface.

## Files Created

### 1. `admin_utils.py`
Core utility module that:
- Discovers routers and their registrations from all apps
- Maps models to viewsets automatically
- Detects filter backends, search fields, and ordering fields
- Builds API URLs dynamically

### 2. `admin_mixin.py`
Admin mixin class (optional helper) for adding API endpoint functionality

### 3. `add_api_endpoint_helper.py`
Helper functions for adding API endpoint methods to admin classes

## Implementation Details

### How It Works

1. **Router Discovery**: The system imports all URL modules and discovers router registrations:
   - `panchang.urls` → `/api/`
   - `posts.urls` → `/api/posts/`
   - `audio_manager.urls` → `/api/audio-manager/`
   - `mobileapp_settings.urls` → `/api/mobile-settings/`
   - `wallpaper_manager.urls` → `/api/wallpapers/`

2. **Model-to-ViewSet Mapping**: Extracts models from viewsets by:
   - Checking `queryset.model`
   - Checking `serializer_class.Meta.model`
   - Instantiating viewset and calling `get_queryset().model` as fallback

3. **Query Parameter Detection**: Automatically detects:
   - Filter fields from `filterset_fields` or `filterset_class`
   - Search fields from `search_fields`
   - Ordering fields from `ordering_fields`
   - Pagination from `pagination_class`

4. **URL Generation**: Builds URLs in format:
   - Detail: `/api/<prefix>/<route>/<lookup_value>/`
   - List: `/api/<prefix>/<route>/`

## Updated Admin Files

### 1. `panchang/admin.py`
- Added API endpoint to `FestivalAdmin`
- Added API endpoint to `ImportantDayAdmin`

### 2. `posts/admin.py`
- Added API endpoint to `CategoryAdmin`
- Added API endpoint to `TagAdmin`
- Added API endpoint to `PostAdmin`

### 3. `audio_manager/admin.py`
- Added API endpoint to `CategoryAdmin`
- Added API endpoint to `AudioFileAdmin`

### 4. `mobileapp_settings/admin.py`
- Added API endpoint to `CarouselImageAdmin`

### 5. `wallpaper_manager/admin.py`
- Added API endpoint to `CategoryAdmin`
- Added API endpoint to `WallpaperAdmin`

## API Endpoint Pattern Added to Each Admin

```python
from admin_utils import get_api_endpoint_url

# In readonly_fields:
readonly_fields = (..., 'api_endpoint')

# Method added:
def api_endpoint(self, obj):
    """Display API endpoint link"""
    if not obj or not hasattr(obj, 'pk') or not obj.pk:
        return format_html('<span style="color: #888;">API available after saving.</span>')
    
    request = getattr(self, '_request', None)
    api_url = get_api_endpoint_url(obj, request=request)
    
    if not api_url:
        return format_html('<span style="color: #888;">No API endpoint configured for this model.</span>')
    
    if not api_url.startswith('http'):
        if not api_url.startswith('/'):
            api_url = '/' + api_url
    
    return format_html(
        '<a href="{}" target="_blank" style="font-weight: bold; color: #417690;">📌 View API</a>',
        api_url
    )
api_endpoint.short_description = "API Endpoint"

def changeform_view(self, request, *args, **kwargs):
    """Store request in instance for use in api_endpoint method"""
    self._request = request
    return super().changeform_view(request, *args, **kwargs)
```

## Detected API Endpoints

### Panchang App (`/api/`)
- **Festival**: `/api/festivals/{slug}/`
  - Filters: type, importance, month, paksha, tithi, calculation_type
  - Search: festival_name, slug, description, month
  - Ordering: festival_name, importance, month
  
- **ImportantDay**: `/api/important-days/{slug}/`
  - Filters: type_of, importance, is_holiday, calendar_type
  - Search: day_name, slug, description, date
  - Ordering: date, day_name, importance, sequence_id

### Posts App (`/api/posts/`)
- **Category**: `/api/posts/categories/{slug}/`
  - Lookup field: slug
  
- **Tag**: `/api/posts/tags/{slug}/`
  - Lookup field: slug
  
- **Post**: `/api/posts/posts/{slug}/`
  - Filters: category (slug), tags (slug), is_published
  - Lookup field: slug

### Audio Manager App (`/api/audio-manager/`)
- **Category**: `/api/audio-manager/categories/{slug}/`
  - Lookup field: slug
  
- **AudioFile**: `/api/audio-manager/audio-files/{slug}/`
  - Filters: category (slug), tags (slug), is_published
  - Lookup field: slug

### Mobile Settings App (`/api/mobile-settings/`)
- **CarouselImage**: `/api/mobile-settings/carousel-images/{pk}/`
  - Lookup field: pk

### Wallpaper Manager App (`/api/wallpapers/`)
- **Category**: `/api/wallpapers/categories/{slug}/`
  - Filters: is_active
  - Search: name, description
  - Ordering: order, name, created_at
  - Lookup field: slug
  
- **Wallpaper**: `/api/wallpapers/wallpapers/{pk}/`
  - Filters: main_category, main_category_id, sub_category, sub_category_id, is_active
  - Search: title
  - Ordering: created_at, views_count, download_count
  - Lookup field: pk

## Usage

1. Navigate to any model's detail page in Django Admin
2. Scroll to the "API Endpoint" section
3. Click "📌 View API" to open the API endpoint in a new tab
4. If the record hasn't been saved yet, you'll see: "API available after saving."

## Features

- ✅ Automatic endpoint detection
- ✅ Support for slug and pk lookup fields
- ✅ Detection of filters, search, and ordering parameters
- ✅ Works with nested routers
- ✅ Graceful handling of unsaved records
- ✅ Clean, readable admin interface integration

## Notes

- The system only shows endpoints for models that have corresponding viewsets registered
- Gallery models (FestivalGallery, ImportantDayGallery) don't have API endpoints as they're inline models
- The implementation handles both DefaultRouter and SimpleRouter



