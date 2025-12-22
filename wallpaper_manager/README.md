# Wallpaper Manager App

A Django app for managing wallpapers with categories, subcategories, and bulk upload functionality.

## Features

- **Categories**: Main categories for organizing wallpapers
- **Sub Categories**: Sub-categories under each main category
- **Wallpapers**: Image wallpapers with metadata
- **Bulk Upload**: Upload multiple images at once using Dropzone.js
- **REST API**: Full REST API for accessing wallpapers, categories, and subcategories
- **Image Processing**: Automatic WebP conversion and multiple size generation
- **Admin Interface**: Django admin interface for managing all data

## Models

### Category
- `name`: Category name
- `slug`: URL-friendly slug (auto-generated)
- `description`: Category description
- `image`: Category thumbnail image
- `is_active`: Active status
- `order`: Display order

### SubCategory
- `name`: Sub-category name
- `slug`: URL-friendly slug (auto-generated)
- `category`: Foreign key to Category
- `description`: Sub-category description
- `image`: Sub-category thumbnail image
- `is_active`: Active status
- `order`: Display order

### Wallpaper
- `title`: Optional wallpaper title
- `image`: Wallpaper image file
- `category`: Foreign key to Category
- `subcategory`: Foreign key to SubCategory (optional)
- `image_hash`: MD5 hash for duplicate detection
- `is_active`: Active status
- `views_count`: Number of views
- `download_count`: Number of downloads

## API Endpoints

### Categories
- `GET /api/wallpapers/categories/` - List all categories
- `GET /api/wallpapers/categories/{id}/` - Get category details

### Sub Categories
- `GET /api/wallpapers/subcategories/` - List all subcategories
- `GET /api/wallpapers/subcategories/{id}/` - Get subcategory details
- `GET /api/wallpapers/subcategories/by_category/?category={category_id}` - Get subcategories by category

### Wallpapers
- `GET /api/wallpapers/wallpapers/` - List all wallpapers
- `GET /api/wallpapers/wallpapers/{id}/` - Get wallpaper details
- `POST /api/wallpapers/wallpapers/{id}/increment_view/` - Increment view count
- `POST /api/wallpapers/wallpapers/{id}/increment_download/` - Increment download count

### Bulk Upload
- `GET /api/wallpapers/bulk-upload/` - Bulk upload page (HTML)
- `POST /api/wallpapers/bulk-upload/api/` - Bulk upload API endpoint

## Usage

### Bulk Upload Page

1. Navigate to `/api/wallpapers/bulk-upload/`
2. Select a category (required)
3. Optionally select a subcategory
4. Drag and drop images or click to select files
5. Images will be uploaded automatically

### API Usage Examples

#### Get all categories
```bash
curl http://localhost:8000/api/wallpapers/categories/
```

#### Get wallpapers by category
```bash
curl http://localhost:8000/api/wallpapers/wallpapers/?category=1
```

#### Get subcategories by category
```bash
curl http://localhost:8000/api/wallpapers/subcategories/by_category/?category=1
```

## Image Processing

All uploaded images are:
- Converted to WebP format for better compression
- Automatically resized to multiple sizes (thumb, small, medium, large) as defined in `settings.IMAGE_SIZES`
- Stored with MD5 hash for duplicate detection

## Admin Interface

Access the admin interface at `/admin/` to:
- Manage categories and subcategories
- View and manage wallpapers
- See upload statistics (views, downloads)

## Setup

1. Run migrations:
```bash
python manage.py migrate wallpaper_manager
```

2. Create a superuser (if not already created):
```bash
python manage.py createsuperuser
```

3. Access admin interface and create categories/subcategories

4. Use bulk upload page to upload wallpapers


