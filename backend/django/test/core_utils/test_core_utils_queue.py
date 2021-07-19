from test.util import assert_obj_exists, assert_redis_matches_db, read_test_data_backend

from core.models import Data, DataQueue, DataUncertainty, Queue
from core.utils.util import add_data, create_project, md5_hash
from core.utils.utils_queue import (
    add_queue,
    fill_queue,
    find_queue_length,
    get_nonempty_queue,
    pop_first_nonempty_queue,
    pop_queue,
)
from core.utils.utils_redis import get_ordered_data, init_redis


def test_find_queue_length():
    # [batch_size, num_coders, q_length]
    test_vals = [[20, 1, 20], [20, 2, 30], [30, 2, 45], [30, 3, 50]]

    for vals in test_vals:
        q_length = find_queue_length(vals[0], vals[1])
        assert q_length == vals[2]


def test_add_queue_no_profile(test_project):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN)
    assert_obj_exists(
        Queue, {"project": test_project, "length": QUEUE_LEN, "profile": None}
    )


def test_add_queue_profile(test_project, test_profile):
    QUEUE_LEN = 10
    add_queue(test_project, QUEUE_LEN, profile=test_profile)
    assert_obj_exists(
        Queue, {"project": test_project, "length": QUEUE_LEN, "profile": test_profile}
    )


def test_fill_empty_queue(db, test_queue):
    fill_queue(test_queue, orderby="random")

    assert test_queue.data.count() == test_queue.length


def test_fill_nonempty_queue(db, test_queue):
    # Manually add one observation so the queue is now nonempty
    test_datum = Data.objects.create(
        text="test data", project=test_queue.project, upload_id_hash=md5_hash(0)
    )
    DataQueue.objects.create(data=test_datum, queue=test_queue)
    assert test_queue.data.count() == 1

    fill_queue(test_queue, orderby="random")
    assert test_queue.data.count() == test_queue.length


def test_fill_queue_all_remaining_data(db, test_queue):
    # Raise the queue length so it's bigger than the amount of data available
    all_data_count = Data.objects.filter(project=test_queue.project).count()
    test_queue.length = all_data_count + 1
    test_queue.save()

    fill_queue(test_queue, orderby="random")
    assert test_queue.data.count() == all_data_count


def test_fill_multiple_projects(db, test_queue, test_profile):
    project_data_count = test_queue.project.data_set.count()
    test_queue.length = project_data_count + 1
    test_queue.save()
    test_project2 = create_project("test_project2", test_profile)
    project2_data = read_test_data_backend(
        file="./core/data/test_files/test_no_labels.csv"
    )

    add_data(test_project2, project2_data)

    fill_queue(test_queue, orderby="random")

    # Ensure the queue didn't fill any data from the other project
    assert test_queue.data.count() == project_data_count
    assert all((d.project == test_queue.project for d in test_queue.data.all()))


def test_pop_empty_queue(db, test_project, test_redis):
    queue = add_queue(test_project, 10)

    datum = pop_queue(queue)

    assert datum is None
    assert not test_redis.exists("queue:" + str(queue.pk))
    assert queue.data.count() == 0


def test_pop_nonempty_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    fill_queue(queue, orderby="random")

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen("queue:" + str(queue.pk)) == (queue_len - 1)
    assert test_redis.scard("set:" + str(queue.pk)) == (queue_len)
    assert queue.data.count() == queue_len


def test_pop_only_affects_one_queue(db, test_project_data, test_redis):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)
    fill_queue(queue, orderby="random")
    fill_queue(queue2, orderby="random")

    datum = pop_queue(queue)

    assert isinstance(datum, Data)
    assert test_redis.llen("queue:" + str(queue.pk)) == (queue_len - 1)
    assert test_redis.scard("set:" + str(queue.pk)) == (queue_len)
    assert queue.data.count() == queue_len

    assert test_redis.llen("queue:" + str(queue2.pk)) == queue_len
    assert test_redis.scard("set:" + str(queue2.pk)) == (queue_len)
    assert queue2.data.count() == queue_len


def test_get_nonempty_queue_noprofile(db, test_project_data):
    queue_len = 10
    queue = add_queue(test_project_data, queue_len)
    queue2 = add_queue(test_project_data, queue_len)

    assert get_nonempty_queue(test_project_data) is None

    fill_queue(queue2, orderby="random")
    assert get_nonempty_queue(test_project_data) == queue2

    fill_queue(queue, orderby="random")
    assert get_nonempty_queue(test_project_data) == queue


