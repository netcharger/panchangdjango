# Quick Update Guide: API Endpoint at Top + List View

## What Changed

All admin files need these updates:
1. **API Endpoint fieldset moved to TOP** of detail page
2. **API URL shown in LIST view** (add to list_display)
3. **Full URL displayed prominently** (not just a link)

## Files Already Updated

✅ `panchang/admin.py` - FestivalAdmin (partially done, need to add api_url method)
⏳ Other files need updates

## Quick Fix Pattern

For each admin class:

1. **Import helper**:
```python
from admin_api_helper import get_api_endpoint_display
```

2. **Add to list_display**:
```python
list_display = [..., 'api_url']
```

3. **Move API Endpoint fieldset to TOP** (first in fieldsets tuple)

4. **Replace api_endpoint method**:
```python
def api_endpoint(self, obj):
    """Display API endpoint link and URL"""
    request = getattr(self, '_request', None)
    return get_api_endpoint_display(obj, request=request, for_list=False)
api_endpoint.short_description = "API Endpoint"
```

5. **Add api_url method**:
```python
def api_url(self, obj):
    """Display API URL in list view"""
    request = getattr(self, '_request', None)
    return get_api_endpoint_display(obj, request=request, for_list=True)
api_url.short_description = "API URL"
```

6. **Add changelist_view**:
```python
def changelist_view(self, request, *args, **kwargs):
    """Store request for list view"""
    self._request = request
    return super().changelist_view(request, *args, **kwargs)
```

## Status

I'm updating all files now. Check back in a moment!

