'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''

from core.models import (Project, Queue, Data, DataQueue)
from core.util import (create_project, add_queue, fill_queue)

from test.util import read_test_data

def assert_obj_exists(model, filter_):
    '''
    See if an instance of the given model matching the given filter
    dict exists.
    '''
    matching_count = model.objects.filter(**filter_).count()
    assert matching_count > 0, "{} matching filter {} " \
        "does not exist. ".format(model.__name__, filter_)


def test_create_project(db):
    project_attrs = { 'name': 'test_project' }
    data = read_test_data()
    project = create_project(project_attrs, data)

    assert_obj_exists(Project, { 'name': 'test_project' })

    test_data = read_test_data()
    for d in test_data:
        assert_obj_exists(Data, d)


def test_add_queue_no_user(db, test_project):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN)
    assert_obj_exists(Queue, {
        'project': test_project, 'length': QUEUE_LEN,
        'user': None
    })

def test_add_queue_user(db, test_project, test_user):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN, user=test_user)
    assert_obj_exists(Queue, {
        'project': test_project, 'length': QUEUE_LEN,
        'user': test_user
    })

def test_fill_empty_queue(db, test_queue):
    fill_queue(test_queue)

    assert test_queue.data.count() == test_queue.length

def test_fill_nonempty_queue(db, test_queue):
    # Manually add one observation so the queue is now nonempty
    test_datum = Data.objects.create(text='test data', project=test_queue.project)
    DataQueue.objects.create(data=test_datum, queue=test_queue)
    assert test_queue.data.count() == 1

    fill_queue(test_queue)
    assert test_queue.data.count() == test_queue.length

def test_fill_queue_all_remaining_data(db, test_queue):
    # Raise the queue length so it's bigger than the amount of data available
    all_data_count = Data.objects.filter(project=test_queue.project).count()
    test_queue.length = all_data_count + 1

    fill_queue(test_queue)
    assert test_queue.data.count() == all_data_count
