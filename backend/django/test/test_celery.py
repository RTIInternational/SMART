import os

from core import tasks
from core.models import Model, DataPrediction, Data, DataUncertainty
from core.util import get_ordered_queue_data

from test.util import assert_obj_exists, assert_redis_matches_db


def test_celery():
    result = tasks.send_test_task.delay().get()
    assert result == 'Test Task Complete'


def test_model_task(test_project_labeled_and_tfidf, test_queue, test_redis, tmpdir):
    project = test_project_labeled_and_tfidf
    data_temp = tmpdir.listdir()[0]  # tmpdir already has data directory from test_project_labeled_and_tfidf
    data_temp.mkdir('model_pickles')

    tasks.send_model_task.delay(project.pk, str(tmpdir)).get()

    # Assert model created and saved
    assert_obj_exists(Model, {
        'project': project
    })
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert len(predictions) == Data.objects.filter(project=project,
                                                   labelers=None).count() * project.labels.count()

    # Assert queue filled and redis sycned
    assert test_queue.data.count() == test_queue.length
    assert_redis_matches_db(test_redis)

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


def test_tfidf_creation_task(test_project_data, tmpdir):
    pre_dir = tmpdir.mkdir('data').mkdir('tf_idf')
    project = test_project_data
    data_list = [d.text for d in project.data_set.all()]

    file = tasks.send_tfidf_creation_task.delay(data_list, project.pk, str(tmpdir)).get()

    assert os.path.isfile(file)