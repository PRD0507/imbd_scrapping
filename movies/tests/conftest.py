import os
import django
import pytest
import sys

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imdb_scraper.settings')
django.setup()

if 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass 