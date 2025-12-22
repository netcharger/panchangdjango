"""
Database configuration helper
You can modify these values directly or use environment variables
"""
import os

# Database Configuration
DB_CONFIG = {
    'NAME': os.environ.get('DB_NAME', 'panchang_db'),
    'USER': os.environ.get('DB_USER', 'root'),
    'PASSWORD': os.environ.get('DB_PASSWORD', ''),
    'HOST': os.environ.get('DB_HOST', 'localhost'),
    'PORT': os.environ.get('DB_PORT', '3306'),
}

# To set these in Windows PowerShell:
# $env:DB_NAME="panchang_db"
# $env:DB_USER="root"
# $env:DB_PASSWORD="your_password"
# $env:DB_HOST="localhost"
# $env:DB_PORT="3306"

# To set these in Linux/Mac:
# export DB_NAME=panchang_db
# export DB_USER=root
# export DB_PASSWORD=your_password
# export DB_HOST=localhost
# export DB_PORT=3306

