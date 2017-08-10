import pytest
import redis

from django.conf import settings
from django.contrib.auth import get_user_model
from smart.celery import app as celery_app
from core.management.commands.seed import (
    seed_database, SEED_USERNAME)
from core.models import (User)
from core.util import (create_project, add_queue,
                       add_data)

from test.util import read_test_data

TEST_QUEUE_LEN = 10

@pytest.fixture()
def seeded_database(db):
    # Seed the database using the management command
    seed_database()

@pytest.fixture(autouse=True)
def setup_celery():
    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)

@pytest.fixture
def test_redis():
    r = redis.StrictRedis.from_url(settings.REDIS_URL)
    yield r

    # Teardown by removing all keys when we're done with the fixture
    r.flushdb()


@pytest.fixture
def test_project(db):
    return create_project('test_project')

@pytest.fixture
def test_project_data(db, test_project):
    test_data = read_test_data()
    add_data(test_project, test_data)
    return test_project

@pytest.fixture
def test_user(db):
    auth_user = get_user_model()(username=SEED_USERNAME)
    return User.objects.filter(auth_user=auth_user).first()

@pytest.fixture
def test_queue(db, test_project_data):
    return add_queue(test_project_data, TEST_QUEUE_LEN)
