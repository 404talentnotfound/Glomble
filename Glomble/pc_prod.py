"""
Django settings for Glomble project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = open(os.path.join(BASE_DIR, "secret_key.txt")).read()

CREATOR_ID = open(os.path.join(BASE_DIR, "creator.txt")).read()
DEVELOPER_IDS = open(os.path.join(BASE_DIR, "developers.txt")).read().split("\n")
SUPPORTER_IDS = open(os.path.join(BASE_DIR, "supporters.txt")).read().split("\n")

MILESTONES = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

LOGIN_URL = 'login'

ALLOWED_HOSTS = ['glomble.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://*.glomble.com']

CRISPY_TEMPLATE_PACK = 'bootstrap5'

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "media/"

CRONJOBS = [
    ('0 13 * * MON', 'videos.cron.reset_recommendations'),
    ('0 */8 * * *', 'profiles.cron.reset_recommendations_left')
]

INSTALLED_APPS = [
    'dumbshit',
    'django_crontab',

    'creatorfund',
    'notifications',
    'videos',
    'profiles',
    'comments',
    'reports',
    'crispy_forms',
    'crispy_bootstrap5',

    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

ROOT_URLCONF = 'Glomble.urls'

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

WSGI_APPLICATION = 'Glomble.wsgi.application'

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (os.path.join(BASE_DIR, "profiles/static"), os.path.join(BASE_DIR, "videos/static"))

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_POST = 587
EMAIL_USE_TLS = True

with open(os.path.join(BASE_DIR, 'email.txt')) as f:
    EMAIL_HOST_USER = f.read().strip()
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
with open(os.path.join(BASE_DIR, 'email_pass.txt')) as f:
    EMAIL_HOST_PASSWORD = f.read().strip()

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'profiles.middleware.CheckProfileMiddleware',
    'allauth.account.middleware.AccountMiddleware'
]

SITE_ID = 2

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}