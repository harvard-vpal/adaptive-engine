from config.settings.base import *

SECRET_KEY = 'sp(j(ts6ri()muwz-$^i+k+jgjfv$jbgs@9oq@lzy6x5@lynqd'

INSTALLED_APPS += [
    'django_extensions',
    'tests',
]

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'engine',
        'USER': 'postgres',
        'HOST': 'postgres',
        'PASSWORD': 'postgres',
        'PORT': 5432,
    }
}
