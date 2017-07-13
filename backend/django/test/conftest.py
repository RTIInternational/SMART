import pytest

from smart.celery import app as celery_app
from core.management.commands.seed import seed_database

@pytest.fixture(autouse=True)
def setup_database(db):
    seed_database()

@pytest.fixture(autouse=True)
def setup_celery():
    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)
