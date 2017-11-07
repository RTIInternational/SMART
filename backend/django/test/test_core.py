'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''
import pytest
import unittest
import os
import numpy as np
import scipy
import pandas as pd
import math

from django.contrib.auth import get_user_model

from core.models import (Project, Queue, Data, DataQueue, Profile, Model,
                         AssignedData, Label, DataLabel, DataPrediction,
                         DataUncertainty, TrainingSet, ProjectPermissions)
from core.util import (redis_serialize_queue, redis_serialize_data,
                       redis_parse_queue, redis_parse_data,
                       create_project, add_data, assign_datum,
                       add_queue, fill_queue, pop_queue,
                       init_redis_queues, get_nonempty_queue,
                       create_profile, label_data, pop_first_nonempty_queue,
                       get_assignments, unassign_datum,  save_data_file,
                       save_tfidf_matrix, load_tfidf_matrix,
                       train_and_save_model, predict_data,
                       least_confident, margin_sampling, entropy,
                       check_and_trigger_model, get_ordered_queue_data,
                       find_queue_length)

from test.util import read_test_data, assert_obj_exists, assert_redis_matches_db
from test.conftest import TEST_QUEUE_LEN


def test_redis_serialize_queue(test_queue):
    queue_key = redis_serialize_queue(test_queue)

    assert queue_key == 'queue:' + str(test_queue.pk)


def test_redis_serialize_data(test_project_data):
    datum = test_project_data.data_set.first()
    data_key = redis_serialize_data(datum)

    assert data_key == 'data:' + str(datum.pk)


