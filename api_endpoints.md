# Posts Application API Endpoints

This document outlines the API endpoints for the `posts` application, including available filters, for integration with your frontend.

**Base URL for all Posts API endpoints:** `http://127.0.0.1:8000/api/posts/`

---

## 1. Categories Endpoints

### 1.1 List all Categories

Retrieves a list of all active categories, ordered by the `order` field (ascending), then by `name`. Child categories are also ordered by `order` and `name`.

- **URL:** `/api/posts/categories/`
- **Method:** `GET`
- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "name": "Festivals",
      "slug": "festivals",
      "parent": null,
      "description": "Articles about various festivals.",
      "meta_title": "",
      "meta_description": "",
      "category_image": null,
      "is_active": true,
      "get_absolute_url": "/posts/category/festivals/"
    },
    {
      "id": 6,
      "name": "Diwali",
      "slug": "diwali",
      "parent": 1,
      "description": "",
      "meta_title": "",
      "meta_description": "",
      "category_image": null,
      "is_active": true,
      "get_absolute_url": "/posts/category/diwali/"
    }
  ]
  ```

### 1.2 Retrieve a Single Category by Slug

Retrieves the details of a single active category using its unique slug.

- **URL:** `/api/posts/categories/{slug}/`
- **Method:** `GET`
- **Example:** `/api/posts/categories/festivals/`
- **Response Example:**
  ```json
  {
    "id": 1,
    "name": "Festivals",
    "slug": "festivals",
    "parent": null,
    "description": "Articles about various festivals.",
    "meta_title": "",
    "meta_description": "",
    "category_image": null,
    "is_active": true,
    "get_absolute_url": "/posts/category/festivals/"
  }
  ```

---

## 2. Tags Endpoints

### 2.1 List all Tags

Retrieves a list of all tags.

- **URL:** `/api/posts/tags/`
- **Method:** `GET`
- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "name": "Hindu Festival",
      "slug": "hindu-festival"
    },
    {
      "id": 2,
      "name": "Lights",
      "slug": "lights"
    }
  ]
  ```

### 2.2 Retrieve a Single Tag by Slug

Retrieves the details of a single tag using its unique slug.

- **URL:** `/api/posts/tags/{slug}/`
- **Method:** `GET`
- **Example:** `/api/posts/tags/hindu-festival/`
- **Response Example:**
  ```json
  {
    "id": 1,
    "name": "Hindu Festival",
    "slug": "hindu-festival"
  }
  ```

---

## 3. Posts Endpoints

### 3.1 List all Posts (with Filters)

Retrieves a list of published posts, ordered by the `order` field (ascending), then by `published_date` (newest first). Supports various filters.

- **URL:** `/api/posts/posts/`
- **Method:** `GET`
- **Filters:**
    - **`category`**: Filter posts by the slug of their category.
      - **Example:** `/api/posts/posts/?category=festivals`
    - **`tags`**: Filter posts by the slug of a specific tag.
      - **Example:** `/api/posts/posts/?tags=lights`
    - **`is_published`**: Filter posts by their published status.
      - **Values:** `true` or `false`
      - **Example:** `/api/posts/posts/?is_published=true`

- **Combining Filters:** You can combine multiple filters.
    - **Example:** `/api/posts/posts/?category=festivals&tags=lights&is_published=true`

- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "title": "Dummy Post Title 1",
      "slug": "dummy-post-title-1",
      "featured_image": "http://127.0.0.1:8000/media/posts/featured_post_1.webp"
    },
    {
      "id": 2,
      "title": "Dummy Post Title 2",
      "slug": "dummy-post-title-2",
      "featured_image": "http://127.0.0.1:8000/media/posts/featured_post_2.webp"
    }
  ]
  ```

### 3.2 Retrieve a Single Post by Slug

Retrieves the details of a single published post using its unique slug.

- **URL:** `/api/posts/posts/{slug}/`
- **Method:** `GET`
- **Example:** `/api/posts/posts/dummy-post-title-1/`
- **Response Example:**
  ```json
  {
    "id": 1,
    "category": {
      "id": 1,
      "name": "Festivals",
      "slug": "festivals",
      "parent": null,
      "get_absolute_url": "/posts/category/festivals/"
    },
    "tags": [
      {"id": 1, "name": "Hindu Festival", "slug": "hindu-festival"},
      {"id": 2, "name": "Lights", "slug": "lights"}
    ],
    "author": "dummyadmin",
    "title": "Dummy Post Title 1",
    "slug": "dummy-post-title-1",
    "excerpt": "This is a short excerpt...",
    "content": "<p>This is the rich text content...</p>",
    "featured_image": "http://127.0.0.1:8000/media/posts/featured_post_1.webp",
    "images": [
      {"id": 1, "image_file": "http://127.0.0.1:8000/media/post_images/post_1_gallery_0.webp", "caption": "Gallery image 1 for Dummy Post Title 1", "uploaded_at": "2025-11-12T10:00:00Z"}
    ],
    "meta_title": "",
    "meta_description": "",
    "is_published": true,
    "published_date": "2025-05-15T10:00:00Z",
    "created_at": "2025-11-12T10:00:00Z",
    "updated_at": "2025-11-12T10:00:00Z"
  }
  ```

### 3.3 Retrieve a Single Post by ID

Retrieves the details of a single published post using its unique ID.

- **URL:** `/api/posts/posts/by-id/{post_id}/`
- **Method:** `GET`
- **Example:** `/api/posts/posts/by-id/1/`
- **Response Example:** (Same as Retrieve a Single Post by Slug response above)
- **Error Response:** If post not found or not published:
  ```json
  {
    "error": "Post not found"
  }
  ```

# Audio Manager Application API Endpoints

This document outlines the API endpoints for the `audio_manager` application, including available filters, for integration with your frontend.

**Base URL for all Audio Manager API endpoints:** `http://127.0.0.1:8000/api/audio-manager/`

---

## 1. Categories Endpoints

### 1.1 List all Main Categories

Retrieves a list of all active main audio categories only (no subcategories/children). Returns only main categories (categories with no parent), ordered by the `order` field.

- **URL:** `/api/audio-manager/categories/`
- **Method:** `GET`
- **Response Example:**
  ```json
  [
    {
      "id": 10,
      "name": "Music Genres",
      "slug": "music-genres",
      "order": 0
    },
    {
      "id": 15,
      "name": "Religious",
      "slug": "religious",
      "order": 1
    },
    {
      "id": 20,
      "name": "Meditation",
      "slug": "meditation",
      "order": 2
    }
  ]
  ```

**Response Fields:**
- `id`: Unique category ID
- `name`: Category name
- `slug`: URL-friendly category identifier
- `order`: Display order (used for sorting)

### 1.2 Retrieve a Single Category by Slug

Retrieves the details of a single active audio category using its unique slug. Works for both main categories and subcategories.

- **URL:** `/api/audio-manager/categories/{slug}/`
- **Method:** `GET`
- **Example:** `/api/audio-manager/categories/music-genres/` (main category)
- **Example:** `/api/audio-manager/categories/classical/` (subcategory)
- **Response Example (Main Category):**
  ```json
  {
    "id": 10,
    "name": "Music Genres",
    "slug": "music-genres",
    "parent": null,
    "description": "Various genres of music.",
    "meta_title": "",
    "meta_description": "",
    "is_active": true,
    "order": 0,
    "audio_file_count": 15,
    "children": [
      {
        "id": 11,
        "name": "Classical",
        "slug": "classical",
        "parent": "Music Genres",
        "description": "Classical music pieces.",
        "meta_title": "",
        "meta_description": "",
        "is_active": true,
        "order": 0,
        "audio_file_count": 8,
        "children": []
      }
    ]
  }
  ```
