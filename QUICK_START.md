# Quick Start Guide

## Database Configuration

The project is pre-configured with these default database settings:
- **Database Name:** `panchang_db`
- **User:** `root`
- **Password:** (empty - set if your MySQL has a password)
- **Host:** `localhost`
- **Port:** `3306`

### Option 1: Use Default Settings (No Password)
If your MySQL root user has no password, you can use the defaults directly.

### Option 2: Set Environment Variables (Recommended)

**Windows PowerShell:**
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

### Option 3: Create local_settings.py
1. Copy `local_settings.example.py` to `local_settings.py`
2. Update the `DATABASE_CONFIG` dictionary with your credentials
3. The settings will automatically load from this file

## Quick Setup Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set database password (if needed):**
   ```powershell
   # Windows PowerShell
   $env:DB_PASSWORD="your_mysql_password"
   ```

3. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Load data:**
   ```bash
   python manage.py load_festivals --file ../panchang_calculator/festivals_panchangam_style.json
   python manage.py load_important_days --file ../panchang_calculator/important_days_india.json
   ```

5. **Run server:**
   ```bash
   python manage.py runserver
   ```

6. **Test API:**
   ```
   http://localhost:8000/api/festivals/
   ```