def test_redis_parse_queue(test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    queue_key = [key for key in test_redis.keys() if 'queue' in key.decode()][0]
    parsed_queue = redis_parse_queue(queue_key)

    assert parsed_queue.pk == test_queue.pk
    assert_obj_exists(DataQueue, { 'queue_id': parsed_queue.pk })
    assert_obj_exists(Queue, { 'pk': parsed_queue.pk })


def test_redis_parse_data(test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    popped_data_key = test_redis.lpop(redis_serialize_queue(test_queue))
    parsed_data = redis_parse_data(popped_data_key)

    assert_obj_exists(Data, { 'pk': parsed_data.pk })
    assert_obj_exists(DataQueue, { 'data_id': parsed_data.pk })


def test_find_queue_length():
    # [batch_size, num_coders, q_length]
    test_vals = [
        [20, 1, 20],
        [20, 2, 30],
        [30, 2, 45],
        [30, 3, 50]
    ]

    for vals in test_vals:
        q_length = find_queue_length(vals[0], vals[1])
        assert q_length == vals[2]


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


def test_get_current_training_set_no_training_set(test_profile):
    project = Project.objects.create(name='test', creator=test_profile)

    training_set = project.get_current_training_set()

    assert training_set == None


def test_get_current_training_set_one_training_set(test_project):
    training_set = test_project.get_current_training_set()
    assertTrainingSet = TrainingSet.objects.filter(project=test_project).order_by('-set_number')[0]

    assert_obj_exists(TrainingSet, { 'project': test_project, 'set_number': 0 })
    assert training_set == assertTrainingSet


def test_get_current_training_set_multiple_training_set(test_project):
    # Test Project already has training set with set number 0, create set number 1,2,3
    set_num_one = TrainingSet.objects.create(project=test_project, set_number=1)
    set_num_two = TrainingSet.objects.create(project=test_project, set_number=2)
    set_num_three = TrainingSet.objects.create(project=test_project, set_number=3)

    assert test_project.get_current_training_set() == set_num_three


def test_add_data_no_labels(db, test_project):
    test_data = read_test_data(file='./core/data/test_files/test_no_labels.csv')

    df =  pd.DataFrame(test_data)
    df['Label'] = df['Label'].apply(lambda x: None if x == '' else x)
    add_data(test_project, df)

    for d in test_data:
        assert_obj_exists(Data, {
            'text': d['Text'],
            'project': test_project
        })


def test_add_data_with_labels(db, test_project_labels):
    test_data = read_test_data(file='./core/data/test_files/test_some_labels.csv')

    df =  pd.DataFrame(test_data)
    df['Label'] = df['Label'].apply(lambda x: None if x == '' else x)
    add_data(test_project_labels, df)

    for d in test_data:
        assert_obj_exists(Data, {
            'text': d['Text'],
            'project': test_project_labels
        })
        if d['Label'] != '':
            assert_obj_exists(DataLabel, {
                'data__text': d['Text'],
                'profile': test_project_labels.creator,
                'label__name': d['Label']
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
    fill_queue(test_queue, orderby='random')

    assert test_queue.data.count() == test_queue.length


def test_fill_nonempty_queue(db, test_queue):
    # Manually add one observation so the queue is now nonempty
    test_datum = Data.objects.create(text='test data', project=test_queue.project, df_idx=0)
    DataQueue.objects.create(data=test_datum, queue=test_queue)
    assert test_queue.data.count() == 1

    fill_queue(test_queue, orderby='random')
    assert test_queue.data.count() == test_queue.length


def test_fill_queue_all_remaining_data(db, test_queue):
    # Raise the queue length so it's bigger than the amount of data available
    all_data_count = Data.objects.filter(project=test_queue.project).count()
    test_queue.length = all_data_count + 1
    test_queue.save()

    fill_queue(test_queue, orderby='random')
    assert test_queue.data.count() == all_data_count


def test_fill_multiple_projects(db, test_queue, test_profile):
    project_data_count = test_queue.project.data_set.count()
    test_queue.length = project_data_count + 1
    test_queue.save()
    test_project2 = create_project('test_project2', test_profile)
    project2_data = read_test_data(file='./core/data/test_files/test_no_labels.csv')
    df =  pd.DataFrame(project2_data)
    df['Label'] = df['Label'].apply(lambda x: None if x == '' else x)

    add_data(test_project2, pd.DataFrame(df))

    fill_queue(test_queue, orderby='random')

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
    fill_queue(queue, orderby='random')

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_queues(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue, orderby='random')

    queue2 = add_queue(test_project_data, 10)

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_init_redis_queues_multiple_projects(db, test_project_data, test_redis, test_profile):
    # Try a mix of multiple queues in multiple projects with
    # and without data to see if everything initializes as expected.
    p1_queue1 = add_queue(test_project_data, 10)
    fill_queue(p1_queue1, orderby='random')
    p1_queue2 = add_queue(test_project_data, 10)

    project2 = create_project('test_project2', test_profile)
    project2_data = read_test_data(file='./core/data/test_files/test_no_labels.csv')
    df =  pd.DataFrame(project2_data)
    df['Label'] = df['Label'].apply(lambda x: None if x == '' else x)

    add_data(project2, pd.DataFrame(df))
    p2_queue1 = add_queue(project2, 10)
    fill_queue(p2_queue1, orderby='random')
    p2_queue2 = add_queue(project2, 10)

    test_redis.flushdb()
    init_redis_queues()

    assert_redis_matches_db(test_redis)


def test_pop_empty_queue(db, test_project, test_redis):
    queue = add_queue(test_project, 10)

    datum = pop_queue(queue)

    assert datum is None
    assert not test_redis.exists('queue:'+str(queue.pk))
    assert queue.data.count() == 0


def test_pop_nonempty_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    fill_queue(queue, orderby='random')

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen('queue:'+str(queue.pk)) == (queue_len - 1)
    assert queue.data.count() == queue_len


def test_pop_only_affects_one_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)
    fill_queue(queue, orderby='random')
    fill_queue(queue2, orderby='random')

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen('queue:'+str(queue.pk)) == (queue_len - 1)
    assert queue.data.count() == queue_len

    assert test_redis.llen('queue:'+str(queue2.pk)) == queue_len
    assert queue2.data.count() == queue_len


def test_get_nonempty_queue_noprofile(db, test_project_data):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)

    assert get_nonempty_queue(test_project_data) is None

    fill_queue(queue2, orderby='random')
    assert get_nonempty_queue(test_project_data) == queue2

    fill_queue(queue, orderby='random')
    assert get_nonempty_queue(test_project_data) == queue


def test_get_nonempty_profile_queue(db, test_project_data, test_profile):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    profile_queue = add_queue(test_project_data, queue_len,
                           profile=test_profile)
    profile_queue2 = add_queue(test_project_data, queue_len,
                            profile=test_profile)

    assert get_nonempty_queue(test_project_data, profile=test_profile) is None

    fill_queue(profile_queue2, orderby='random')
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue2

    fill_queue(profile_queue, orderby='random')
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue


def test_get_nonempty_queue_multiple_profiles(db, test_project_data, test_profile,
                                           test_profile2, test_profile_queue, test_profile_queue2):

    assert get_nonempty_queue(test_project_data) is None

    # Fill the correct one last, so we can test whether the first-filled queue is being
    # selected
    for queue in (test_profile_queue2, test_profile_queue):
        fill_queue(queue, orderby='random')

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
    fill_queue(test_queue, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_profile_queue(db, test_project_data, test_profile,
                                             test_profile_queue, test_redis):
    fill_queue(test_profile_queue, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_multiple_queues(db, test_project_data, test_queue,
                                                  test_redis):
    test_queue2 = add_queue(test_project_data, 10)
    fill_queue(test_queue2, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue2

    fill_queue(test_queue, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue


def test_pop_first_nonempty_queue_multiple_profile_queues(db, test_project_data, test_profile,
                                                       test_profile_queue, test_profile_queue2,
                                                       test_redis):
    fill_queue(test_profile_queue2, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert queue is None
    assert data is None

    fill_queue(test_profile_queue, orderby='random')

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue


def test_assign_datum_project_queue_returns_datum(db, test_queue, test_profile, test_redis):
    '''
    Assign a datum from a project-wide queue (null profile ID).
    '''
    fill_queue(test_queue, orderby='random')

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure we got the datum
    assert isinstance(datum, Data)


def test_assign_datum_project_queue_correct_assignment(db, test_queue, test_profile, test_redis):
    fill_queue(test_queue, orderby='random')

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the assignment is correct
    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_project_queue_pops_queues(db, test_queue, test_profile, test_redis):
    fill_queue(test_queue, orderby='random')

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the datum was removed from queues
    assert test_redis.llen('queue:'+str(test_queue.pk)) == test_queue.length - 1

    # but not from the db queue
    assert test_queue.data.count() == test_queue.length
    assert datum in test_queue.data.all()


def test_assign_datum_profile_queue_returns_correct_datum(db, test_profile_queue, test_profile,
                                                       test_profile_queue2, test_profile2,
                                                       test_redis):
    fill_queue(test_profile_queue, orderby='random')
    fill_queue(test_profile_queue2, orderby='random')

    datum = assign_datum(test_profile, test_profile_queue.project)

    assert isinstance(datum, Data)


def test_assign_datum_profile_queue_correct_assignment(db, test_profile_queue, test_profile,
                                                    test_profile_queue2, test_profile2,
                                                    test_redis):
    fill_queue(test_profile_queue, orderby='random')
    fill_queue(test_profile_queue2, orderby='random')

    datum = assign_datum(test_profile, test_profile_queue.project)

    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_profile_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_profile_queue_pops_queues(db, test_profile_queue, test_profile,
                                             test_profile_queue2, test_profile2, test_redis):
    fill_queue(test_profile_queue, orderby='random')
    fill_queue(test_profile_queue2, orderby='random')

    datum = assign_datum(test_profile, test_profile_queue.project)

    # Make sure the datum was removed from the correct queues
    assert test_redis.llen('queue:'+str(test_profile_queue.pk)) == test_profile_queue.length - 1

    # ...but not the other queues
    assert test_profile_queue.data.count() == test_profile_queue.length
    assert datum in test_profile_queue.data.all()
    assert test_redis.llen('queue:'+str(test_profile_queue2.pk)) == test_profile_queue2.length
    assert test_profile_queue2.data.count() == test_profile_queue2.length


def test_init_redis_queues_ignores_assigned_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    assigned_datum = test_queue.data.first()

    AssignedData.objects.create(
        profile=test_profile,
        data=assigned_datum,
        queue=test_queue)

    init_redis_queues()

    # Make sure the assigned datum didn't get into the redis queue
    assert test_redis.llen('queue:'+str(test_queue.pk)) == test_queue.length - 1


def test_label_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    datum = assign_datum(test_profile, test_queue.project)
    test_label = Label.objects.create(name='test', project=test_queue.project)
    label_data(test_label, datum, test_profile, 3)

    # Make sure the label was properly recorded
    assert datum in test_profile.labeled_data.all()
    assert_obj_exists(DataLabel, {
        'data': datum,
        'profile': test_profile,
        'label': test_label,
        'time_to_label': 3
    })

    # Make sure the assignment was removed
    assert not AssignedData.objects.filter(profile=test_profile,
                                           data=datum,
                                           queue=test_queue).exists()


def test_get_assignments_no_existing_assignment_one_assignment(db, test_profile, test_project_data, test_queue,
                                               test_redis):
    fill_queue(test_queue, orderby='random')

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, 1)

    assert len(data) == 1
    assert isinstance(data[0], Data)
    assert_obj_exists(AssignedData, {
        'data': data[0],
        'profile': test_profile
    })


def test_get_assignments_no_existing_assignment_half_max_queue_length(db, test_profile, test_project_data, test_queue,
                                               test_redis):
    fill_queue(test_queue, orderby='random')

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN // 2)

    assert len(data) == TEST_QUEUE_LEN // 2
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {
            'data': datum,
            'profile': test_profile
        })


def test_get_assignments_no_existing_assignment_max_queue_length(db, test_profile, test_project_data, test_queue,
                                               test_redis):
    fill_queue(test_queue, orderby='random')

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN)

    assert len(data) == TEST_QUEUE_LEN
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {
            'data': datum,
            'profile': test_profile
        })


def test_get_assignments_no_existing_assignment_over_max_queue_length(db, test_profile, test_project_data, test_queue,
                                               test_redis):
    fill_queue(test_queue, orderby='random')

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN + 10)

    assert len(data) == TEST_QUEUE_LEN
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {
            'data': datum,
            'profile': test_profile
        })


def test_get_assignments_one_existing_assignment(db, test_profile, test_project_data, test_queue,
                                            test_redis):
    fill_queue(test_queue, orderby='random')

    assigned_datum = assign_datum(test_profile, test_project_data)

    data = get_assignments(test_profile, test_project_data, 1)

    assert isinstance(data[0], Data)
    # We should just get the datum that was already assigned
    assert data[0] == assigned_datum


def test_get_assignments_multiple_existing_assignments(db, test_profile, test_project_data, test_queue,
                                            test_redis):
    fill_queue(test_queue, orderby='random')

    assigned_data = []
    for i in range(5):
        assigned_data.append(assign_datum(test_profile, test_project_data))

    data = get_assignments(test_profile, test_project_data, 5)

    case = unittest.TestCase()
    assert len(data) == 5
    assert len(data) == len(assigned_data)
    for datum, assigned_datum in zip(data, assigned_data):
        assert isinstance(datum, Data)
    # We should just get the data that was already assigned
    case.assertCountEqual(data, assigned_data)


def test_unassign(db, test_profile, test_project_data, test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    assert test_redis.llen('queue:'+str(test_queue.pk)) == test_queue.length

    datum = get_assignments(test_profile, test_project_data, 1)[0]

    assert test_redis.llen('queue:'+str(test_queue.pk)) == (test_queue.length - 1)
    assert AssignedData.objects.filter(
        data=datum,
        profile=test_profile).exists()

    unassign_datum(datum, test_profile)

    assert test_redis.llen('queue:'+str(test_queue.pk)) == test_queue.length
    assert not AssignedData.objects.filter(
        data=datum,
        profile=test_profile).exists()

    # The unassigned datum should be the next to be assigned
    reassigned_datum = get_assignments(test_profile, test_project_data, 1)[0]

    assert reassigned_datum == datum


def test_save_data_file_no_labels_csv(test_project, tmpdir, settings):
    test_file = './core/data/test_files/test_no_labels.csv'

    temp_data_file_path = tmpdir.mkdir('data').mkdir('data_files')
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)

    fname = save_data_file(data, test_project.pk)

    saved_data = pd.read_csv(fname)

    assert fname == os.path.join(str(temp_data_file_path), 'project_' + str(test_project.pk) + '_data_0.csv')
    assert os.path.isfile(fname)
    assert saved_data.equals(data)


def test_save_data_file_some_labels_csv(test_project, tmpdir, settings):
    test_file = './core/data/test_files/test_some_labels.csv'

    temp_data_file_path = tmpdir.mkdir('data').mkdir('data_files')
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)

    fname = save_data_file(data, test_project.pk)

    saved_data = pd.read_csv(fname)

    assert fname == os.path.join(str(temp_data_file_path), 'project_' + str(test_project.pk) + '_data_0.csv')
    assert os.path.isfile(fname)
    assert saved_data.equals(data)


