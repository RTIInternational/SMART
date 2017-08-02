import pytest

from smart.celery import app as celery_app
from core.management.commands.seed import seed_database

@pytest.fixture(autouse=True, scope='session')
def setup_database(django_db_setup, django_db_blocker):
    # Set up the database only once per session
    with django_db_blocker.unblock():
        seed_database()

@pytest.fixture(autouse=True)
def setup_celery():
    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)
