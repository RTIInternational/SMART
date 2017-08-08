'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''

from core.models import (Project, Queue, Data)
from core.util import (add_queue)

from test.util import read_test_data

def assert_obj_exists(model, filter_):
    '''
    See if an instance of the given model matching the given filter
    dict exists.
    '''
    matching_count = model.objects.filter(**filter_).count()
    assert matching_count > 0, "{} matching filter {} " \
        "does not exist. ".format(model.__name__, filter_)


def test_create_project(db, test_project):
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

