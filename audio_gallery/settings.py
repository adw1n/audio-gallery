import os
import typing
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

    # I'd rather do
    # generate_secret_key(secret_key_file)
    # from .secret_key import SECRET_KEY
    # than:
    # SECRET_KEY=generate_secret_key(secret_key_file)
    # but I'm randomly getting those errors:
    # ImportError: No module named 'audio_gallery.secret_key'
    # django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.
    # or sometimes it works
    # without docker it works reliably 100% of time
    # I am confused, I'll investigate this some other time
    # notes to myself in the future:
    # docker-compose version 1.10.0, build 4bd6f1a
    # Docker version 1.12.6, build 78d1802, host ubuntu 15.10
    # ubuntu 16.04 Python 3.5.2 Django==1.10.6
    # print(os.path.isfile(secret_key_file)) prints True
    # with open(secret_key_file,"r") as file:
    #     print(file.read())
    # prints the secret file just fine
    # time.sleep does not help
    # secret_key_file.flush()
    # os.fsync(secret_key_file.fileno()) does not help (obviously...)
    # checked sys.modules - nothing weird there
    # another weird thing is that if I run this code in try: ... except django.core.exceptions.ImproperlyConfigured:
    # I can't seem to be able to catch the exception ImproperlyConfigured - TODO check why

try:
    __debug_env_var = os.environ['DJANGO_DEBUG']
except KeyError:
    DEBUG = True
else:
    DEBUG = bool(distutils.util.strtobool(__debug_env_var))

ALLOWED_HOSTS = ['*']

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
        'LOCATION': '127.0.0.1:11211',
    }
}

DATABASE_DIR=os.environ.get('DJANGO_DATABASE_DIR', os.path.join(BASE_DIR, '../database/'))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATABASE_DIR, 'db.sqlite3'),
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

# little heads up - if you are testing the app locally using the manage.py runserver command, you might experience some
# problems with the audio that plays in your browser not being seekable - related stackoverflow thread:
# http://stackoverflow.com/questions/4538810/html5-video-element-non-seekable-when-using-django-development-server
if DEBUG:
    import mimetypes
    mimetypes.add_type("audio/wav", ".wav", True)
