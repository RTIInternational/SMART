from test.util import assert_obj_exists, assert_redis_matches_db, read_test_data_backend

from core.models import AssignedData, Data, DataQueue, Queue
from core.utils.util import add_data, create_project
from core.utils.utils_queue import add_queue, fill_queue
from core.utils.utils_redis import (
    init_redis,
    redis_parse_data,
    redis_parse_list_dataids,
    redis_parse_queue,
    redis_serialize_data,
    redis_serialize_queue,
    redis_serialize_set,
)


def test_redis_serialize_queue(test_queue):
    queue_key = redis_serialize_queue(test_queue)

    assert queue_key == "queue:" + str(test_queue.pk)


def test_redis_serialzie_set(test_queue):
    set_key = redis_serialize_set(test_queue)

    assert set_key == "set:" + str(test_queue.pk)


def test_redis_serialize_data(test_project_data):
    datum = test_project_data.data_set.first()
    data_key = redis_serialize_data(datum)

    assert data_key == "data:" + str(datum.pk)


def test_redis_parse_queue(test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    queue_key = [key for key in test_redis.keys() if "queue" in key.decode()][0]
    parsed_queue = redis_parse_queue(queue_key)

    assert parsed_queue.pk == test_queue.pk
    assert_obj_exists(DataQueue, {"queue_id": parsed_queue.pk})
    assert_obj_exists(Queue, {"pk": parsed_queue.pk})


def test_redis_parse_data(test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    popped_data_key = test_redis.lpop(redis_serialize_queue(test_queue))
    parsed_data = redis_parse_data(popped_data_key)

    assert_obj_exists(Data, {"pk": parsed_data.pk})
    assert_obj_exists(DataQueue, {"data_id": parsed_data.pk})


def test_redis_parse_list_dataids(test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    data_ids = [d.pk for d in test_queue.data.all()]
    redis_ids = test_redis.lrange(redis_serialize_queue(test_queue), 0, -1)
    parsed_ids = redis_parse_list_dataids(redis_ids)

    assert data_ids.sort() == parsed_ids.sort()


def test_init_redis_empty(db, test_redis):
    init_redis()

    assert_redis_matches_db(test_redis)


def test_init_redis_one_empty_queue(db, test_project, test_redis):
    add_queue(test_project, 10)

    test_redis.flushdb()
    init_redis()

    assert_redis_matches_db(test_redis)


def test_init_redis_one_nonempty_queue(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue, orderby="random")

    test_redis.flushdb()
    init_redis()

    assert_redis_matches_db(test_redis)


def test_init_redis_multiple_queues(db, test_project_data, test_redis):
    queue = add_queue(test_project_data, 10)
    fill_queue(queue, orderby="random")

    add_queue(test_project_data, 10)

    test_redis.flushdb()
    init_redis()

    assert_redis_matches_db(test_redis)


def test_init_redis_multiple_projects(db, test_project_data, test_redis, test_profile):
    # Try a mix of multiple queues in multiple projects with
    # and without data to see if everything initializes as expected.
    p1_queue1 = add_queue(test_project_data, 10)
    fill_queue(p1_queue1, orderby="random")
    add_queue(test_project_data, 10)

    project2 = create_project("test_project2", test_profile)
    project2_data = read_test_data_backend(
        file="./core/data/test_files/test_no_labels.csv"
    )

    add_data(project2, project2_data)
    p2_queue1 = add_queue(project2, 10)
    fill_queue(p2_queue1, orderby="random")
    add_queue(project2, 10)

    test_redis.flushdb()
    init_redis()

    assert_redis_matches_db(test_redis)


def test_init_redis_ignores_assigned_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    assigned_datum = test_queue.data.first()

    AssignedData.objects.create(
        profile=test_profile, data=assigned_datum, queue=test_queue
    )

    init_redis()

    # Make sure the assigned datum didn't get into the redis queue
    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length - 1
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length - 1