def test_save_data_file_multiple_files(test_project, tmpdir, settings):
    test_file = './core/data/test_files/test_no_labels.csv'

    temp_data_file_path = tmpdir.mkdir('data').mkdir('data_files')
    settings.PROJECT_FILE_PATH = str(temp_data_file_path)

    data = pd.read_csv(test_file)

    fname1 = save_data_file(data, test_project.pk)
    fname2 = save_data_file(data, test_project.pk)
    fname3 = save_data_file(data, test_project.pk)

    assert fname1 == os.path.join(str(temp_data_file_path), 'project_' + str(test_project.pk) + '_data_0.csv')
    assert os.path.isfile(fname1)
    assert fname2 == os.path.join(str(temp_data_file_path), 'project_' + str(test_project.pk) + '_data_1.csv')
    assert os.path.isfile(fname2)
    assert fname3 == os.path.join(str(temp_data_file_path), 'project_' + str(test_project.pk) + '_data_2.csv')
    assert os.path.isfile(fname3)


def test_create_tfidf_matrix(test_tfidf_matrix):
    assert type(test_tfidf_matrix) == scipy.sparse.csr.csr_matrix
    assert test_tfidf_matrix.shape == (285, 11)
    assert test_tfidf_matrix.dtype == np.float64


def test_save_tfidf_matrix(test_project_data, test_tfidf_matrix, tmpdir, settings):
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)

    file = save_tfidf_matrix(test_tfidf_matrix, test_project_data.pk)

    assert os.path.isfile(file)
    assert file == os.path.join(settings.TF_IDF_PATH, str(test_project_data.pk) + '.npz')


