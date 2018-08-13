import pytest
import redis
import os
import pandas as pd

from django.conf import settings
from django.contrib.auth import get_user_model
from smart.celery import app as celery_app
from core.management.commands.seed import (
    seed_database, SEED_USERNAME, SEED_LABELS)
from core.models import (Profile, Label, Model, DataLabel, Data)
from core.util import (create_project, add_queue,
                       create_profile, add_data,
                       create_tfidf_matrix, save_tfidf_matrix,
                       train_and_save_model, predict_data,
                       save_tfidf_vectorizer)

from test.util import read_test_data_backend

TEST_QUEUE_LEN = 30
MAX_DATA_LEN = 2000000

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
    celery_app.conf.update(CELERY_TASK_ALWAYS_EAGER=True,
                           CELERY_TASK_EAGER_PROPAGATES=True)

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
    test_data = read_test_data_backend(file='./core/data/test_files/test_no_labels.csv')
    add_data(test_project, test_data)
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
def test_profile3(db):
    '''
    Additional profile for tests requiring multiple users.
    '''
    return create_profile('test_profile3', 'password', 'test_profile3@rti.org')

@pytest.fixture
def test_queue(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN)

@pytest.fixture
def test_queue_labeled(db, test_project_labeled):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_labeled, TEST_QUEUE_LEN, type="normal")

@pytest.fixture
def test_queue_labeled(db, test_project_labeled):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_labeled, TEST_QUEUE_LEN, type="normal")

@pytest.fixture
def test_admin_queue(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, type="admin")

@pytest.fixture
def test_irr_queue(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_data, MAX_DATA_LEN, type="irr")

@pytest.fixture
def test_irr_queue_labeled(db, test_project_labeled):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_labeled, MAX_DATA_LEN, type="irr")

@pytest.fixture
def test_admin_queue_labeled(db, test_project_labeled):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_labeled, TEST_QUEUE_LEN, type="admin")

@pytest.fixture
def test_admin_queue_labeled(db, test_project_labeled):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    return add_queue(test_project_labeled, TEST_QUEUE_LEN, type="admin")

@pytest.fixture
def test_profile_queue(db, test_profile, test_project_data):
    '''
    A queue with test data, associated with the first test profile.
    '''
    return add_queue(test_project_data, TEST_QUEUE_LEN, profile=test_profile)

@pytest.fixture
def test_all_queues(db, test_project_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    normal_q =  add_queue(test_project_data, TEST_QUEUE_LEN)
    admin_q = add_queue(test_project_data, TEST_QUEUE_LEN, type="admin")
    irr_q = add_queue(test_project_data, MAX_DATA_LEN, type="irr")
    return [normal_q, admin_q, irr_q]

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
    data = Data.objects.filter(project=test_project_data)
    return create_tfidf_matrix(data, test_project_data.pk)[0]

@pytest.fixture
def test_tfidf_matrix_labeled(test_project_labeled):
    '''
    A CSR-format tf-idf matrix created from the data of test_project_data
    '''
    data = Data.objects.filter(project=test_project_labeled)
    return create_tfidf_matrix(data, test_project_labeled.pk)[0]

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
def test_project_labels(test_project):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []

    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project))

    return test_project

@pytest.fixture
def test_project_labeled(test_project):
    '''
    A project that has labeled data
    '''
    for l in SEED_LABELS:
        Label.objects.create(name=l, project=test_project)
    test_data = read_test_data_backend(file='./core/data/test_files/test_some_labels.csv')
    add_data(test_project, test_data)
    return test_project


@pytest.fixture
def test_project_labeled_and_tfidf(test_project_labeled, test_tfidf_matrix_labeled, tmpdir, settings):
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)
    fpath = save_tfidf_matrix(test_tfidf_matrix_labeled, test_project_labeled.pk)
    return test_project_labeled

@pytest.fixture
def test_project_with_trained_model(test_project_labeled_and_tfidf, tmpdir):
    '''
    A project which has labeled data, a tfidf matrix saved, and
    a model with pickle file
    '''
    temp_pickle_path = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(temp_pickle_path)

    trained_model = train_and_save_model(test_project_labeled_and_tfidf)

    return test_project_labeled_and_tfidf

