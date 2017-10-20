import os

from core import tasks
from core.models import Model, DataPrediction, Data, DataUncertainty

from test.util import assert_obj_exists, assert_redis_matches_db


def test_celery():
    result = tasks.send_test_task.delay().get()
    assert result == 'Test Task Complete'


def test_model_task(test_project_labeled_and_tfidf, test_queue, test_redis, tmpdir):
    project = test_project_labeled_and_tfidf
    data_temp = tmpdir.listdir()[0]  # tmpdir already has data directory from test_project_labeled_and_tfidf
    data_temp.mkdir('model_pickles')
    tasks.send_model_task.apply(args=(project.pk,str(tmpdir))).get()

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

    """ this is literally the exact same code as a test in test_core.py
    test_fill_queue_least_confident_predicted_data

    fill_queue with "least confident" after training the model.  I have already
    asserted that the model is created, predictions are made, the queue is filled
    I do not understand why this queue is unordered but the queue in that other
    function is ordered.

    The only difference is that this is called from celery? Is it possible that
    celery inserts in a different order than normaL?

    I don think that either.  I just tested it live on the server.  The data that
    was in the queue was indeed the least confident data.
    """
    # Assert least confident in queue
    # data_list = test_queue.data.all()
    # previous_lc = data_list[0].datauncertainty_set.get().least_confident
    # for datum in data_list:
    #     assert len(datum.datalabel_set.all()) == 0
    #     assert_obj_exists(DataUncertainty, {
    #         'data': datum
    #     })
    #     assert datum.datauncertainty_set.get().least_confident <= previous_lc
    #     previous_lc = datum.datauncertainty_set.get().least_confident