import pytest
import redis
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from smart.celery import app as celery_app
from core.management.commands.seed import (
    seed_database, SEED_USERNAME, SEED_LABELS)
from core.models import (Profile, Label, Model, DataLabel)
from core.util import (create_project, add_queue,
                       create_profile, add_data,
                       create_tfidf_matrix, save_tfidf_matrix,
                       train_and_save_model, predict_data)

from test.util import read_test_data

TEST_QUEUE_LEN = 10

# Before starting any tests clear the redis cache
def pytest_sessionstart(session):
    r = settings.REDIS

    for key in r.scan_iter():
        r.delete(key)

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
def test_project(db, test_profile):
    '''
    This fixture only creates the test project without any data.
    '''
    return create_project('test_project', test_profile)

@pytest.fixture
def test_project_data(db, test_project):
    '''
    Creates the test project and adds test data to it.
    '''
    test_data = read_test_data()
    add_data(test_project, [d['text'] for d in test_data])
    return test_project

@pytest.fixture
def test_profile(db):
    '''
    Creates a test profile with associated auth_user.
    '''
    return create_profile('test_profile', 'password', 'test_profile@rti.org')

@pytest.fixture
def test_profile2(db):
    '''
    Additional profile for tests requiring multiple users.
    '''
    return create_profile('test_profile2', 'password', 'test_profile2@rti.org')

@pytest.fixture
def test_queue(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN)

@pytest.fixture
def test_profile_queue(db, test_profile, test_project_data):
    '''
    A queue with test data, associated with the first test profile.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, profile=test_profile)

@pytest.fixture
def test_profile_queue2(db, test_profile2, test_project_data):
    '''
    A queue with test data, associated with an additional test profile.
    Useful for tests requiring multiple profiles/queues on the same project.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, profile=test_profile2)

@pytest.fixture
def test_tfidf_matrix(test_project_data):
    '''
    A CSR-format tf-idf matrix created from the data of test_project_data
    '''
    return create_tfidf_matrix(test_project_data.data_set.all())

@pytest.fixture
def test_labels(test_project_data):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []

    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project_data))

    return labels

@pytest.fixture
def test_project_labeled(test_project_data, test_labels):
    '''
    A project that has labeled data
    '''
    data = test_project_data.data_set.all()[:10]
    random_labels = [0, 1, 2, 0, 1, 2, 0, 1, 2, 0]
    for i, d in enumerate(data):
        DataLabel.objects.create(data=d,
                                label=test_labels[random_labels[i]],
                                profile=test_project_data.creator,
                                training_set=test_project_data.current_training_set
                                )

    return test_project_data

@pytest.fixture
def test_project_labeled_and_tfidf(test_project_labeled, test_tfidf_matrix, tmpdir):
    data_temp = tmpdir.mkdir('data')
    data_temp.mkdir('tf_idf')

    save_tfidf_matrix(test_tfidf_matrix, test_project_labeled, prefix_dir=str(tmpdir))

    return test_project_labeled

@pytest.fixture
def test_project_with_trained_model(test_project_labeled_and_tfidf, tmpdir):
    '''
    A project which has labeled data, a tfidf matrix saved, and
    a model with pickle file
    '''
    data_temp = tmpdir.listdir()[0]  # tmpdir already has data directory from test_project_labeled_and_tfidf
    data_temp.mkdir('model_pickles')

    trained_model = train_and_save_model(test_project_labeled_and_tfidf, prefix_dir=str(tmpdir))

    return test_project_labeled_and_tfidf

@pytest.fixture
def test_project_predicted_data(test_project_with_trained_model, tmpdir):
    project = test_project_with_trained_model

    predictions = predict_data(project, project.model_set.get(), prefix_dir=str(tmpdir))

    return test_project_with_trained_model