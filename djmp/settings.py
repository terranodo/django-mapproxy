
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ENABLE_GUARDIAN_PERMISSIONS = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'e#i*49t%&&=jbfs64hb8(fj(m8gqicz9h3+!3(y#(9k!uu#sd!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djmp',
    'guardian'
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    'guardian.backends.ObjectPermissionBackend',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djmp.middleware.GuardianAuthenticationMiddleware',
)

ROOT_URLCONF = 'djmp.urls'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

TILESET_CACHE_DIRECTORY = getattr(settings, 'TILESET_CACHE_DIRECTORY', os.path.join(BASE_DIR, 'cache/layers'))
TILESET_CACHE_URL = getattr(settings, 'TILESET_CACHE_URL', 'cache/layers')

TASTYPIE_DEFAULT_FORMATS = ['json']

DJMP_AUTHORIZATION_CLASS = getattr(settings, 'DJMP_AUTHORIZATION_CLASS', 'tastypie.authorization.DjangoAuthorization')