def test_load_tfidf_matrix(test_project_labeled_and_tfidf, test_tfidf_matrix, tmpdir, settings):
    matrix = load_tfidf_matrix(test_project_labeled_and_tfidf.pk)

    assert np.allclose(matrix.A, test_tfidf_matrix.A)


def test_least_confident_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        ls = least_confident(probs)

    assert 'Probs should be a numpy array' in str(excinfo.value)


def test_least_confident_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.4)


def test_least_confident_binary():
    probs = np.array([0.2, 0.8])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.2)


def test_least_confident_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    lc = least_confident(probs)

    np.testing.assert_almost_equal(lc, 0.3)


def test_margin_sampling_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        ms = margin_sampling(probs)

    assert 'Probs should be a numpy array' in str(excinfo.value)


def test_margin_sampling_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.3)


def test_margin_sampling_binary():
    probs = np.array([0.2, 0.8])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.6)


def test_margin_sampling_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    ms = margin_sampling(probs)

    np.testing.assert_almost_equal(ms, 0.6)


def test_entropy_notarray():
    probs = [0.5, 0.5]

    with pytest.raises(ValueError) as excinfo:
        e = entropy(probs)

    assert 'Probs should be a numpy array' in str(excinfo.value)


def test_entropy_threeclass():
    probs = np.array([0.1, 0.3, 0.6])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.3899728733539152)


