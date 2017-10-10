'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''
import pytest

from django.contrib.auth import get_user_model

from core.models import (Project, Queue, Data, DataQueue, Profile,
                         AssignedData, Label, DataLabel)
from core.util import (create_project, add_data, assign_datum,
                       add_queue, fill_queue, pop_queue,
                       init_redis_queues, get_nonempty_queue,
                       create_profile, label_data, pop_first_nonempty_queue,
                       get_assignment, unassign_datum)

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
            assert test_redis.exists('queue:'+str(q.pk))
            assert test_redis.llen('queue:'+str(q.pk)) == data_count
        else:
            # Empty lists don't exist in redis
            assert not test_redis.exists(q.pk)


def test_create_profile(db):
    username = 'test_user'
    password = 'password'
    email = 'test_user@rti.org'

    create_profile(username, password, email)

    auth_user_attrs = {
        'username': username,
        'password': password,
        'email': email
    }

    assert_obj_exists(get_user_model(), auth_user_attrs)

    auth_user = (get_user_model().objects
                 .filter(**auth_user_attrs)
                 .first())

    assert_obj_exists(Profile, { 'user': auth_user })


def test_create_project(db, test_profile):
    name = 'test_project'
    project = create_project(name, test_profile)

    assert_obj_exists(Project, { 'name': name })


def test_add_data(db, test_project):
    test_data = read_test_data()

    add_data(test_project, [d['text'] for d in test_data])

    for d in test_data:
        assert_obj_exists(Data, {
            'text': d['text'],
            'project': test_project
        })


def test_add_queue_no_profile(test_project):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN)
    assert_obj_exists(Queue, {
        'project': test_project, 'length': QUEUE_LEN,
        'profile': None
    })