- **Response Example (Subcategory):**
  ```json
  {
    "id": 11,
    "name": "Classical",
    "slug": "classical",
    "parent": "Music Genres",
    "description": "Classical music pieces.",
    "meta_title": "",
    "meta_description": "",
    "is_active": true,
    "order": 0,
    "audio_file_count": 8,
    "children": []
  }
  ```

---

## 2. Audio Files Endpoints

### 2.1 List all Audio Files (with Filters and Pagination)

Retrieves a paginated list of published audio files. Supports various filters and pagination.

- **URL:** `/api/audio-manager/audio-files/`
- **Method:** `GET`
- **Pagination:**
    - **Default:** 10 items per page
    - **Page Size Parameter:** `page_size` (max 100)
    - **Page Parameter:** `page`
    - **Example:** `/api/audio-manager/audio-files/?page=2&page_size=20`

- **Filters:**
    - **`category`**: Filter audio files by the slug of their category.
      - **Example:** `/api/audio-manager/audio-files/?category=classical`
    - **`tags`**: Filter audio files by the slug of a specific tag.
      - **Example:** `/api/audio-manager/audio-files/?tags=instrumental`
    - **`is_published`**: Filter audio files by their published status.
      - **Values:** `true` or `false`
      - **Example:** `/api/audio-manager/audio-files/?is_published=true`

- **Combining Filters and Pagination:** You can combine multiple filters with pagination.
    - **Example:** `/api/audio-manager/audio-files/?category=classical&tags=instrumental&page=1&page_size=20`

- **Response Example (with pagination):**
  ```json
  {
    "count": 50,
    "next": "http://127.0.0.1:8000/api/audio-manager/audio-files/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "category": {
          "id": 11,
          "name": "Classical",
          "slug": "classical",
          "parent": "Music Genres",
          "description": "Classical music pieces.",
          "meta_title": "",
          "meta_description": "",
          "is_active": true
        },
        "tags": [
          {"id": 5, "name": "Instrumental", "slug": "instrumental"}
        ],
        "title": "Morning Mood",
        "slug": "morning-mood",
        "description": "A beautiful classical piece by Grieg.",
        "mp3_file": "http://127.0.0.1:8000/media/audio/morning_mood.mp3",
        "image": "http://127.0.0.1:8000/media/audio_images/morning_mood_cover.jpg",
        "meta_title": "Morning Mood by Grieg",
        "meta_description": "Listen to Grieg's Morning Mood.",
        "is_published": true,
        "published_date": "2025-11-14T12:00:00Z",
        "created_at": "2025-11-14T10:00:00Z",
        "updated_at": "2025-11-14T10:00:00Z"
      }
    ]
  }
  ```

**Pagination Response Fields:**
- `count`: Total number of audio files matching the filters
- `next`: URL to the next page (null if on last page)
- `previous`: URL to the previous page (null if on first page)
- `results`: Array of audio file objects (10 items per page by default)

### 2.2 Retrieve a Single Audio File by Slug

Retrieves the details of a single published audio file using its unique slug.

- **URL:** `/api/audio-manager/audio-files/{slug}/`
- **Method:** `GET`
- **Example:** `/api/audio-manager/audio-files/morning-mood/`
- **Response Example:** (Same as individual item in List Audio Files response above)

