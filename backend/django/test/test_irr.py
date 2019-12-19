import math

from core.models import Data, DataLabel, DataQueue, IRRLog
from core.utils.utils_annotate import assign_datum, label_data, skip_data
from core.utils.utils_model import check_and_trigger_model
from core.utils.utils_queue import fill_queue


def test_fill_half_irr_queues(
    setup_celery,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_profile,
    test_redis,
    tmpdir,
    settings,
):
    """Using a project with equal irr settings (50%, 2), check that the normal and irr
    queues get filled correctly."""
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    batch_size = test_project_half_irr_data.batch_size
    percentage_irr = test_project_half_irr_data.percentage_irr
    fill_queue(normal_queue, "random", irr_queue, percentage_irr, batch_size)

    # check that the queue is filled with the correct proportion of IRR and not
    irr_count = math.ceil((percentage_irr / 100) * batch_size)
    non_irr_count = math.ceil(((100 - percentage_irr) / 100) * batch_size)
    num_in_norm = DataQueue.objects.filter(queue=normal_queue).count()
    num_in_irr = DataQueue.objects.filter(queue=irr_queue).count()
    assert (num_in_norm + num_in_irr) == batch_size
    assert num_in_norm == non_irr_count
    assert num_in_irr == irr_count
    assert num_in_norm == num_in_irr

    # check that all of the data in the irr queue is labeled irr_ind=True
    assert DataQueue.objects.filter(queue=irr_queue, data__irr_ind=False).count() == 0
    # check that NONE of the data in the normal queue is irr_ind=True
    assert DataQueue.objects.filter(queue=normal_queue, data__irr_ind=True).count() == 0
    # check that there is no duplicate data across the two queues
    data_irr = DataQueue.objects.filter(queue=irr_queue).values_list(
        "data__hash", flat=True
    )
    data_norm = DataQueue.objects.filter(queue=normal_queue).values_list(
        "data__hash", flat=True
    )
    assert len(set(data_irr) & set(data_norm)) == 0


def test_annotate_irr(
    setup_celery,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_profile,
    test_profile2,
    test_profile3,
    test_labels_half_irr,
    test_redis,
    tmpdir,
    settings,
):
    """This tests the irr labeling workflow, and checks that the data is in the correct
    models."""
    project = test_project_half_irr_data
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )
    # get an irr datum. One should exist.
    datum = assign_datum(test_profile, project, "irr")
    assert datum is not None

    # let one user label a datum. It should be in DataLabel, not be in IRRLog,
    # still be in IRR Queue
    label_data(test_labels_half_irr[0], datum, test_profile, 3)
    assert DataLabel.objects.filter(data=datum, profile=test_profile).count() > 0
    assert IRRLog.objects.filter(data=datum, profile=test_profile).count() == 0
    assert DataQueue.objects.filter(data=datum, queue=irr_queue).count() > 0

    datum2 = assign_datum(test_profile2, project, "irr")
    assert datum.pk == datum2.pk

    datum3 = assign_datum(test_profile3, project, "irr")
    assert datum.pk == datum3.pk

    # let other user label the same datum. It should now be in datatable with
    # creater=profile, be in IRRLog (twice), not be in IRRQueue
    label_data(test_labels_half_irr[0], datum2, test_profile2, 3)
    assert DataLabel.objects.filter(data=datum2).count() == 1
    assert DataLabel.objects.get(data=datum2).profile.pk == project.creator.pk
    assert IRRLog.objects.filter(data=datum2).count() == 2
    assert DataQueue.objects.filter(data=datum2, queue=irr_queue).count() == 0

    # let a third user label the first data something else. It should be in
    # IRRLog but not overwrite the label from before
    label_data(test_labels_half_irr[0], datum3, test_profile3, 3)
    assert IRRLog.objects.filter(data=datum3).count() == 3
    assert DataLabel.objects.filter(data=datum3).count() == 1
    assert DataLabel.objects.get(data=datum3).profile.pk == project.creator.pk

    # let two users disagree on a datum. It should be in the admin queue,
    # not in irr queue, not in datalabel, in irrlog twice
    second_datum = assign_datum(test_profile, project, "irr")
    # should be a new datum
    assert datum.pk != second_datum.pk
    second_datum2 = assign_datum(test_profile2, project, "irr")
    label_data(test_labels_half_irr[0], second_datum, test_profile, 3)
    label_data(test_labels_half_irr[1], second_datum2, test_profile2, 3)
    assert DataQueue.objects.filter(data=second_datum2, queue=admin_queue).count() == 1
    assert DataQueue.objects.filter(data=second_datum2, queue=irr_queue).count() == 0
    assert DataLabel.objects.filter(data=second_datum2).count() == 0
    assert IRRLog.objects.filter(data=second_datum2).count() == 2


