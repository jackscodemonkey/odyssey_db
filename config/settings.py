#######################
# Odyssey settings file.
#######################

import os

# Toggle debug
DEBUG = os.environ.get('ODYSSEY_DEBUG')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = {
    'NAME': os.environ.get('ODYSSEY_DB_NAME'),
    'USER': os.environ.get('ODYSSEY_DB_USER'),
    'PASSWORD': os.environ.get('ODYSSEY_DB_PASSWD'),
    'HOST': os.environ.get('ODYSSEY_DB_HOST'),
    'PORT': os.environ.get('ODYSSEY_DB_PORT'),
}

SQL_SRC = os.path.join(BASE_DIR, 'src')

MIGRATION_FOLDER = os.path.join(BASE_DIR, 'migrations')

LOGGING = {
    'format': '%(asctime)s [%(levelname)s] [%(module)s] - %(message)s',
}