def test_add_queue_profile(test_project, test_profile):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN, profile=test_profile)
    assert_obj_exists(Queue, {
        'project': test_project, 'length': QUEUE_LEN,
        'profile': test_profile
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
    test_queue.save()

    fill_queue(test_queue)
    assert test_queue.data.count() == all_data_count


def test_fill_multiple_projects(db, test_queue, test_profile):
    project_data_count = test_queue.project.data_set.count()
    test_queue.length = project_data_count + 1
    test_queue.save()
    test_project2 = create_project('test_project2', test_profile)
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

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_one_nonempty_queue(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue)

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_queues(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue)

    queue2 = add_queue(test_project_data, 10)

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_projects(db, test_project_data, test_redis, test_profile):
    # Try a mix of multiple queues in multiple projects with
    # and without data to see if everything initializes as expected.
    p1_queue1 = add_queue(test_project_data, 10)
    fill_queue(p1_queue1)
    p1_queue2 = add_queue(test_project_data, 10)

    project2 = create_project('test_project2', test_profile)
    project2_data = read_test_data()
    add_data(project2, [d['text'] for d in project2_data])
    p2_queue1 = add_queue(project2, 10)
    fill_queue(p2_queue1)
    p2_queue2 = add_queue(project2, 10)

    test_redis.flushdb()
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
    assert queue.data.count() == queue_len


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
    assert queue.data.count() == queue_len

    assert test_redis.llen(queue2.pk) == queue_len
    assert queue2.data.count() == queue_len


def test_get_nonempty_queue_noprofile(db, test_project_data):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)

    assert get_nonempty_queue(test_project_data) is None

    fill_queue(queue2)
    assert get_nonempty_queue(test_project_data) == queue2

    fill_queue(queue)
    assert get_nonempty_queue(test_project_data) == queue


def test_get_nonempty_profile_queue(db, test_project_data, test_profile):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    profile_queue = add_queue(test_project_data, queue_len,
                           profile=test_profile)
    profile_queue2 = add_queue(test_project_data, queue_len,
                            profile=test_profile)

    assert get_nonempty_queue(test_project_data, profile=test_profile) is None

    fill_queue(profile_queue2)
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue2

    fill_queue(profile_queue)
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue


def test_get_nonempty_queue_multiple_profiles(db, test_project_data, test_profile,
                                           test_profile2, test_profile_queue, test_profile_queue2):

    assert get_nonempty_queue(test_project_data) is None

    # Fill the correct one last, so we can test whether the first-filled queue is being
    # selected
    for queue in (test_profile_queue2, test_profile_queue):
        fill_queue(queue)

    assert get_nonempty_queue(test_project_data, profile=test_profile) == test_profile_queue


def test_pop_first_nonempty_queue_noqueue(db, test_project_data, test_redis):
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert queue is None
    assert data is None


def test_pop_first_nonempty_queue_empty(db, test_project_data, test_queue, test_redis):
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert queue is None
    assert data is None


def test_pop_first_nonempty_queue_single_queue(db, test_project_data, test_queue, test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_profile_queue(db, test_project_data, test_profile,
                                             test_profile_queue, test_redis):
    fill_queue(test_profile_queue)
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_multiple_queues(db, test_project_data, test_queue,
                                                  test_redis):
    test_queue2 = add_queue(test_project_data, 10)
    fill_queue(test_queue2)
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue2

    fill_queue(test_queue)
    # sync_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue


def test_pop_first_nonempty_queue_multiple_profile_queues(db, test_project_data, test_profile,
                                                       test_profile_queue, test_profile_queue2,
                                                       test_redis):
    fill_queue(test_profile_queue2)
    init_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert queue is None
    assert data is None

    fill_queue(test_profile_queue)
    # sync_redis_queues()

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue


def test_assign_datum_project_queue_returns_datum(db, test_queue, test_profile, test_redis):
    '''
    Assign a datum from a project-wide queue (null profile ID).
    '''
    fill_queue(test_queue)
    init_redis_queues()

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure we got the datum
    assert isinstance(datum, Data)


def test_assign_datum_project_queue_correct_assignment(db, test_queue, test_profile, test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the assignment is correct
    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_project_queue_pops_queues(db, test_queue, test_profile, test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the datum was removed from queues
    assert test_redis.llen(test_queue.pk) == test_queue.length - 1

    # but not from the db queue
    assert test_queue.data.count() == test_queue.length
    assert datum in test_queue.data.all()


def test_assign_datum_profile_queue_returns_correct_datum(db, test_profile_queue, test_profile,
                                                       test_profile_queue2, test_profile2,
                                                       test_redis):
    fill_queue(test_profile_queue)
    fill_queue(test_profile_queue2)
    init_redis_queues()

    datum = assign_datum(test_profile, test_profile_queue.project)

    assert isinstance(datum, Data)


def test_assign_datum_profile_queue_correct_assignment(db, test_profile_queue, test_profile,
                                                    test_profile_queue2, test_profile2,
                                                    test_redis):
    fill_queue(test_profile_queue)
    fill_queue(test_profile_queue2)
    init_redis_queues()

    datum = assign_datum(test_profile, test_profile_queue.project)

    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_profile_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_profile_queue_pops_queues(db, test_profile_queue, test_profile,
                                             test_profile_queue2, test_profile2, test_redis):
    fill_queue(test_profile_queue)
    fill_queue(test_profile_queue2)
    init_redis_queues()

    datum = assign_datum(test_profile, test_profile_queue.project)

    # Make sure the datum was removed from the correct queues
    assert test_redis.llen(test_profile_queue.pk) == test_profile_queue.length - 1

    # ...but not the other queues
    assert test_profile_queue.data.count() == test_profile_queue.length
    assert datum in test_profile_queue.data.all()
    assert test_redis.llen(test_profile_queue2.pk) == test_profile_queue2.length
    assert test_profile_queue2.data.count() == test_profile_queue2.length


def test_init_redis_queues_ignores_assigned_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue)

    assigned_datum = test_queue.data.first()

    AssignedData.objects.create(
        profile=test_profile,
        data=assigned_datum,
        queue=test_queue)

    init_redis_queues()

    # Make sure the assigned datum didn't get into the redis queue
    assert test_redis.llen(test_queue.pk) == test_queue.length - 1


def test_label_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    datum = assign_datum(test_profile, test_queue.project)
    test_label = Label.objects.create(name='test', project=test_queue.project)
    label_data(test_label, datum, test_profile)

    # Make sure the label was properly recorded
    assert datum in test_profile.labeled_data.all()
    assert_obj_exists(DataLabel, {
        'data': datum,
        'profile': test_profile,
        'label': test_label
    })

    # Make sure the assignment was removed
    assert not AssignedData.objects.filter(profile=test_profile,
                                           data=datum,
                                           queue=test_queue).exists()


def test_get_assignment_no_existing_assignment(db, test_profile, test_project_data, test_queue,
                                               test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    assert AssignedData.objects.count() == 0

    datum = get_assignment(test_profile, test_project_data)

    assert isinstance(datum, Data)
    assert_obj_exists(AssignedData, {
        'data': datum,
        'profile': test_profile
    })


def test_get_assignment_existing_assignment(db, test_profile, test_project_data, test_queue,
                                            test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    assigned_datum = assign_datum(test_profile, test_project_data)

    datum = get_assignment(test_profile, test_project_data)

    assert isinstance(datum, Data)
    # We should just get the datum that was already assigned
    assert datum == assigned_datum


def test_unassign(db, test_profile, test_project_data, test_queue, test_redis):
    fill_queue(test_queue)
    init_redis_queues()

    assert test_redis.llen(test_queue.pk) == test_queue.length

    datum = get_assignment(test_profile, test_project_data)

    assert test_redis.llen(test_queue.pk) == (test_queue.length - 1)
    assert AssignedData.objects.filter(
        data=datum,
        profile=test_profile).exists()

    unassign_datum(datum, test_profile)

    assert test_redis.llen(test_queue.pk) == test_queue.length
    assert not AssignedData.objects.filter(
        data=datum,
        profile=test_profile).exists()

    # The unassigned datum should be the next to be assigned
    reassigned_datum = get_assignment(test_profile, test_project_data)

    assert reassigned_datum == datum
