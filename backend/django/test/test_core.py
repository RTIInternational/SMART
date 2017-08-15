'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''
from django.contrib.auth import get_user_model

from core.models import (Project, Queue, Data, DataQueue, User)
from core.util import (create_project, add_data, assign_datum,
                       add_queue, fill_queue, pop_queue,
                       init_redis_queues, get_nonempty_queue,
                       create_user)

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


def test_create_user(db):
    username = 'test_user'
    password = 'password'
    email = 'test_user@rti.org'

    create_user(username, password, email)

    auth_user_attrs = {
        'username': username,
        'password': password,
        'email': email
    }

    assert_obj_exists(get_user_model(), auth_user_attrs)

    auth_user = (get_user_model().objects
                 .filter(**auth_user_attrs)
                 .first())

    assert_obj_exists(User, { 'auth_user': auth_user })


def test_create_project(db):
    name = 'test_project'
    project = create_project(name)

    assert_obj_exists(Project, { 'name': name })


def test_add_data(db, test_project):
    test_data = read_test_data()

    add_data(test_project, [d['text'] for d in test_data])

    for d in test_data:
        assert_obj_exists(Data, {
            'text': d['text'],
            'project': test_project
        })


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


def test_fill_multiple_queues(db, test_queue):
    # Set both queues to be as large as the amount of available data
    # so we can be sure they won't overlap each other when filled
    data_count = Data.objects.count()
    test_queue.length = data_count
    test_queue2 = add_queue(test_queue.project, data_count)

    fill_queue(test_queue)
    fill_queue(test_queue2)

    assert test_queue.data.count() == data_count
    assert test_queue2.data.count() == 0


def test_fill_multiple_projects(db, test_queue):
    project_data_count = test_queue.project.data_set.count()
    test_queue.length = project_data_count + 1
    test_project2 = create_project('test_project2')
    project2_data = read_test_data()

    add_data(test_project2, [d['text'] for d in project2_data])

    fill_queue(test_queue)

    # Ensure the queue didn't fill any data from the other project
    assert test_queue.data.count() == project_data_count
    assert all((d.project == test_queue.project
                for d in test_queue.data.all()))


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
    fill_queue(queue)

    queue2 = add_queue(test_project_data, 10)
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_projects(db, test_project_data, test_redis):
    # Try a mix of multiple queues in multiple projects with
    # and without data to see if everything initializes as expected.
    p1_queue1 = add_queue(test_project_data, 10)
    fill_queue(p1_queue1)
    p1_queue2 = add_queue(test_project_data, 10)

    project2 = create_project('test_project2')
    project2_data = read_test_data()
    add_data(project2, [d['text'] for d in project2_data])
    p2_queue1 = add_queue(project2, 10)
    fill_queue(p2_queue1)
    p2_queue2 = add_queue(project2, 10)

    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_pop_empty_queue(db, test_project, test_redis):
    queue = add_queue(test_project, 10)
    init_redis_queues()

    datum = pop_queue(queue)

    assert datum is None
    assert not test_redis.exists(queue.pk)
    assert queue.data.count() == 0


def test_pop_nonempty_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    fill_queue(queue)
    init_redis_queues()

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen(queue.pk) == (queue_len - 1)
    assert queue.data.count() == (queue_len - 1)


def test_pop_only_affects_one_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)
    fill_queue(queue)
    fill_queue(queue2)
    init_redis_queues()

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen(queue.pk) == (queue_len - 1)
    assert queue.data.count() == (queue_len - 1)

    assert test_redis.llen(queue2.pk) == queue_len
    assert queue2.data.count() == queue_len


def test_get_nonempty_queue_nouser(db, test_project_data):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)

    assert get_nonempty_queue(test_project_data) is None

    fill_queue(queue2)
    assert get_nonempty_queue(test_project_data) == queue2

    fill_queue(queue)
    assert get_nonempty_queue(test_project_data) == queue


def test_get_nonempty_queue_user(db, test_project_data, test_user):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue_user = add_queue(test_project_data, queue_len,
                           user=test_user)
    queue_user2 = add_queue(test_project_data, queue_len,
                            user=test_user)

    assert get_nonempty_queue(test_project_data, user=test_user) is None

    fill_queue(queue_user2)
    assert get_nonempty_queue(test_project_data, user=test_user) == queue_user2

    fill_queue(queue_user)
    assert get_nonempty_queue(test_project_data, user=test_user) == queue_user


def test_get_nonempty_queue_multiple_users(db, test_project_data, test_user):
    queue_len = 10
    test_user2 = create_user('test_user2', 'password', 'test_user2@rti.org')
    test_user3 = create_user('test_user3', 'password', 'test_user3@rti.org')

    # Put the queue of interest in the middle in hopes of
    # catching any incorrect code taking the first or last
    # available queue
    queue_user2 = add_queue(test_project_data,
                            queue_len, user=test_user2)
    queue_user = add_queue(test_project_data,
                           queue_len, user=test_user)
    queue_user3 = add_queue(test_project_data,
                            queue_len, user=test_user3)

    for queue in (queue_user2, queue_user, queue_user3):
        fill_queue(queue)

    assert get_nonempty_queue(test_project_data) is None

    assert get_nonempty_queue(test_project_data, user=test_user) == queue_user