304|
305|# Mobile App Settings API Endpoints
306|
307|This document outlines the API endpoints for the `mobileapp_settings` application, providing carousel images for integration with your frontend.
308|
309|**Base URL for all Mobile App Settings API endpoints:** `http://127.0.0.1:8000/api/mobile-settings/`
310|
311|---
312|
313|## 1. Carousel Images Endpoints
314|
315|### 1.1 List all Active Carousel Images
316|
317|Retrieves a list of all active carousel images, ordered by their `order` field.
318|
319|- **URL:** `/api/mobile-settings/carousel-images/`
320|- **Method:** `GET`
321|- **Response Example:**
322|  ```json
323|  [
324|    {
325|      "id": 1,
326|      "heading": "Welcome to our App!",
327|      "description": "Discover amazing features and content.",
328|      "image": "http://127.0.0.1:8000/media/carousel_images/welcome_banner.jpg",
329|      "link": "https://example.com/welcome",
330|      "order": 1,
331|      "is_active": true,
332|      "created_at": "2025-11-15T10:00:00Z",
333|      "updated_at": "2025-11-15T10:00:00Z"
334|    },
335|    {
336|      "id": 2,
337|      "heading": "New Audio Collection",
338|      "description": "Explore our latest audio releases.",
339|      "image": "http://127.0.0.1:8000/media/carousel_images/audio_promo.jpg",
340|      "link": "http://127.0.0.1:8000/api/audio-manager/audio-files/",
341|      "order": 2,
342|      "is_active": true,
343|      "created_at": "2025-11-15T11:00:00Z",
344|      "updated_at": "2025-11-15T11:00:00Z"
345|    }
346|  ]
347|  ```
348|
349|### 1.2 Retrieve a Single Carousel Image by ID
350|
351|Retrieves the details of a single active carousel image using its primary key (ID).
352|
353|- **URL:** `/api/mobile-settings/carousel-images/{id}/`
354|- **Method:** `GET`
355|- **Example:** `/api/mobile-settings/carousel-images/1/`
356|- **Response Example:** (Same as individual item in List Active Carousel Images response above)

# Panchang Application API Endpoints

This document outlines the API endpoints for the `panchang` application, for integration with your frontend.

**Base URL for all Panchang API endpoints:** `http://127.0.0.1:8000/api/panchang/`

---

## 1. Panchang Endpoints

### 1.1 Today's Panchang

Retrieves the panchang (daily astrological almanac) for a specified date.

- **URL:** `/api/panchang/today/`
- **Method:** `GET`
- **Query Parameters:**
    - **`date`**: The date for which to retrieve the panchang, in `YYYY-MM-DD` format.
      - **Example:** `/api/panchang/today/?date=2025-12-25`
    - **`language`**: (Optional) The language code for the response. Defaults to `en` (English).
      - **Values:** `en` (English), `te` (Telugu), `hi` (Hindi), `ta` (Tamil), `kn` (Kannada), `bn` (Bengali), `gu` (Gujarati)
      - **Example:** `/api/panchang/today/?date=2025-12-25&language=te`

