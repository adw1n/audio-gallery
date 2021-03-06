import os
import distutils.util

from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_secret_key(file: str)->str:
    from django.utils.crypto import get_random_string
    # key is generated in the same way as in django startproject command
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    random_secret_key=get_random_string(50, chars)
    with open(file,"w+") as secret_key_file:
        secret_key_file.write('SECRET_KEY = "%s"\n'%random_secret_key)
    return random_secret_key


# This way of handling secret key creation has been suggested in:
# http://stackoverflow.com/questions/4664724/distributing-django-projects-with-unique-secret-keys
try:
    from .secret_key import SECRET_KEY
except ImportError:
    SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
    secret_key_file = os.path.join(SETTINGS_DIR, 'secret_key.py')
    SECRET_KEY=generate_secret_key(secret_key_file)

try:
    __debug_env_var = os.environ['DJANGO_DEBUG']
except KeyError:
    DEBUG = True
else:
    DEBUG = bool(distutils.util.strtobool(__debug_env_var))

try:
    ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(':')
except KeyError:
    ALLOWED_HOSTS = ['*']

try:
    ADMINS = [('admin', os.environ["ADMINS"])]
except KeyError:
    pass

INSTALLED_APPS = (
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'audio_profiling'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'audio_gallery.urls'

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

WSGI_APPLICATION = 'audio_gallery.wsgi.application'

#using memcache only for celery to be able to use locking
#cache middleware is not added
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.environ.get('MEMCACHED_HOST', '127.0.0.1')+':11211',
    }
}

# RabbitMQ
CELERY_BROKER_URL = 'amqp://{0}:{1}@{2}:5672//'.format(
    os.environ.get('RABBIT_USER', 'guest'),
    os.environ.get('RABBIT_PASSWORD', 'guest'),
    os.environ.get('RABBIT_HOST', '127.0.0.1'))


DATABASE_DIR=os.environ.get('DJANGO_DATABASE_DIR', os.path.join(BASE_DIR, '../database/'))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'audiogallery',
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': '5432',
    }
}

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

LOGS_DIR = os.environ.get('DJANGO_LOGS_DIR', os.path.join(BASE_DIR, '..', 'logs'))
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
        'verbose': {
            'format': '[%(levelname)s] [%(asctime)s] [logger: %(name)s file: %(pathname)s function: %(funcName)s line: %(lineno)d]'
                      ' [proc: %(process)d thread: %(thread)d]\n%(message)s'
        },
    },
    'filters':{
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'django_log_file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 50*(1024**2), #50MB
            'backupCount': 5,
            'encoding': 'utf-8',
            'filename': '%s' % (os.path.join(LOGS_DIR, "django.log")),
            'formatter': 'verbose'
        },
        'celery_log_file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 50*(1024**2), #50MB
            'backupCount': 5,
            'encoding': 'utf-8',
            'filename': '%s' % (os.path.join(LOGS_DIR, "django_celery.log")),
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false']
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console','django_log_file','mail_admins'],
            'propagate': True
        },
        'django.request': {
            'handlers': ['console','django_log_file','mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console','celery_log_file','mail_admins'],
            'level': 'DEBUG',
        },
        'audio_profiling': {
            'handlers': ['console', 'django_log_file','mail_admins'],
            'level': 'DEBUG'
        }
    }
}

LANGUAGES = [
    ('en', _('English')),
    ('pl', _('Polish')),
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(BASE_DIR, '../static'))

MEDIA_URL='/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, '../media'))
FILE_UPLOAD_PERMISSIONS = 0o644  # nginx was not able to read .wav files - those were being created with permissions 600

# little heads up - if you are testing the app locally using the manage.py runserver command, you might experience some
# problems with the audio that plays in your browser not being seekable - related stackoverflow thread:
# http://stackoverflow.com/questions/4538810/html5-video-element-non-seekable-when-using-django-development-server
if DEBUG:
    import mimetypes
    mimetypes.add_type("audio/wav", ".wav", True)
