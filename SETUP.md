# Quick Setup Guide

## Step 1: Install Python Dependencies

```bash
cd panchang_api
pip install -r requirements.txt
```

**Note:** This project uses `PyMySQL` which is a pure Python MySQL client and works on all platforms including Windows without requiring C++ compilers.

## Step 2: Create MySQL Database

```sql
CREATE DATABASE panchang_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Step 3: Configure Database Settings

Edit `panchang_api/settings.py` or set environment variables:

**Windows (PowerShell):**
```powershell
$env:DB_NAME="panchang_db"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
```

**Linux/Mac:**
```bash
export DB_NAME=panchang_db
export DB_USER=root
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306
```

## Step 4: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 5: Load Data

```bash
# Load festivals
python manage.py load_festivals --file ../panchang_calculator/festivals_panchangam_style.json

# Load important days
python manage.py load_important_days --file ../panchang_calculator/important_days_india.json
```

## Step 6: Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

## Step 7: Run Server

```bash
python manage.py runserver
```

API will be available at: `http://localhost:8000/api/`

## Testing APIs

### Get all festivals:
```
GET http://localhost:8000/api/festivals/
```

### Get festivals by month:
```
GET http://localhost:8000/api/festivals/?month=Chaitra
```

### Calculate Panchang:
```
POST http://localhost:8000/api/panchang/calculate/
Content-Type: application/json

{
    "date": "2025-12-25",
    "profile_code": "te"
}
```

### Get Amavasya dates:
```
GET http://localhost:8000/api/panchang/amavasya/?year=2025
```