- **Response Example (Telugu):**
  ```json
  {
    "date": "2025-12-25",
    "భారత పౌర క్యాలెండర్": {
      "సంవత్సరం": 1947,
      "నెల": "పుష్యమాసం",
      "రోజు": 4
    },
    "అమాంత మాసం": {
      "పేరు": "మార్గశిరమాసం"
    },
    "పూర్ణిమాంత మాసం": {
      "పేరు": "పుష్యమాసం"
    },
    "పక్షం": {
      "పేరు": "బహుళపక్షం"
    },
    "సూర్యోదయం_చంద్రోదయం": {
      "సూర్యోదయం": {
        "విలువ": "06:37 AM"
      },
      "సూర్యాస్తమయం": {
        "విలువ": "05:43 PM"
      },
      "చంద్రోదయం": {
        "విలువ": "04:00 AM"
      },
      "చంద్రాస్తమయం": {
        "విలువ": "03:52 PM"
      }
    },
    "ముఖ్య పంచాంగం": {
      "తిథులు": [
        {
          "పేరు": "దశమి",
          "ఆర్డినల్": 10,
          "ప్రారంభం": "Dec 24 09:37 PM",
          "ముగింపు": "Dec 25 08:30 PM"
        },
        {
          "పేరు": "ఏకాదశి",
          "ఆర్డినల్": 11,
          "ప్రారంభం": "Dec 25 08:30 PM",
          "ముగింపు": "Dec 26 12:00 AM"
        }
      ],
      "నక్షత్రములు": [
        {
          "పేరు": "స్వాతి",
          "ఆర్డినల్": 15,
          "ప్రారంభం": "Dec 24 10:15 PM",
          "ముగింపు": "Dec 25 09:45 PM"
        },
        {
          "పేరు": "విశాఖ",
          "ఆర్డినల్": 16,
          "ప్రారంభం": "Dec 25 09:45 PM",
          "ముగింపు": "Dec 26 12:00 AM"
        }
      ],
      "కరణం": [
        {
          "పేరు": "వణిజ",
          "ఆర్డినల్": 6,
          "ప్రారంభం": "Dec 24 09:37 PM",
          "ముగింపు": "Dec 25 09:55 AM"
        },
        {
          "పేరు": "విష్టి",
          "ఆర్డినల్": 7,
          "ప్రారంభం": "Dec 25 09:55 AM",
          "ముగింపు": "Dec 25 08:30 PM"
        },
        {
          "పేరు": "భవ",
          "ఆర్డినల్": 1,
          "ప్రారంభం": "Dec 25 08:30 PM",
          "ముగింపు": "Dec 26 12:00 AM"
        }
      ],
      "యోగం": [
        {
          "పేరు": "శోభన",
          "ఆర్డినల్": 7,
          "ప్రారంభం": "Dec 24 08:00 PM",
          "ముగింపు": "Dec 25 08:00 PM"
        },
        {
          "పేరు": "అతిగండ",
          "ఆర్డినల్": 8,
          "ప్రారంభం": "Dec 25 08:00 PM",
          "ముగింపు": "Dec 26 12:00 AM"
        }
      ]
    },
    "శుభ సమయాలు": {
      "అభిజిత్ ముహూర్తం": {
        "విలువ": "12:00 PM - 12:48 PM"
      },
      "అమృత కాలం": {
        "విలువ": "09:28 PM - 10:53 PM"
      },
      "బ్రహ్మ ముహూర్తం": {
        "విలువ": "05:01 AM - 05:50 AM"
      },
      "ప్రాతః సంధ్య": {
        "విలువ": "06:22 AM - 07:37 AM"
      },
      "విజయ ముహూర్తం": {
        "విలువ": "03:19 PM - 04:07 PM"
      },
      "గోధూళి ముహూర్తం": {
        "విలువ": "05:28 PM - 05:58 PM"
      },
      "సాయాహ్న సంధ్య": {
        "విలువ": "05:43 PM - 06:58 PM"
      },
      "నిశిత ముహూర్తం": {
        "విలువ": "11:50 PM - 12:38 AM"
      }
    },
    "అశుభ సమయాలు": {
      "రాహు కాలం": {
        "విలువ": "01:31 PM - 02:50 PM"
      },
      "యమగండం": {
        "విలువ": "06:37 AM - 07:56 AM"
      },
      "గుళిక కాలం": {
        "విలువ": "09:15 AM - 10:34 AM"
      }
    },
    "హోరాస్": {
      "పగలు": [
        "గురుడు: 06:37 AM - 07:34 AM",
        "కుజుడు: 07:34 AM - 08:31 AM",
        "సూర్యుడు: 08:31 AM - 09:28 AM",
        "శుక్రుడు: 09:28 AM - 10:25 AM",
        "బుధుడు: 10:25 AM - 11:22 AM",
        "చంద్రుడు: 11:22 AM - 12:19 PM",
        "శని: 12:19 PM - 01:16 PM",
        "గురుడు: 01:16 PM - 02:13 PM",
        "కుజుడు: 02:13 PM - 03:10 PM",
        "సూర్యుడు: 03:10 PM - 04:07 PM",
        "శుక్రుడు: 04:07 PM - 05:04 PM",
        "బుధుడు: 05:04 PM - 06:01 PM"
      ],
      "రాత్రి": [
        "చంద్రుడు: 05:43 PM - 06:40 PM",
        "శని: 06:40 PM - 07:37 PM",
        "గురుడు: 07:37 PM - 08:34 PM",
        "కుజుడు: 08:34 PM - 09:31 PM",
        "సూర్యుడు: 09:31 PM - 10:28 PM",
        "శుక్రుడు: 10:28 PM - 11:25 PM",
        "బుధుడు: 11:25 PM - 12:22 AM",
        "చంద్రుడు: 12:22 AM - 01:19 AM",
        "శని: 01:19 AM - 02:16 AM",
        "గురుడు: 02:16 AM - 03:13 AM",
        "కుజుడు: 03:13 AM - 04:10 AM",
        "సూర్యుడు: 04:10 AM - 05:07 AM"
      ]
    },
    "పండుగలు": []
  }
  ```


  bulk upload the images

  http://127.0.0.1:8000/api/wallpapers/bulk-upload/

