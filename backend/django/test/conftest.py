import pytest
import redis

from django.conf import settings
from django.contrib.auth import get_user_model
from smart.celery import app as celery_app
from core.management.commands.seed import (
    seed_database, SEED_USERNAME)
from core.models import (User)
from core.util import (create_project, add_queue,
                       create_user, add_data)

from test.util import read_test_data

TEST_QUEUE_LEN = 10

@pytest.fixture()
def seeded_database(db):
    # Seed the database using the management command
    seed_database()

@pytest.fixture(autouse=True)
def setup_celery():
    celery_app.conf.update(CELERY_ALWAYS_EAGER=True)

@pytest.fixture(scope='function')
def test_redis(request):
    r = settings.REDIS

    # Teardown by removing all keys when we're done with the fixture
    def teardown():
        r.flushdb()
    request.addfinalizer(teardown)

    return r

@pytest.fixture
def test_project(db):
    '''
    This fixture only creates the test project without any data.
    '''
    return create_project('test_project')

@pytest.fixture
def test_project_data(db, test_project):
    '''
    Creates the test project and adds test data to it.
    '''
    test_data = read_test_data()
    add_data(test_project, test_data)
    return test_project

@pytest.fixture
def test_user(db):
    '''
    Creates a test user with associated auth_user.
    '''
    return create_user('test_user', 'password', 'test_user@rti.org')

@pytest.fixture
def test_user2(db):
    '''
    Additional user for tests requiring multiple users.
    '''
    return create_user('test_user2', 'password', 'test_user2@rti.org')

@pytest.fixture
def test_queue(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN)

@pytest.fixture
def test_user_queue(db, test_user, test_project_data):
    '''
    A queue with test data, associated with the first test user.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, user=test_user)

@pytest.fixture
def test_user_queue2(db, test_user2, test_project_data):
    '''
    A queue with test data, associated with an additional test user.
    Useful for tests requiring multiple users/queues on the same project.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, user=test_user2)