def test_skip_irr(
    setup_celery,
    test_project_half_irr_data,
    test_half_irr_all_queues,
    test_profile,
    test_profile2,
    test_profile3,
    test_labels_half_irr,
    test_redis,
    tmpdir,
    settings,
):
    """This tests the skip function, and see if the data is in the correct places."""
    project = test_project_half_irr_data
    normal_queue, admin_queue, irr_queue = test_half_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )
    # get an irr datum. One should exist.
    datum = assign_datum(test_profile, project, "irr")
    assert datum is not None

    # let one user skip an irr datum. It should not be in adminqueue, should be in irr queue,
    # should be in irrlog, should be in irr queue, not be in datalabel
    skip_data(datum, test_profile)
    assert DataQueue.objects.filter(data=datum, queue=admin_queue).count() == 0
    assert DataQueue.objects.filter(data=datum, queue=irr_queue).count() == 1
    assert IRRLog.objects.filter(data=datum, profile=test_profile).count() == 1
    assert DataLabel.objects.filter(data=datum, profile=test_profile).count() == 0

    # let the other user skip the data. It should be in admin queue,
    # IRRlog (twice), and nowhere else.
    datum2 = assign_datum(test_profile2, project, "irr")
    assert datum.pk == datum2.pk
    skip_data(datum2, test_profile2)
    assert DataQueue.objects.filter(data=datum, queue=admin_queue).count() == 1
    assert DataQueue.objects.filter(data=datum, queue=irr_queue).count() == 0
    assert IRRLog.objects.filter(data=datum).count() == 2
    assert DataLabel.objects.filter(data=datum).count() == 0

    # have two users label an IRR datum then have a third user skip it.
    # It should be in the IRRLog but not in admin queue or anywhere else.
    second_datum = assign_datum(test_profile, project, "irr")
    second_datum2 = assign_datum(test_profile2, project, "irr")
    assert second_datum.pk != datum.pk
    assert second_datum.pk == second_datum2.pk
    second_datum3 = assign_datum(test_profile3, project, "irr")
    assert second_datum2.pk == second_datum3.pk

    label_data(test_labels_half_irr[0], second_datum, test_profile, 3)
    label_data(test_labels_half_irr[0], second_datum2, test_profile2, 3)
    skip_data(second_datum3, test_profile3)
    assert DataQueue.objects.filter(data=second_datum3, queue=admin_queue).count() == 0
    assert DataQueue.objects.filter(data=second_datum3, queue=irr_queue).count() == 0
    assert IRRLog.objects.filter(data=second_datum3).count() == 3
    assert DataLabel.objects.filter(data=second_datum3).count() == 1


def test_queue_refill(
    setup_celery,
    test_project_data,
    test_all_queues,
    test_profile,
    test_labels,
    test_redis,
    tmpdir,
    settings,
):
    """Check that the queues refill the way they should.

    Have one person label everything in a batch. Check that the queue refills but the irr queue now has twice the irr% * batch amount
    """
    project = test_project_data
    normal_queue, admin_queue, irr_queue = test_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    irr_count = math.ceil((project.percentage_irr / 100) * project.batch_size)
    non_irr_count = math.ceil(
        ((100 - project.percentage_irr) / 100) * project.batch_size
    )

    for i in range(non_irr_count):
        datum = assign_datum(test_profile, project, "normal")
        assert datum is not None
        label_data(test_labels[0], datum, test_profile, 3)
        check_and_trigger_model(datum, test_profile)
    for i in range(irr_count):
        datum = assign_datum(test_profile, project, "irr")
        assert datum is not None
        label_data(test_labels[0], datum, test_profile, 3)
        check_and_trigger_model(datum, test_profile)
    assert DataQueue.objects.filter(queue=normal_queue).count() == non_irr_count
    assert DataQueue.objects.filter(queue=irr_queue).count() == irr_count * 2