@pytest.fixture
def test_project_predicted_data(test_project_with_trained_model, tmpdir):
    project = test_project_with_trained_model

    predictions = predict_data(project, project.model_set.get())

    return test_project_with_trained_model


'''Fixtures for IRR tests'''
@pytest.fixture
def test_project_no_irr(db, test_profile):
    '''
    This fixture only creates the test project without any data and 0% irr.
    '''
    return create_project('test_project_no_irr', test_profile, 0, 2)

@pytest.fixture
def test_project_no_irr_data(db, test_project_no_irr):
    '''
    Creates the test project with no irr and adds test data to it.
    '''
    test_data = read_test_data_backend(file='./core/data/test_files/test_no_labels.csv')
    add_data(test_project_no_irr, test_data)
    return test_project_no_irr

@pytest.fixture
def test_no_irr_all_queues(db, test_project_no_irr_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    normal_q =  add_queue(test_project_no_irr_data, TEST_QUEUE_LEN)
    admin_q = add_queue(test_project_no_irr_data, TEST_QUEUE_LEN, type="admin")
    irr_q = add_queue(test_project_no_irr_data, MAX_DATA_LEN, type="irr")
    return [normal_q, admin_q, irr_q]

@pytest.fixture
def test_labels_no_irr(test_project_no_irr_data):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []
    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project_no_irr_data))
    return labels

@pytest.fixture
def test_project_all_irr_3_coders(db, test_profile):
    '''
    This fixture only creates the test project without any data.
    '''
    return create_project('test_project', test_profile, 100, 3)

@pytest.fixture
def test_project_all_irr_3_coders_data(db, test_project_all_irr_3_coders):
    '''
    Creates the test project with 100% irr and adds test data to it.
    '''
    test_data = read_test_data_backend(file='./core/data/test_files/test_no_labels.csv')
    add_data(test_project_all_irr_3_coders, test_data)
    return test_project_all_irr_3_coders

@pytest.fixture
def test_all_irr_3_coders_all_queues(db, test_project_all_irr_3_coders_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    normal_q =  add_queue(test_project_all_irr_3_coders_data, TEST_QUEUE_LEN)
    admin_q = add_queue(test_project_all_irr_3_coders_data, TEST_QUEUE_LEN, type="admin")
    irr_q = add_queue(test_project_all_irr_3_coders_data, MAX_DATA_LEN, type="irr")
    return [normal_q, admin_q, irr_q]

@pytest.fixture
def test_labels_all_irr_3_coders(test_project_all_irr_3_coders_data):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []
    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project_all_irr_3_coders_data))
    return labels

@pytest.fixture
def test_project_half_irr(db, test_profile):
    '''
    This fixture only creates the test project without any data.
    '''
    return create_project('test_project', test_profile, 50, 2)

@pytest.fixture
def test_project_half_irr_data(db, test_project_half_irr):
    '''
    Creates the test project with 50% irr and adds test data to it.
    '''
    test_data = read_test_data_backend(file='./core/data/test_files/test_no_labels.csv')
    add_data(test_project_half_irr, test_data)
    return test_project_half_irr

@pytest.fixture
def test_half_irr_all_queues(db, test_project_half_irr):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    normal_q =  add_queue(test_project_half_irr, TEST_QUEUE_LEN)
    admin_q = add_queue(test_project_half_irr, TEST_QUEUE_LEN, type="admin")
    irr_q = add_queue(test_project_half_irr, MAX_DATA_LEN, type="irr")
    return [normal_q, admin_q, irr_q]

@pytest.fixture
def test_labels_half_irr(test_project_half_irr_data):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []

    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project_half_irr_data))

    return labels

@pytest.fixture
def test_project_all_irr_data(db, test_profile):
    '''
    Creates the test project with 100% irr and adds test data to it.
    '''
    project = create_project('test_project', test_profile, 100, 2)
    test_data = read_test_data_backend(file='./core/data/test_files/test_no_labels.csv')
    add_data(project, test_data)
    return project

@pytest.fixture
def test_all_irr_all_queues(db, test_project_all_irr_data):
    '''
    A queue containing data from the test project, with length set to
    the global len.
    '''
    normal_q =  add_queue(test_project_all_irr_data, TEST_QUEUE_LEN)
    admin_q = add_queue(test_project_all_irr_data, TEST_QUEUE_LEN, type="admin")
    irr_q = add_queue(test_project_all_irr_data, MAX_DATA_LEN, type="irr")
    return [normal_q, admin_q, irr_q]

