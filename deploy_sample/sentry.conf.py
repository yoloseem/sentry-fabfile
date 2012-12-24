DATABASES = {  'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'sentry',
    'USER': 'sentry',
    'PASSWORD': 'sentry',
    'HOST': 'localhost',
    'PORT': '',
  }
}

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = 9000
SENTRY_WEB_OPTIONS = { 'workers': 2, 'worker_class': 'gevent' }
