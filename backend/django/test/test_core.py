'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''
from core.models import (Project, Queue, Data, DataQueue)
from core.util import (create_project, add_data,
                       add_queue, fill_queue,
                       init_redis_queues)

from test.util import read_test_data

def assert_obj_exists(model, filter_):
    '''
    See if an instance of the given model matching the given filter
    dict exists.
    '''
    matching_count = model.objects.filter(**filter_).count()
    assert matching_count > 0, "{} matching filter {} " \
        "does not exist. ".format(model.__name__, filter_)

def assert_redis_matches_db(test_redis):
    '''
    Make sure all nonempty queues are present in the redis DB and
    have the correct amount of data, as determined by the DB.
    '''
    for q in Queue.objects.all():
        data_count = q.data.count()

        if data_count > 0:
            assert test_redis.exists(q.pk)
            assert test_redis.llen(q.pk) == data_count
        else:
            # Empty lists don't exist in redis
            assert not test_redis.exists(q.pk)


def test_create_project(db):
    project_attrs = { 'name': 'test_project' }
    project = create_project(project_attrs)

    assert_obj_exists(Project, { 'name': 'test_project' })


def test_add_data(db, test_project):
    test_data = read_test_data()

    add_data(test_project, test_data)

    for d in test_data:
        assert_obj_exists(Data, d)


def test_add_queue_no_user(test_project):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN)
    assert_obj_exists(Queue, {
        'project': test_project, 'length': QUEUE_LEN,
        'user': None
    })


def test_add_queue_user(test_project, test_user):
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


def test_init_redis_queues_empty(db, test_redis):
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_one_empty_queue(db, test_project, test_redis):
    queue = add_queue(test_project, 10)
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_one_nonempty_queue(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue)
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_queues(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    queue2 = add_queue(test_project_data, 10)
    init_redis_queues()

    assert_redis_matches_db(test_redis)
