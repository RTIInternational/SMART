import os
import random

from core import tasks
from core.models import Model, DataPrediction, Data, DataUncertainty
from core.util import (label_data, fill_queue, get_ordered_data,
                       assign_datum, redis_serialize_queue)
from core.serializers import DataSerializer

from test.util import assert_obj_exists, assert_redis_matches_db


def test_celery():
    result = tasks.send_test_task.delay().get()
    assert result == 'Test Task Complete'


def test_model_task(test_project_labeled_and_tfidf, test_queue, test_redis, tmpdir, settings):
    project = test_project_labeled_and_tfidf
    initial_training_set = project.get_current_training_set()
    initial_queue_length = test_queue.length

    model_path_temp = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    tasks.send_model_task.delay(project.pk).get()

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

    # Assert queue correct size
    assert test_queue.length == initial_queue_length

    # Assert least confident in queue
    data_list = get_ordered_data(test_queue.data.all(), 'least confident')
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {
            'data': datum
        })
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert project.get_current_training_set().set_number == initial_training_set.set_number + 1


def test_tfidf_creation_task(test_project_data, tmpdir, settings):
    data_temp = tmpdir.mkdir('data').mkdir('tf_idf')
    settings.TF_IDF_PATH = str(data_temp)

    project = test_project_data
    data = Data.objects.filter(project=project)

    file = tasks.send_tfidf_creation_task.delay(DataSerializer(data, many=True).data, project.pk).get()

    assert os.path.isfile(file)
    assert file == os.path.join(str(data_temp), str(test_project_data.pk) + '.npz')


def test_model_task_redis_no_dupes(test_project_labeled_and_tfidf, test_queue, test_redis, tmpdir, settings):
    project = test_project_labeled_and_tfidf
    initial_training_set = project.get_current_training_set().set_number
    queue = project.queue_set.get()
    queue.length = 40
    queue.save()

    model_path_temp = tmpdir.listdir()[0].mkdir('model_pickles')
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    fill_queue(queue, 'random')

    batch_size = project.labels.count() * 10
    labels = project.labels.all()
    for i in range(batch_size):
        datum = assign_datum(project.creator, project)
        label_data(random.choice(labels), datum, project.creator, 3)

    tasks.send_model_task.delay(project.pk).get()
    assert project.get_current_training_set().set_number == initial_training_set + 1
    redis_items = test_redis.lrange(redis_serialize_queue(queue), 0, -1)
    assert len(redis_items) == len(set(redis_items))
