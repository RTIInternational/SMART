import pytest

from django.contrib.auth import get_user_model
from smart.celery import app as celery_app
from core.management.commands.seed import (
    seed_database, SEED_USERNAME)
from core.models import (User)
from core.util import (create_project)

from test.util import read_test_data

@pytest.fixture(autouse=True, scope='session')
def setup_database(django_db_setup, django_db_blocker):
    # Set up the database only once per session
    with django_db_blocker.unblock():
        seed_database()

@pytest.fixture(autouse=True)
def setup_celery():
    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)

@pytest.fixture
def test_project():
    project_attrs = { 'name': 'test_project' }
    data = read_test_data()
    project = create_project(project_attrs, data)
    return project

@pytest.fixture
def test_user():
    auth_user = get_user_model()(username=SEED_USERNAME)
    return User.objects.filter(auth_user=auth_user).first()
