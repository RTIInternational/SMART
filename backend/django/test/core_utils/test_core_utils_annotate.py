from test.conftest import TEST_QUEUE_LEN
from test.util import assert_obj_exists

from core.models import AssignedData, Data, DataLabel, DataQueue, Label
from core.utils.utils_annotate import (
    assign_datum,
    get_assignments,
    label_data,
    move_skipped_to_admin_queue,
    unassign_datum,
)
from core.utils.utils_queue import fill_queue


def test_assign_datum_project_queue_returns_datum(
    db, test_queue, test_profile, test_redis
):
    """Assign a datum from a project-wide queue (null profile ID)."""
    fill_queue(test_queue, orderby="random")

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure we got the datum
    assert isinstance(datum, Data)


def test_assign_datum_project_queue_correct_assignment(
    db, test_queue, test_profile, test_redis
):
    fill_queue(test_queue, orderby="random")

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the assignment is correct
    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_project_queue_pops_queues(
    db, test_queue, test_profile, test_redis
):
    fill_queue(test_queue, orderby="random")

    datum = assign_datum(test_profile, test_queue.project)

    # Make sure the datum was removed from queues but not set
    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length - 1
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length

    # but not from the db queue
    assert test_queue.data.count() == test_queue.length
    assert datum in test_queue.data.all()


def test_assign_datum_profile_queue_returns_correct_datum(
    db, test_profile_queue, test_profile, test_profile_queue2, test_profile2, test_redis
):
    fill_queue(test_profile_queue, orderby="random")
    fill_queue(test_profile_queue2, orderby="random")

    datum = assign_datum(test_profile, test_profile_queue.project)

    assert isinstance(datum, Data)


def test_assign_datum_profile_queue_correct_assignment(
    db, test_profile_queue, test_profile, test_profile_queue2, test_profile2, test_redis
):
    fill_queue(test_profile_queue, orderby="random")
    fill_queue(test_profile_queue2, orderby="random")

    datum = assign_datum(test_profile, test_profile_queue.project)

    assignment = AssignedData.objects.filter(data=datum)
    assert len(assignment) == 1
    assert assignment[0].profile == test_profile
    assert assignment[0].queue == test_profile_queue
    assert assignment[0].assigned_timestamp is not None


def test_assign_datum_profile_queue_pops_queues(
    db, test_profile_queue, test_profile, test_profile_queue2, test_profile2, test_redis
):
    fill_queue(test_profile_queue, orderby="random")
    fill_queue(test_profile_queue2, orderby="random")

    datum = assign_datum(test_profile, test_profile_queue.project)

    # Make sure the datum was removed from the correct queues but not sets
    assert (
        test_redis.llen("queue:" + str(test_profile_queue.pk))
        == test_profile_queue.length - 1
    )
    assert (
        test_redis.scard("set:" + str(test_profile_queue.pk))
        == test_profile_queue.length
    )

    # ...but not the other queues
    assert test_profile_queue.data.count() == test_profile_queue.length
    assert datum in test_profile_queue.data.all()
    assert (
        test_redis.llen("queue:" + str(test_profile_queue2.pk))
        == test_profile_queue2.length
    )
    assert (
        test_redis.scard("set:" + str(test_profile_queue2.pk))
        == test_profile_queue2.length
    )
    assert test_profile_queue2.data.count() == test_profile_queue2.length


def test_label_data(db, test_profile, test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    datum = assign_datum(test_profile, test_queue.project)
    test_label = Label.objects.create(name="test", project=test_queue.project)
    label_data(test_label, datum, test_profile, 3)

    # Make sure the label was properly recorded
    assert datum in test_profile.labeled_data.all()
    assert_obj_exists(
        DataLabel,
        {
            "data": datum,
            "profile": test_profile,
            "label": test_label,
            "time_to_label": 3,
        },
    )

    # Make sure the assignment was removed
    assert not AssignedData.objects.filter(
        profile=test_profile, data=datum, queue=test_queue
    ).exists()


def test_get_assignments_no_existing_assignment_one_assignment(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, 1)

    assert len(data) == 1
    assert isinstance(data[0], Data)
    assert_obj_exists(AssignedData, {"data": data[0], "profile": test_profile})


def test_get_assignments_no_existing_assignment_half_max_queue_length(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN // 2)

    assert len(data) == TEST_QUEUE_LEN // 2
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {"data": datum, "profile": test_profile})


def test_get_assignments_no_existing_assignment_max_queue_length(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN)

    assert len(data) == TEST_QUEUE_LEN
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {"data": datum, "profile": test_profile})