def test_entropy_binary():
    probs = np.array([0.2, 0.8])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.21732201127364886)


def test_entropy_fourclass():
    probs = np.array([0.1, 0.1, 0.1, 0.7])

    e = entropy(probs)

    np.testing.assert_almost_equal(e, 0.4084313719900203)


def test_train_and_save_model(test_project_labeled_and_tfidf, tmpdir, settings):
    project = test_project_labeled_and_tfidf

    model_path_temp = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    model = train_and_save_model(project)

    assert isinstance(model, Model)
    assert_obj_exists(Model, {
        'pickle_path': model.pickle_path,
        'project': project
    })
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(str(model_path_temp), 'project_' + str(project.pk)
                                             + '_training_' + str(project.get_current_training_set().set_number)
                                             + '.pkl')


def test_predict_data(test_project_with_trained_model, tmpdir):
    project = test_project_with_trained_model

    predictions = predict_data(project, project.model_set.get())

    # Number of unlabeled data * number of labels.  Each data gets a prediction for each label.
    expected_predction_count = project.data_set.filter(datalabel__isnull=True).count() * project.labels.count()
    assert len(predictions) ==  expected_predction_count

    for prediction in predictions:
        assert isinstance(prediction, DataPrediction)
        assert_obj_exists(DataPrediction, {
            'data': prediction.data,
            'model': prediction.model,
            'label': prediction.label,
            'predicted_probability': prediction.predicted_probability
        })


