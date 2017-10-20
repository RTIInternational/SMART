'''
Test core logic for the SMART app, such as creating projects, managing
queues, etc.
'''
import pytest
import unittest
import os
import numpy as np
import scipy

from django.contrib.auth import get_user_model

from core.models import (Project, Queue, Data, DataQueue, Profile, Model,
                         AssignedData, Label, DataLabel, DataPrediction,
                         DataUncertainty)
from core.util import (redis_serialize_queue, redis_serialize_data,
                       redis_parse_queue, redis_parse_data,
                       create_project, add_data, assign_datum,
                       add_queue, fill_queue, pop_queue,
                       init_redis_queues, get_nonempty_queue,
                       create_profile, label_data, pop_first_nonempty_queue,
                       get_assignments, unassign_datum,
                       save_tfidf_matrix, load_tfidf_matrix,
                       train_and_save_model, predict_data,
                       least_confident, margin_sampling, entropy)

from test.util import read_test_data, assert_obj_exists, assert_redis_matches_db


def test_redis_serialize_queue(test_queue):
    queue_key = redis_serialize_queue(test_queue)

    assert queue_key == 'queue:' + str(test_queue.pk)


def test_redis_serialize_data(test_project_data):
    datum = test_project_data.data_set.first()
    data_key = redis_serialize_data(datum)

    assert data_key == 'data:' + str(datum.pk)


def test_redis_parse_queue(test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    last_data_in_queue = [d for d in test_queue.data.all()][-1]

    queue_key = [key for key in test_redis.keys() if 'queue' in key.decode()][0]
    parsed_queue = redis_parse_queue(queue_key)

    assert parsed_queue.pk == test_queue.pk


def test_redis_parse_data(test_queue, test_redis):
    fill_queue(test_queue, orderby='random')

    last_data_in_queue = [d for d in test_queue.data.all()][-1]
    popped_data_key = test_redis.lpop(redis_serialize_queue(test_queue))
    parsed_data = redis_parse_data(popped_data_key)

    assert parsed_data.pk == last_data_in_queue.pk


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
    fill_queue(test_queue, orderby='random')

    assert test_queue.data.count() == test_queue.length


def test_fill_nonempty_queue(db, test_queue):
    # Manually add one observation so the queue is now nonempty
    test_datum = Data.objects.create(text='test data', project=test_queue.project)
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
    project2_data = read_test_data()

    add_data(test_project2, [d['text'] for d in project2_data])

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
    project2_data = read_test_data()
    add_data(project2, [d['text'] for d in project2_data])
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

    data = get_assignments(test_profile, test_project_data, 5)

    assert len(data) == 5
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

    data = get_assignments(test_profile, test_project_data, 10)

    assert len(data) == 10
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

    data = get_assignments(test_profile, test_project_data, 15)

    assert len(data) == 10
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


def test_create_tfidf_matrix(test_tfidf_matrix):
    assert type(test_tfidf_matrix) == scipy.sparse.csr.csr_matrix
    assert test_tfidf_matrix.shape == (285, 47)
    assert test_tfidf_matrix.dtype == np.float64


def test_save_tfidf_matrix(test_project_data, test_tfidf_matrix, tmpdir):
    pre_dir = tmpdir.mkdir('data').mkdir('tf_idf')
    file = save_tfidf_matrix(test_tfidf_matrix, test_project_data.pk, prefix_dir=str(tmpdir))

    assert os.path.isfile(file)
    assert file == os.path.join(str(tmpdir), 'data/tf_idf/'+ str(test_project_data.pk) + '.npz')


def test_load_tfidf_matrix(test_project_labeled_and_tfidf, test_tfidf_matrix, tmpdir):
    matrix = load_tfidf_matrix(test_project_labeled_and_tfidf, prefix_dir=str(tmpdir))

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


def test_train_and_save_model(test_project_labeled_and_tfidf, tmpdir):
    data_temp = tmpdir.listdir()[0]  # tmpdir already has data directory from test_project_labeled_and_tfidf
    data_temp.mkdir('model_pickles')
    model = train_and_save_model(test_project_labeled_and_tfidf, prefix_dir=str(tmpdir))

    assert isinstance(model, Model)
    assert_obj_exists(Model, {
        'pickle_path': model.pickle_path,
        'project': test_project_labeled_and_tfidf
    })
    assert os.path.isfile(model.pickle_path)


def test_predict_data(test_project_with_trained_model, tmpdir):
    project = test_project_with_trained_model

    predictions = predict_data(project, project.model_set.get(), prefix_dir=str(tmpdir))

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
    data_list = test_queue.data.all()
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in test_queue.data.all():
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
    data_list = test_queue.data.all()
    previous_ms = data_list[0].datauncertainty_set.get().margin_sampling
    for datum in test_queue.data.all():
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
    data_list = test_queue.data.all()
    previous_e = data_list[0].datauncertainty_set.get().entropy
    for datum in test_queue.data.all():
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().entropy <= previous_e
        previous_e = datum.datauncertainty_set.get().entropy