---

# Wallpaper Manager Application API Endpoints

This document outlines the API endpoints for the `wallpaper_manager` application.

**Base URL for all Wallpaper API endpoints:** `http://127.0.0.1:8000/api/wallpapers/`

---

## 1. Main Categories Endpoint

### 1.1 List all Main Categories

Retrieves a list of all active main categories.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/categories/`
- **Method:** `GET`

---

## 2. Sub Categories Endpoint

### 2.1 Get Sub Categories by Main Category

Retrieves all subcategories for a specific main category. Accepts both ID or slug. Use this endpoint by providing `main_category_id` or `main_category` parameter without `sub_category_id` or `sub_category`.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/`
- **Method:** `GET`
- **Query Parameters:**
  - **`main_category_id`**: (Required) Main category ID
  - **`main_category`**: (Optional) Main category slug (alternative to main_category_id)
- **Examples:**
  - `http://127.0.0.1:8000/api/wallpapers/wallpapers/?main_category_id=1`
  - `http://127.0.0.1:8000/api/wallpapers/wallpapers/?main_category=shiva-god-wallpapers`

---

## 3. Wallpapers Endpoints

### 3.1 List Wallpapers by Sub Category

Retrieves a paginated list of wallpapers filtered by sub category. Returns 10 items per page. Accepts both ID or slug.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/`
- **Method:** `GET`
- **Query Parameters:**
  - **`sub_category_id`**: (Optional) Sub category ID
  - **`sub_category`**: (Optional) Sub category slug
  - **`page`**: (Optional) Page number (default: 1)
  - **`page_size`**: (Optional) Items per page (default: 10, max: 100)
- **Pagination Response Format:**
  ```json
  {
    "count": 50,
    "next": "http://127.0.0",
    "previous": null,
    "results": [...]
  }.1:8000/api/wallpapers/wallpapers/?sub_category_id=5&page=2
  ```
- **Examples:**
  - Get first page (10 items): `http://127.0.0.1:8000/api/wallpapers/wallpapers/?sub_category_id=5`
  - Get second page: `http://127.0.0.1:8000/api/wallpapers/wallpapers/?sub_category_id=5&page=2`
  - Get third page: `http://127.0.0.1:8000/api/wallpapers/wallpapers/?sub_category_id=5&page=3`
  - Custom page size (20 items per page): `http://127.0.0.1:8000/api/wallpapers/wallpapers/?sub_category_id=5&page=2&page_size=20`
  - Using slug: `http://127.0.0.1:8000/api/wallpapers/wallpapers/?sub_category=mountains&page=2`

### 3.2 Retrieve a Single Wallpaper

Retrieves the details of a single wallpaper by ID.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/{id}/`
- **Method:** `GET`
- **Example:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/1/`

### 3.3 Increment View Count

Increments the view count for a wallpaper.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/{id}/increment_view/`
- **Method:** `POST`
- **Example:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/1/increment_view/`

### 3.4 Increment Download Count

Increments the download count for a wallpaper.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/{id}/increment_download/`
- **Method:** `POST`
- **Example:** `http://127.0.0.1:8000/api/wallpapers/wallpapers/1/increment_download/`

---

## 4. Bulk Upload Endpoint

### 4.1 Bulk Upload Page

Renders the bulk upload HTML page with Dropzone.js interface.

- **URL:** `http://127.0.0.1:8000/api/wallpapers/bulk-upload/`
- **Method:** `GET`