def test_get_nonempty_profile_queue(db, test_project_data, test_profile):
    queue_len = 10
    add_queue(test_project_data, queue_len)
    profile_queue = add_queue(test_project_data, queue_len, profile=test_profile)
    profile_queue2 = add_queue(test_project_data, queue_len, profile=test_profile)

    assert get_nonempty_queue(test_project_data, profile=test_profile) is None

    fill_queue(profile_queue2, orderby="random")
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue2

    fill_queue(profile_queue, orderby="random")
    assert get_nonempty_queue(test_project_data, profile=test_profile) == profile_queue


def test_get_nonempty_queue_multiple_profiles(
    db,
    test_project_data,
    test_profile,
    test_profile2,
    test_profile_queue,
    test_profile_queue2,
):

    assert get_nonempty_queue(test_project_data) is None

    # Fill the correct one last, so we can test whether the first-filled queue is being
    # selected
    for queue in (test_profile_queue2, test_profile_queue):
        fill_queue(queue, orderby="random")

    assert (
        get_nonempty_queue(test_project_data, profile=test_profile)
        == test_profile_queue
    )


def test_pop_first_nonempty_queue_noqueue(db, test_project_data, test_redis):
    init_redis()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert queue is None
    assert data is None


def test_pop_first_nonempty_queue_empty(db, test_project_data, test_queue, test_redis):
    init_redis()

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert queue is None
    assert data is None


def test_pop_first_nonempty_queue_single_queue(
    db, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_profile_queue(
    db, test_project_data, test_profile, test_profile_queue, test_redis
):
    fill_queue(test_profile_queue, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue

    assert isinstance(data, Data)


def test_pop_first_nonempty_queue_multiple_queues(
    db, test_project_data, test_queue, test_redis
):
    test_queue2 = add_queue(test_project_data, 10)
    fill_queue(test_queue2, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue2

    fill_queue(test_queue, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data)

    assert isinstance(queue, Queue)
    assert queue == test_queue


def test_pop_first_nonempty_queue_multiple_profile_queues(
    db,
    test_project_data,
    test_profile,
    test_profile_queue,
    test_profile_queue2,
    test_redis,
):
    fill_queue(test_profile_queue2, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert queue is None
    assert data is None

    fill_queue(test_profile_queue, orderby="random")

    queue, data = pop_first_nonempty_queue(test_project_data, profile=test_profile)

    assert isinstance(queue, Queue)
    assert queue == test_profile_queue


def test_fill_queue_random_predicted_data(
    test_project_predicted_data, test_queue, test_redis
):
    fill_queue(test_queue, "random")

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length
    for datum in test_queue.data.all():
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})


def test_fill_queue_least_confident_predicted_data(
    test_project_predicted_data, test_queue, test_redis
):
    fill_queue(test_queue, "least confident")

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length

    data_list = get_ordered_data(test_queue.data.all(), "least confident")
    previous_lc = data_list[0].datauncertainty_set.get().least_confident
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().least_confident <= previous_lc
        previous_lc = datum.datauncertainty_set.get().least_confident


def test_fill_queue_margin_sampling_predicted_data(
    test_project_predicted_data, test_queue, test_redis
):
    fill_queue(test_queue, "margin sampling")

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length

    data_list = get_ordered_data(test_queue.data.all(), "margin sampling")
    previous_ms = data_list[0].datauncertainty_set.get().margin_sampling
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().margin_sampling >= previous_ms
        previous_ms = datum.datauncertainty_set.get().margin_sampling


def test_fill_queue_entropy_predicted_data(
    test_project_predicted_data, test_queue, test_redis
):
    fill_queue(test_queue, "entropy")

    assert_redis_matches_db(test_redis)
    assert test_queue.data.count() == test_queue.length

    data_list = get_ordered_data(test_queue.data.all(), "entropy")
    previous_e = data_list[0].datauncertainty_set.get().entropy
    for datum in data_list:
        assert len(datum.datalabel_set.all()) == 0
        assert_obj_exists(DataUncertainty, {"data": datum})
        assert datum.datauncertainty_set.get().entropy <= previous_e
        previous_e = datum.datauncertainty_set.get().entropy
