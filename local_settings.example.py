"""
Local settings example - Copy this to local_settings.py and update with your values
This file is gitignored and won't be committed to version control
"""
# Database Configuration
# Update these values with your MySQL database credentials

DATABASE_CONFIG = {
    'NAME': 'panchang_db',
    'USER': 'root',
    'PASSWORD': '',  # Set your MySQL password here
    'HOST': 'localhost',
    'PORT': '3306',
}

# To use this configuration, copy this file to local_settings.py
# and import it in settings.py, or set environment variables:
#
# Windows PowerShell:
#   $env:DB_NAME="panchang_db"
#   $env:DB_USER="root"
#   $env:DB_PASSWORD="your_password"
#   $env:DB_HOST="localhost"
#   $env:DB_PORT="3306"
#
# Linux/Mac:
#   export DB_NAME=panchang_db
#   export DB_USER=root
#   export DB_PASSWORD=your_password
#   export DB_HOST=localhost
#   export DB_PORT=3306