def test_no_irr(
    setup_celery,
    test_project_no_irr_data,
    test_no_irr_all_queues,
    test_profile,
    test_labels_no_irr,
    test_redis,
    tmpdir,
    settings,
):
    """This tests a case where the IRR percentage is 0."""
    project = test_project_no_irr_data
    normal_queue, admin_queue, irr_queue = test_no_irr_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # check that the normal queue is filled and the IRR queue is empty
    assert DataQueue.objects.filter(queue=irr_queue).count() == 0
    assert DataQueue.objects.filter(queue=normal_queue).count() == project.batch_size

    # check that no data has irr_ind=True
    assert Data.objects.filter(irr_ind=True).count() == 0


def test_all_irr(
    setup_celery,
    test_project_all_irr_3_coders_data,
    test_all_irr_3_coders_all_queues,
    test_profile,
    test_profile2,
    test_profile3,
    test_labels_all_irr_3_coders,
    test_redis,
    tmpdir,
    settings,
):
    """This tests the case with 100% IRR and triple labeling required."""
    project = test_project_all_irr_3_coders_data
    labels = test_labels_all_irr_3_coders
    normal_queue, admin_queue, irr_queue = test_all_irr_3_coders_all_queues
    fill_queue(
        normal_queue, "random", irr_queue, project.percentage_irr, project.batch_size
    )

    # check the normal queue is empty and the irr queue is full
    assert DataQueue.objects.filter(queue=irr_queue).count() == project.batch_size
    assert DataQueue.objects.filter(queue=normal_queue).count() == 0

    # check everything in the irr queue has irr_ind = true
    assert (
        DataQueue.objects.filter(queue=irr_queue, data__irr_ind=True).count()
        == project.batch_size
    )

    # have one person label three datum and check that they are still in the queue
    datum = assign_datum(test_profile, project, "irr")
    second_datum = assign_datum(test_profile, project, "irr")
    third_datum = assign_datum(test_profile, project, "irr")
    assert datum.pk != second_datum.pk
    assert third_datum.pk != second_datum.pk

    label_data(labels[0], datum, test_profile, 3)
    label_data(labels[0], second_datum, test_profile, 3)
    label_data(labels[0], third_datum, test_profile, 3)

    assert (
        DataQueue.objects.filter(
            queue=irr_queue, data__in=[datum, second_datum, third_datum]
        ).count()
        == 3
    )

    # have one person skip all three datum, and check that they are still in the irr queue, in irrlog, and in datalabel, but not in admin queue
    datum2 = assign_datum(test_profile2, project, "irr")
    second_datum2 = assign_datum(test_profile2, project, "irr")
    third_datum2 = assign_datum(test_profile2, project, "irr")

    assert datum.pk == datum2.pk
    assert second_datum.pk == second_datum2.pk
    assert third_datum.pk == third_datum2.pk

    skip_data(datum2, test_profile2)
    skip_data(second_datum2, test_profile2)
    skip_data(third_datum2, test_profile2)

    assert (
        DataQueue.objects.filter(
            data__in=[datum2, second_datum2, third_datum2], queue=irr_queue
        ).count()
        == 3
    )
    assert (
        DataQueue.objects.filter(
            data__in=[datum2, second_datum2, third_datum2], queue=admin_queue
        ).count()
        == 0
    )
    assert (
        IRRLog.objects.filter(data__in=[datum2, second_datum2, third_datum2]).count()
        == 3
    )
    assert (
        DataLabel.objects.filter(data__in=[datum2, second_datum2, third_datum2]).count()
        == 3
    )

    # have the third person label all three datum and check that they are in the log and admin queue, but not in irr queue or datalabel
    datum3 = assign_datum(test_profile3, project, "irr")
    second_datum3 = assign_datum(test_profile3, project, "irr")
    third_datum3 = assign_datum(test_profile3, project, "irr")

    assert datum.pk == datum3.pk
    assert second_datum.pk == second_datum3.pk
    assert third_datum.pk == third_datum3.pk

    label_data(labels[0], datum3, test_profile3, 3)
    label_data(labels[1], second_datum3, test_profile3, 3)
    label_data(labels[0], third_datum3, test_profile3, 3)

    assert (
        DataQueue.objects.filter(
            data__in=[datum3, second_datum3, third_datum3], queue=irr_queue
        ).count()
        == 0
    )
    assert (
        DataQueue.objects.filter(
            data__in=[datum3, second_datum3, third_datum3], queue=admin_queue
        ).count()
        == 3
    )
    assert (
        IRRLog.objects.filter(data__in=[datum3, second_datum3, third_datum3]).count()
        == 9
    )
    assert (
        DataLabel.objects.filter(data__in=[datum3, second_datum3, third_datum3]).count()
        == 0
    )