def test_get_assignments_no_existing_assignment_over_max_queue_length(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assert AssignedData.objects.count() == 0

    data = get_assignments(test_profile, test_project_data, TEST_QUEUE_LEN + 10)

    assert len(data) == TEST_QUEUE_LEN
    for datum in data:
        assert isinstance(datum, Data)
        assert_obj_exists(AssignedData, {"data": datum, "profile": test_profile})


def test_get_assignments_one_existing_assignment(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assigned_datum = assign_datum(test_profile, test_project_data)

    data = get_assignments(test_profile, test_project_data, 1)

    assert isinstance(data[0], Data)
    # We should just get the datum that was already assigned
    assert data[0] == assigned_datum


def test_get_assignments_multiple_existing_assignments(
    db, test_profile, test_project_data, test_queue, test_redis
):
    fill_queue(test_queue, orderby="random")

    assigned_data = []
    for i in range(5):
        assigned_data.append(assign_datum(test_profile, test_project_data))

    data = get_assignments(test_profile, test_project_data, 5)

    assert len(data) == 5
    assert len(data) == len(assigned_data)
    for datum, assigned_datum in zip(data, assigned_data):
        assert isinstance(datum, Data)
    # We should just get the data that was already assigned
    assert len(data) == len(assigned_data)


def test_unassign(db, test_profile, test_project_data, test_queue, test_redis):
    fill_queue(test_queue, orderby="random")

    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length

    datum = get_assignments(test_profile, test_project_data, 1)[0]

    assert test_redis.llen("queue:" + str(test_queue.pk)) == (test_queue.length - 1)
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length
    assert AssignedData.objects.filter(data=datum, profile=test_profile).exists()

    unassign_datum(datum, test_profile)

    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length
    assert not AssignedData.objects.filter(data=datum, profile=test_profile).exists()

    # The unassigned datum should be the next to be assigned
    reassigned_datum = get_assignments(test_profile, test_project_data, 1)[0]

    assert reassigned_datum == datum


def test_unassign_after_fillqueue(
    db, test_profile, test_project_data, test_queue, test_labels, test_redis
):
    fill_queue(test_queue, "random")

    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length

    data = get_assignments(test_profile, test_project_data, 10)

    assert test_redis.llen("queue:" + str(test_queue.pk)) == (test_queue.length - 10)
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length

    test_label = test_labels[0]
    for i in range(5):
        label_data(test_label, data[i], test_profile, 3)

    assert test_redis.llen("queue:" + str(test_queue.pk)) == (test_queue.length - 10)
    assert test_redis.scard("set:" + str(test_queue.pk)) == (test_queue.length - 5)

    fill_queue(test_queue, "random")

    assert test_redis.llen("queue:" + str(test_queue.pk)) == test_queue.length - 5
    assert test_redis.scard("set:" + str(test_queue.pk)) == test_queue.length


def test_skip_data(db, test_profile, test_queue, test_admin_queue, test_redis):
    fill_queue(test_queue, orderby="random")
    project = test_queue.project
    datum = assign_datum(test_profile, project)
    move_skipped_to_admin_queue(datum, test_profile, project)

    # Make sure the assignment was removed
    assert not AssignedData.objects.filter(
        profile=test_profile, data=datum, queue=test_queue
    ).exists()
    # make sure the item was re-assigned to the admin queue
    assert DataQueue.objects.filter(data=datum, queue=test_admin_queue).exists()
    # make sure not in normal queue
    assert not DataQueue.objects.filter(data=datum, queue=test_queue).exists()