def test_fill_queue_random_predicted_data(test_project_predicted_data, test_queue, test_redis):
    fill_queue(test_queue, 'random')

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length
    for datum in test_queue.data.all():
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })


def test_fill_queue_least_confident_predicted_data(test_project_predicted_data, test_queue, test_redis):
    fill_queue(test_queue, 'least confident')

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length

    data_list = get_ordered_queue_data(test_queue, 'least confident')
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident


def test_fill_queue_margin_sampling_predicted_data(test_project_predicted_data, test_queue, test_redis):
    fill_queue(test_queue, 'margin sampling')

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length
    data_list = get_ordered_queue_data(test_queue, 'margin sampling')
    previous_ms = data_list[0].datauncertainty_set.get().margin_sampling
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().margin_sampling >= previous_ms
        previous_ms = datum.datauncertainty_set.get().margin_sampling


def test_fill_queue_entropy_predicted_data(test_project_predicted_data, test_queue, test_redis):
    fill_queue(test_queue, 'entropy')

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length
    data_list = get_ordered_queue_data(test_queue, 'entropy')
    previous_e = data_list[0].datauncertainty_set.get().entropy
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().entropy <= previous_e
        previous_e = datum.datauncertainty_set.get().entropy


def test_check_and_trigger_model_first_labeled(setup_celery, test_project_data, test_labels, test_queue, test_profile):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby='random')

    datum = assign_datum(test_profile, test_queue.project)
    test_label = test_labels[0]
    label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == 'no trigger'

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN - 1


