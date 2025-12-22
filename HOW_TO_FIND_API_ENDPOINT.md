# How to Find the API Endpoint in Django Admin

## Where to Look

The **API Endpoint** field appears in the **detail/edit page** of each model, NOT in the list view.

### Step-by-Step Instructions:

1. **Go to Django Admin** (usually at `http://localhost:8000/admin/`)

2. **Navigate to any model** that has an API endpoint:
   - Panchang → Festivals or Important Days
   - Posts → Categories, Tags, or Posts
   - Audio Manager → Categories or Audio Files
   - Mobile Settings → Carousel Images
   - Wallpaper Manager → Categories or Wallpapers

3. **Click on an existing record** (or create a new one and save it first)

4. **Scroll down** in the detail/edit form

5. **Look for a fieldset called "API Endpoint"** - it appears:
   - At the bottom of the form, near the "Timestamps" section
   - OR just before the "Timestamps" section
   - With a clickable link: **"📌 View API"**

## Visual Guide

The API Endpoint section looks like this:

```
┌─────────────────────────────────────┐
│ API Endpoint                        │
├─────────────────────────────────────┤
│ View this [model name] in the API   │
│                                     │
│ 📌 View API  ← Click this link      │
└─────────────────────────────────────┘
```

## Troubleshooting

### If you don't see the "API Endpoint" fieldset:

1. **Make sure you're on the DETAIL/EDIT page**, not the list page
   - The list page shows all records
   - The detail page shows a single record's form

2. **Make sure the record is saved**
   - For new records, save it first
   - Unsaved records show: "API available after saving."

3. **Check if the model has a ViewSet**
   - Only models with DRF viewsets have API endpoints
   - Gallery models (FestivalGallery, ImportantDayGallery) don't have endpoints

4. **Restart your Django server**
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart it:
   python manage.py runserver
   ```

5. **Check for errors in the Django console**
   - Look for any ImportError or AttributeError
   - Make sure `admin_utils.py` is in your project root

### Common Locations:

- **Festival Admin**: Scroll down past "Admin Notes" section
- **Post Admin**: Scroll down past "Publication" section
- **Audio File Admin**: Scroll down past "Publication" section
- **Wallpaper Admin**: Scroll down past "Statistics" section

## Quick Test

To quickly verify it's working:

1. Go to: **Panchang → Festivals**
2. Click on any existing Festival
3. Scroll to the bottom
4. You should see "API Endpoint" fieldset with "📌 View API" link

If you still don't see it, check the browser console for JavaScript errors or Django logs for Python errors.

