"""
Django settings for panchang_api project.
"""

from pathlib import Path
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

import pymysql

load_dotenv()
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*", "192.168.1.2"]

# Check if running on localhost
# Option 1: Check environment variable (set IS_LOCALHOST=true in .env for localhost)
IS_LOCALHOST = os.environ.get("IS_LOCALHOST", "").lower() in ("true", "1", "yes")

# Option 2: Auto-detect localhost based on hostname or if DEBUG is True
# (You can also manually set IS_LOCALHOST=true in your .env file for more control)
if not IS_LOCALHOST:
    try:
        import socket
        hostname = socket.gethostname()
        localhost_indicators = ['localhost', '127.0.0.1', 'local', 'DESKTOP', 'LAPTOP']
        # Check if hostname contains localhost indicators or if it's a typical dev machine name
        IS_LOCALHOST = any(indicator.lower() in hostname.lower() for indicator in localhost_indicators)
    except Exception:
        # If detection fails, default to False (safer for production)
        IS_LOCALHOST = False

# Base installed apps
INSTALLED_APPS = [
    'adminsortable2',
    'taggit',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'ckeditor',
    'ckeditor_uploader',
    'panchang',
    'posts',
    # 'audio_manager',
    'audio_manager',
    'mobileapp_settings',
    'wallpaper_manager',
    'chanting',
]

# Add debugging tools only on localhost
if IS_LOCALHOST:
    INSTALLED_APPS.insert(0, 'silk')
    INSTALLED_APPS.append('debug_toolbar')

# Base middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add debugging middleware only on localhost
if IS_LOCALHOST:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE.append('silk.middleware.SilkyMiddleware')

ROOT_URLCONF = 'panchang_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'panchang_api.wsgi.application'

# Database configuration
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL is not set")

u = urlparse(db_url)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": u.path.lstrip("/"),
        "USER": u.username,
        "PASSWORD": u.password,
        "HOST": u.hostname,
        "PORT": u.port or 3306,
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = False # Temporarily set to False to bypass MySQL timezone issues on Windows



# --------------------
# STATIC FILES
# --------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --------------------
# MEDIA FILES (WORKS ON LOCAL + COOLIFY)
# --------------------

MEDIA_URL = '/media/'

# If MEDIA_ROOT is set in environment (Coolify), use it
# Else fallback to local project media folder
MEDIA_ROOT = os.getenv(
    'MEDIA_ROOT',
    os.path.join(BASE_DIR, 'media')
)

# --------------------
# PANCHANG FILES (SUB-FOLDER INSIDE MEDIA)
# --------------------
PANCHANG_FILES_URL = f'{MEDIA_URL}panchang_files/'
PANCHANG_FILES_ROOT = os.path.join(MEDIA_ROOT, 'panchang_files')




# Autoreloader settings to mitigate WinError 123
os.environ.setdefault('DJANGO_AUTORELOAD_MAX_RETRIES', '10')
os.environ.setdefault('DJANGO_AUTORELOAD_RETRY_DELAY', '0.1')

# Django Debug Toolbar configuration (only on localhost)
if IS_LOCALHOST:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]
    # Additional configuration for Debug Toolbar
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: IS_LOCALHOST,
    }

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source'],
            ['Image', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Maximize'],
        ],
        'toolbar': 'Custom',
        'extraPlugins': ','.join([
            'uploadimage',  # the upload image feature
            'div',
            'autolink',
            'autoembed',
            'embedsemantic',
            'autogrow',
            'widget',
            'lineutils',
            'clipboard',
            'dialog',
            'dialogui',
            'elementspath'
        ]),
        'filebrowserBrowseUrl': '/ckeditor/browse/',
        'filebrowserUploadUrl': '/ckeditor/upload/',
    },
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = DEBUG  # Run tasks synchronously in DEBUG mode
CELERY_TASK_EAGER_PROPAGATES = DEBUG  # Propagate exceptions in DEBUG mode

CORS_ALLOW_ALL_ORIGINS = True

# Image Size Settings for Mobile View
# You can add as many sizes as needed - the system will automatically create folders and generate images for each size
IMAGE_SIZES = {
    'thumb': 200,   # 200px width
    'medium': 600,  # 400px width
    'large': 800,   # 800px width
    # Add more sizes below as needed:
    # 'xlarge': 1200,  # 1200px width
    # 'xxlarge': 1600,  # 1600px width
}

# WhiteNoise static files storage
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