def test_check_and_trigger_lt_batch_labeled(setup_celery, test_project_data, test_labels, test_queue, test_profile):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby='random')

    for i in range(TEST_QUEUE_LEN // 2):
        datum = assign_datum(test_profile, test_queue.project)
        test_label = test_labels[0]
        label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == 'no trigger'

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN - (TEST_QUEUE_LEN // 2)


def test_check_and_trigger_batched_success(setup_celery, test_project_labeled_and_tfidf,
                                           test_queue, test_redis, tmpdir, settings):
    project = test_project_labeled_and_tfidf
    initial_training_set = project.get_current_training_set()
    initial_queue_size = test_queue.length
    model_path_temp = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    datum = DataLabel.objects.filter(data__project=project).first().data
    check = check_and_trigger_model(datum)
    assert check == 'model running'

    # Assert model created and saved
    assert_obj_exists(Model, {
        'project': project
    })
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(str(model_path_temp), 'project_' + str(project.pk)
                                             + '_training_' + str(initial_training_set.set_number)
                                             + '.pkl')

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert len(predictions) == Data.objects.filter(project=project,
                                                   labelers=None).count() * project.labels.count()

    # Assert queue filled and redis sycned
    assert test_queue.data.count() == test_queue.length
    assert_redis_matches_db(test_redis)
    assert test_queue.length == initial_queue_size

    # Assert least confident in queue
    data_list = get_ordered_queue_data(test_queue, 'least confident')
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert project.get_current_training_set().set_number == initial_training_set.set_number + 1


def test_check_and_trigger_batched_onlyone_label(setup_celery, test_project_data, test_labels, test_queue, test_profile):
    initial_training_set = test_project_data.get_current_training_set()

    fill_queue(test_queue, orderby='random')

    for i in range(TEST_QUEUE_LEN):
        datum = assign_datum(test_profile, test_queue.project)
        test_label = test_labels[0]
        label_data(test_label, datum, test_profile, 3)

    check = check_and_trigger_model(datum)
    assert check == 'random'

    assert test_project_data.get_current_training_set() == initial_training_set
    assert test_project_data.model_set.count() == 0
    assert DataPrediction.objects.filter(data__project=test_project_data).count() == 0
    assert DataUncertainty.objects.filter(data__project=test_project_data).count() == 0
    assert DataQueue.objects.filter(queue=test_queue).count() == TEST_QUEUE_LEN


def test_check_and_trigger_queue_changes_success(setup_celery, test_project_labeled_and_tfidf,
                                           test_queue, test_redis, tmpdir, settings, test_profile2):
    project = test_project_labeled_and_tfidf
    initial_training_set = project.get_current_training_set()
    initial_queue_size = test_queue.length
    model_path_temp = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    # Add another user to permissions
    ProjectPermissions.objects.create(profile=test_profile2,
                                      project=project,
                                      permission='CODER')

    datum = DataLabel.objects.filter(data__project=project).first().data
    check = check_and_trigger_model(datum)
    assert check == 'model running'

    # Assert model created and saved
    assert_obj_exists(Model, {
        'project': project
    })
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(str(model_path_temp), 'project_' + str(project.pk)
                                             + '_training_' + str(initial_training_set.set_number)
                                             + '.pkl')

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert len(predictions) == Data.objects.filter(project=project,
                                                   labelers=None).count() * project.labels.count()

    # Assert queue filled and redis sycned
    q = project.queue_set.get()
    assert q.data.count() == q.length
    assert_redis_matches_db(test_redis)

    batch_size = len(project.labels.all()) * 10
    num_coders = len(project.projectpermissions_set.all()) + 1
    new_queue_length = find_queue_length(batch_size, num_coders)
    assert q.length == new_queue_length

    # Assert least confident in queue
    data_list = get_ordered_queue_data(test_queue, 'least confident')
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident
    assert DataQueue.objects.filter(queue=test_queue).count() == new_queue_length

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert project.get_current_training_set().set_number == initial_training_set.set_number + 1