@pytest.fixture
def test_labels_all_irr(test_project_all_irr_data):
    '''
    A list of labels that correspond to SEED_LABELS
    '''
    labels = []
    for l in SEED_LABELS:
        labels.append(Label.objects.create(name=l, project=test_project_all_irr_data))
    return labels

'''Fixtures for the QBC tests'''

@pytest.fixture
def test_project_labeled_and_tfidf_model_qbc_lr(test_profile, tmpdir, settings):
    '''A project with logistic regression and qbc'''
    project = create_project('test_project', test_profile, 0, 2, learning_method = "qbc", classifier = "logistic regression")
    for l in SEED_LABELS:
        Label.objects.create(name=l, project=project)

    test_data = read_test_data_backend(file='./core/data/test_files/test_some_labels.csv')
    add_data(project, test_data)

    matrix = create_tfidf_matrix(test_data, project.pk)[0]
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)
    fpath = save_tfidf_matrix(matrix, project.pk)

    add_queue(project, TEST_QUEUE_LEN)
    add_queue(project, TEST_QUEUE_LEN, type="admin")
    add_queue(project, MAX_DATA_LEN, type="irr")

    temp_pickle_path = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(temp_pickle_path)
    train_and_save_model(project)

    return project

@pytest.fixture
def test_project_labeled_and_tfidf_model_qbc_svm(test_profile, tmpdir, settings):
    '''A project with SVM and qbc'''
    project = create_project('test_project', test_profile, 0, 2, learning_method = "qbc", classifier = "svm")
    for l in SEED_LABELS:
        Label.objects.create(name=l, project=project)

    test_data = read_test_data_backend(file='./core/data/test_files/test_some_labels.csv')
    add_data(project, test_data)

    matrix = create_tfidf_matrix(test_data, project.pk)[0]
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)
    fpath = save_tfidf_matrix(matrix, project.pk)

    add_queue(project, TEST_QUEUE_LEN)
    add_queue(project, TEST_QUEUE_LEN, type="admin")
    add_queue(project, MAX_DATA_LEN, type="irr")

    temp_pickle_path = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(temp_pickle_path)
    train_and_save_model(project)

    return project

@pytest.fixture
def test_project_labeled_and_tfidf_model_qbc_rf(test_profile, tmpdir, settings):
    '''A project with Random Forest and qbc'''
    project = create_project('test_project', test_profile, 0, 2, learning_method = "qbc", classifier = "random forest")
    for l in SEED_LABELS:
        Label.objects.create(name=l, project=project)

    test_data = read_test_data_backend(file='./core/data/test_files/test_some_labels.csv')
    add_data(project, test_data)

    matrix = create_tfidf_matrix(test_data, project.pk)[0]
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)
    fpath = save_tfidf_matrix(matrix, project.pk)

    add_queue(project, TEST_QUEUE_LEN)
    add_queue(project, TEST_QUEUE_LEN, type="admin")
    add_queue(project, MAX_DATA_LEN, type="irr")

    temp_pickle_path = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(temp_pickle_path)
    train_and_save_model(project)

    return project

@pytest.fixture
def test_project_labeled_and_tfidf_model_qbc_gnb(test_profile, tmpdir, settings):
    '''A project with Gaussian Naiive Bayes and qbc'''
    project = create_project('test_project', test_profile, 0, 2, learning_method = "qbc", classifier = "gnb")
    for l in SEED_LABELS:
        Label.objects.create(name=l, project=project)

    test_data = read_test_data_backend(file='./core/data/test_files/test_some_labels.csv')
    add_data(project, test_data)

    matrix = create_tfidf_matrix(test_data, project.pk)[0]
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)
    fpath = save_tfidf_matrix(matrix, project.pk)

    add_queue(project, TEST_QUEUE_LEN)
    add_queue(project, TEST_QUEUE_LEN, type="admin")
    add_queue(project, MAX_DATA_LEN, type="irr")

    temp_pickle_path = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(temp_pickle_path)
    train_and_save_model(project)

    return project
