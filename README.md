# Panchang API - Django REST Framework

A Django REST API for Panchang calculations, festivals, and important days with MySQL database support.

## Setup Instructions

### 1. Install Dependencies

```bash
cd panchang_api
pip install -r requirements.txt
```

**Note:** This project uses `PyMySQL` (pure Python) instead of `mysqlclient`, so it works on Windows without requiring C++ build tools.

### 2. Configure MySQL Database

Create a MySQL database:

```sql
CREATE DATABASE panchang_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update database settings in `panchang_api/settings.py` or set environment variables:

```bash
export DB_NAME=panchang_db
export DB_USER=root
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Load Data into Database

Load festivals:
```bash
python manage.py load_festivals --file ../panchang_calculator/festivals_panchangam_style.json
```

Load important days:
```bash
python manage.py load_important_days --file ../panchang_calculator/important_days_india.json
```

To clear existing data and reload:
```bash
python manage.py load_festivals --clear
python manage.py load_important_days --clear
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

## API Endpoints

### Festivals

- `GET /api/festivals/` - List all festivals
- `GET /api/festivals/{id}/` - Get specific festival
- `GET /api/festivals/by_month/?month=Chaitra` - Filter by month
- `GET /api/festivals/by_tithi/?tithi=Ekadashi&paksha=Shukla` - Filter by tithi and paksha

**Query Parameters:**
- `type` - Filter by festival type
- `importance` - Filter by importance (Major, Moderate, Minor)
- `month` - Filter by month
- `paksha` - Filter by paksha (Shukla, Krishna)
- `tithi` - Filter by tithi
- `calculation_type` - Filter by calculation type (lunar, solar, unspecified)
- `search` - Search in festival_name, description, month
- `ordering` - Order by festival_name, importance, month

### Important Days

- `GET /api/important-days/` - List all important days
- `GET /api/important-days/{id}/` - Get specific important day
- `GET /api/important-days/by_date/?date=25 December` - Filter by date

**Query Parameters:**
- `type_of` - Filter by type
- `importance` - Filter by importance
- `is_holiday` - Filter by holiday type
- `search` - Search in day_name, description, date
- `ordering` - Order by date, day_name, importance

### Panchang Calculation

- `POST /api/panchang/calculate/` - Calculate Panchang for a date

**Request Body:**
```json
{
    "date": "2025-12-25",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "timezone": "Asia/Kolkata",
    "profile_code": "te",
    "format_profile": true
}
```

**Response:** Localized Panchang data in JSON format

### Amavasya Dates

- `GET /api/panchang/amavasya/?year=2025` - Get all Amavasya dates in a year

**Query Parameters:**
- `year` (required) - Year to search
- `latitude` (optional) - Latitude (default: 13.0827)
- `longitude` (optional) - Longitude (default: 80.2707)
- `timezone` (optional) - Timezone (default: Asia/Kolkata)

## Language Codes

- `en` - English
- `te` - Telugu
- `hi` - Hindi
- `ta` - Tamil
- `kn` - Kannada
- `bn` - Bengali
- `gu` - Gujarati

## Example API Calls

### Get festivals for Chaitra month:
```bash
curl http://localhost:8000/api/festivals/?month=Chaitra
```

### Calculate Panchang in Telugu:
```bash
curl -X POST http://localhost:8000/api/panchang/calculate/ \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-12-25", "profile_code": "te"}'
```

### Get Amavasya dates for 2025:
```bash
curl http://localhost:8000/api/panchang/amavasya/?year=2025
```

## Database Models

### Festival
- Stores lunar/solar festival information
- Indexed on festival_name, month, tithi, paksha
- Supports filtering and searching

### ImportantDay
- Stores Gregorian calendar important days
- Indexed on date, day_name, is_holiday
- Supports filtering and searching

