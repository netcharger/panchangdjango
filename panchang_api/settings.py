"""
Django settings for panchang_api project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()


import pymysql
pymysql.install_as_MySQLdb()



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")


print(SECRET_KEY)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*", "192.168.1.2"]

# Application definition
INSTALLED_APPS = [
    'silk',
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
    'debug_toolbar',
    'audio_manager',
    'mobileapp_settings',
    'wallpaper_manager',
    'chanting',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE') or os.environ.get('DB_NAME'),
        'USER': os.environ.get('MYSQL_USER') or os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD') or os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('MYSQL_HOST') or os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('MYSQL_PORT') or os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Panchang files (JSON files)
PANCHANG_FILES_URL = '/panchang_files/'
PANCHANG_FILES_ROOT = os.path.join(BASE_DIR, 'panchang_files')

# Autoreloader settings to mitigate WinError 123
import os
os.environ.setdefault('DJANGO_AUTORELOAD_MAX_RETRIES', '10')
os.environ.setdefault('DJANGO_AUTORELOAD_RETRY_DELAY', '0.1')

# Django Debug Toolbar configuration
INTERNAL_IPS = [
    "127.0.0.1",
]

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
CELERY_TASK_EAGER_PROPAGATES = DEBUG # Propagate exceptions in DEBUG mode

CORS_ALLOW_ALL_ORIGINS = True

# Image Size Settings for Mobile View
# You can add as many sizes as needed - the system will automatically create folders and generate images for each size
IMAGE_SIZES = {
    'thumb': 200,   # 200px width
    'medium': 600,  # 400px width
    'large': 800,   # 800px width
    # Add more sizes below as needed:
    # 'xlarge': 1200,  # 1200px width
    # 'xxlarge': 1600, # 1600px width

}

#

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "panchang_files"),  # Add this line
]