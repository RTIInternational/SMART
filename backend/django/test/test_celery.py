import os
import random
from test.util import assert_obj_exists, assert_redis_matches_db

from core import tasks
from core.models import Data, DataPrediction, DataUncertainty, Model, ProjectPermissions
from core.utils.util import create_profile
from core.utils.utils_annotate import (
    assign_datum,
    batch_unassign,
    get_assignments,
    label_data,
)
from core.utils.utils_queue import fill_queue
from core.utils.utils_redis import get_ordered_data, redis_serialize_queue


def test_celery():
    result = tasks.send_test_task.delay().get()
    assert result == "Test Task Complete"


def test_model_task(
    test_project_labeled_and_tfidf,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_redis,
    tmpdir,
    settings,
):
    project = test_project_labeled_and_tfidf
    test_queue = test_queue_labeled
    initial_training_set = project.get_current_training_set()
    initial_queue_length = test_queue.length

    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    tasks.send_model_task.delay(project.pk).get()

    # Assert model created and saved
    assert_obj_exists(Model, {"project": project})
    model = Model.objects.get(project=project)
    assert os.path.isfile(model.pickle_path)
    assert model.pickle_path == os.path.join(
        str(model_path_temp),
        "project_"
        + str(project.pk)
        + "_training_"
        + str(initial_training_set.set_number)
        + ".pkl",
    )

    # Assert predictions created
    predictions = DataPrediction.objects.filter(data__project=project)
    assert (
        len(predictions)
        == Data.objects.filter(project=project, labelers=None).count()
        * project.labels.count()
    )

    # Assert bothe queues are filled and redis sycned
    assert (
        test_queue.data.count() + test_irr_queue_labeled.data.count()
    ) == test_queue.length
    assert_redis_matches_db(test_redis)

    # Assert queue correct size
    assert test_queue.length == initial_queue_length

    # Assert least confident in queue
    data_list = get_ordered_data(test_queue.data.all(), "least confident")
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident

    # Assert new training set
    assert project.get_current_training_set() != initial_training_set
    assert (
        project.get_current_training_set().set_number
        == initial_training_set.set_number + 1
    )


def test_tfidf_creation_task(test_project_data, tmpdir, settings):
    data_temp = tmpdir.mkdir("data").mkdir("tf_idf")
    settings.TF_IDF_PATH = str(data_temp)

    project = test_project_data
    Data.objects.filter(project=project)

    file = tasks.send_tfidf_creation_task.delay(project.pk).get()

    assert os.path.isfile(file)
    assert file == os.path.join(
        str(data_temp), "project_" + str(test_project_data.pk) + "_tfidf_matrix.pkl"
    )


def test_model_task_redis_no_dupes_data_left_in_queue(
    test_project_labeled_and_tfidf,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_admin_queue_labeled,
    test_redis,
    tmpdir,
    settings,
):
    project = test_project_labeled_and_tfidf
    initial_training_set = project.get_current_training_set().set_number
    queue = project.queue_set.get(type="normal")
    queue.length = 40
    queue.save()

    irr_queue = project.queue_set.get(type="irr")
    irr_queue.length = 40
    irr_queue.save()

    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    batch_size = project.batch_size
    fill_queue(
        queue,
        "random",
        irr_queue,
        irr_percent=project.percentage_irr,
        batch_size=batch_size,
    )

    labels = project.labels.all()
    for i in range(int(batch_size * ((100 - project.percentage_irr) / 100))):
        datum = assign_datum(project.creator, project)
        label_data(random.choice(labels), datum, project.creator, 3)

    tasks.send_model_task.delay(project.pk).get()
    assert project.get_current_training_set().set_number == initial_training_set + 1
    redis_items = test_redis.lrange(redis_serialize_queue(queue), 0, -1)
    assert len(redis_items) == len(set(redis_items))


def test_model_task_redis_no_dupes_data_unassign_assigned_data(
    test_project_labeled_and_tfidf,
    test_queue_labeled,
    test_irr_queue_labeled,
    test_admin_queue_labeled,
    test_redis,
    tmpdir,
    settings,
):
    project = test_project_labeled_and_tfidf
    person2 = create_profile("test_profilezzz", "password", "test_profile@rti.org")
    person3 = create_profile("test_profile2", "password", "test_profile@rti.org")
    ProjectPermissions.objects.create(
        profile=person2, project=project, permission="CODER"
    )
    ProjectPermissions.objects.create(
        profile=person3, project=project, permission="CODER"
    )
    initial_training_set = project.get_current_training_set().set_number
    queue = project.queue_set.get(type="normal")
    queue.length = 40
    queue.save()

    irr_queue = project.queue_set.get(type="irr")
    irr_queue.length = 40
    irr_queue.save()

    model_path_temp = tmpdir.listdir()[0].mkdir("model_pickles")
    settings.MODEL_PICKLE_PATH = str(model_path_temp)

    batch_size = project.batch_size
    fill_queue(
        queue,
        "random",
        irr_queue,
        irr_percent=project.percentage_irr,
        batch_size=batch_size,
    )

    labels = project.labels.all()
    assignments = get_assignments(project.creator, project, batch_size)
    for assignment in assignments:
        label_data(random.choice(labels), assignment, project.creator, 3)

    tasks.send_model_task.delay(project.pk).get()
    assert project.get_current_training_set().set_number == initial_training_set + 1
    redis_items = test_redis.lrange(redis_serialize_queue(queue), 0, -1)
    assert len(redis_items) == len(set(redis_items))

    assignments = get_assignments(project.creator, project, 40)
    for assignment in assignments[:batch_size]:
        label_data(random.choice(labels), assignment, project.creator, 3)

    tasks.send_model_task.delay(project.pk).get()
    assert project.get_current_training_set().set_number == initial_training_set + 2
    redis_items = test_redis.lrange(redis_serialize_queue(queue), 0, -1)
    assert len(redis_items) == len(set(redis_items))

    batch_unassign(project.creator)
    redis_items = test_redis.lrange(redis_serialize_queue(queue), 0, -1)
    assert len(redis_items) == len(set(redis_items))
