# Content Management Features

## Overview

Both `Festival` and `ImportantDay` models now support rich content management with the following features:

### 1. **Image Field**
- Upload main images for festivals and important days
- Images are stored in `media/festivals/` and `media/important_days/` directories
- Accessible via API with full URL in `image_url` field

### 2. **Slug Field**
- URL-friendly version of the name
- Auto-generated from `festival_name` or `day_name + date`
- Unique and indexed for fast lookups
- Can be used for SEO-friendly URLs

### 3. **Rich Text Content Field**
- Full-featured rich text editor (CKEditor) with image upload support
- Upload images directly from within the editor
- Supports formatting, links, tables, and more
- Content stored as HTML

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create media directories:**
   ```bash
   mkdir -p media/festivals
   mkdir -p media/important_days
   mkdir -p media/uploads  # For CKEditor uploads
   ```

## Admin Interface

### Festival Admin
- **Image upload**: Click on the image field to upload
- **Slug**: Auto-populated from festival name, can be edited
- **Content**: Rich text editor with full toolbar including image upload

### Important Day Admin
- **Image upload**: Click on the image field to upload
- **Slug**: Auto-populated from day name and date, can be edited
- **Content**: Rich text editor with full toolbar including image upload

## API Usage

### Get Festival by Slug
```
GET /api/festivals/slug/{slug}/
```

Example:
```
GET /api/festivals/slug/ugadi/
```

### Get Important Day by Slug
```
GET /api/important-days/slug/{slug}/
```

Example:
```
GET /api/important-days/slug/new-years-day-01-january/
```

### API Response Fields

**Festival:**
- `id`: Primary key
- `festival_name`: Name of the festival
- `slug`: URL-friendly slug
- `image`: Image file path (for uploads)
- `image_url`: Full URL to the image
- `content`: Rich text HTML content
- `description`: Plain text description
- ... (other fields)

**Important Day:**
- `id`: Primary key
- `day_name`: Name of the day
- `slug`: URL-friendly slug
- `image`: Image file path (for uploads)
- `image_url`: Full URL to the image
- `content`: Rich text HTML content
- `description`: Plain text description
- ... (other fields)

## CKEditor Image Upload

1. In the admin interface, click on the **Content** field
2. Click the **Image** button in the toolbar
3. Click **Upload** tab
4. Select an image file
5. The image will be uploaded and inserted into the content

Uploaded images are stored in `media/uploads/` directory.

## File Structure

```
panchang_api/
├── media/
│   ├── festivals/          # Festival main images
│   ├── important_days/     # Important day main images
│   └── uploads/            # CKEditor uploaded images
└── ...
```

## Notes

- **Slug Uniqueness**: Slugs must be unique. If auto-generation creates a duplicate, you'll need to manually edit it.
- **Image Formats**: Supported formats: JPG, PNG, GIF, WebP
- **Content Security**: Rich text content is stored as HTML. Be cautious when displaying it to prevent XSS attacks.
- **Media Files**: In production, configure your web server to serve media files, or use a cloud storage service like AWS S3.

## Example: Creating a Festival Post

1. Go to Django Admin: `/admin/panchang/festival/add/`
2. Fill in basic information:
   - Festival Name: "Diwali"
   - Type: "Hindu"
   - Importance: "Major"
3. Upload an image in the **Image** field
4. The **Slug** will auto-populate as "diwali"
5. Write a short description in **Description**
6. Click on **Content** field to open the rich text editor
7. Write your detailed content with formatting
8. Click the **Image** button in the toolbar to upload and insert images
9. Save the festival

The festival will now be accessible via:
- API: `/api/festivals/slug/diwali/`
- Admin: `/admin/panchang/festival/`




