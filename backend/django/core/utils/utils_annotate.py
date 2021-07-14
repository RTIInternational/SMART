from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import AssignedData, Data, DataLabel, DataQueue, IRRLog, Queue
from core.templatetags import project_extras
from core.utils.utils_queue import pop_first_nonempty_queue
from core.utils.utils_redis import (
    redis_serialize_data,
    redis_serialize_queue,
    redis_serialize_set,
)


def assign_datum(profile, project, type="normal"):
    """Given a profile and project, figure out which queue to pull from; then pop a
    datum off that queue and assign it to the profile."""
    with transaction.atomic():
        queue, datum = pop_first_nonempty_queue(project, profile=profile, type=type)
        if datum is None:
            return None
        else:
            num_labeled = DataLabel.objects.filter(data=datum, profile=profile).count()
            if num_labeled == 0:
                AssignedData.objects.create(data=datum, profile=profile, queue=queue)
                return datum
            else:
                return None


def move_skipped_to_admin_queue(datum, profile, project):
    """Remove the data from AssignedData and redis.

    Change the assigned queue to the admin one for this project
    """
    new_queue = Queue.objects.get(project=project, type="admin")
    with transaction.atomic():
        # remove the data from the assignment table
        assignment = AssignedData.objects.get(data=datum, profile=profile)
        queue = assignment.queue
        assignment.delete()

        # change the queue to the admin one
        DataQueue.objects.filter(data=datum, queue=queue).update(queue=new_queue)

    # remove the data from redis
    settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))
    settings.REDIS.sadd(redis_serialize_set(new_queue), redis_serialize_data(datum))


def get_assignments(profile, project, num_assignments):
    """Check if a data is currently assigned to this profile/project; If so, return
    max(num_assignments, len(assigned) of it.

    If not, try to get a num_assigments of new assignments and return them.
    """
    existing_assignments = AssignedData.objects.filter(
        profile=profile, queue__project=project
    )

    if len(existing_assignments) > 0:
        return [
            assignment.data for assignment in existing_assignments[:num_assignments]
        ]
    else:
        data = []
        more_irr = True
        for i in range(num_assignments):

            # first try to get any IRR data
            if more_irr:
                assigned_datum = assign_datum(profile, project, type="irr")
                if assigned_datum is None:
                    # no irr data found
                    more_irr = False
                    assigned_datum = assign_datum(profile, project)
            else:
                # get normal data
                assigned_datum = assign_datum(profile, project)
            if assigned_datum is None:
                break
            data.append(assigned_datum)
        return data


def unassign_datum(datum, profile):
    """Remove a profile's assignment to a datum.

    Re-add the datum to its respective queue in Redis.
    """
    assignment = AssignedData.objects.filter(profile=profile, data=datum).get()

    queue = assignment.queue
    assignment.delete()

    settings.REDIS.lpush(redis_serialize_queue(queue), redis_serialize_data(datum))


def batch_unassign(profile):
    """Remove all of a profile's assignments and Re-add them to its respective queue in
    Redis."""
    assignments = AssignedData.objects.filter(profile=profile)

    for a in assignments:
        unassign_datum(a.data, profile)


def skip_data(datum, profile):
    """Record that a given datum has been skipped."""
    project = datum.project

    IRRLog.objects.create(
        data=datum, profile=profile, label=None, timestamp=timezone.now()
    )
    num_history = IRRLog.objects.filter(data=datum).count()
    # if the datum is irr or processed irr, dont add to admin queue yet
    if datum.irr_ind or num_history > 0:
        # if the IRR history has more than the needed number of labels , it is
        # already processed so don't do anything else
        if num_history <= project.num_users_irr:
            process_irr_label(datum, None)

        # unassign the skipped item
        assignment = AssignedData.objects.get(data=datum, profile=profile)
        assignment.delete()
    else:
        # Make sure coder still has permissions before labeling data
        if project_extras.proj_permission_level(project, profile) > 0:
            move_skipped_to_admin_queue(datum, profile, project)


def label_data(label, datum, profile, time):
    """Record that a given datum has been labeled; remove its assignment, if any.

    Remove datum from DataQueue and its assocaited redis set.
    """
    current_training_set = datum.project.get_current_training_set()
    irr_data = datum.irr_ind

    with transaction.atomic():
        DataLabel.objects.create(
            data=datum,
            label=label,
            profile=profile,
            training_set=current_training_set,
            time_to_label=time,
            timestamp=timezone.now(),
        )
        # There's a unique constraint on data/profile, so this is
        # guaranteed to return one object
        assignment = AssignedData.objects.filter(data=datum, profile=profile).get()
        queue = assignment.queue
        assignment.delete()

        if not irr_data:
            DataQueue.objects.filter(data=datum, queue=queue).delete()
        else:
            num_history = IRRLog.objects.filter(data=datum).count()
            # if the IRR history has more than the needed number of labels , it is
            # already processed so just add this label to the history.
            if num_history >= datum.project.num_users_irr:
                IRRLog.objects.create(
                    data=datum, profile=profile, label=label, timestamp=timezone.now()
                )
                DataLabel.objects.get(data=datum, profile=profile).delete()
            else:
                process_irr_label(datum, label)
    if not irr_data:
        settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))


def process_irr_label(data, label):
    """This function checks if an irr datum has been labeled by enough people.

    if it has, then it will attempt to resolve the labels and record the irr history
    """
    # get the number of labels for that data in the project
    labeled = DataLabel.objects.filter(data=data)
    skipped = IRRLog.objects.filter(label__isnull=True, data=data)
    project = data.project
    current_training_set = project.get_current_training_set()

    admin_queue = Queue.objects.get(project=project, type="admin")
    # if there are >= labels or skips than the project calls for
    if (labeled.count() + skipped.count()) >= project.num_users_irr:
        # add all labels to IRRLog
        history_list = [
            IRRLog(data=data, profile=d.profile, label=d.label, timestamp=d.timestamp)
            for d in labeled
        ]
        with transaction.atomic():
            IRRLog.objects.bulk_create(history_list)

            # remove all labels from DataLabel and save in list
            labels = list(labeled.values_list("label", flat=True))

            DataLabel.objects.filter(data=data).delete()

            # check if the labels agree
            if len(set(labels)) == 1 and skipped.count() == 0:
                # the data is no longer seen as irr (so it can be in the training set)
                Data.objects.filter(pk=data.pk).update(irr_ind=False)
                agree = True
                # if they do, add a new element to dataLabel with one label
                # by creator and remove from the irr queue
                DataLabel.objects.create(
                    data=data,
                    profile=project.creator,
                    label=label,
                    training_set=current_training_set,
                    time_to_label=None,
                    timestamp=timezone.now(),
                )
                DataQueue.objects.filter(data=data).delete()
            else:
                agree = False
                # if they don't, update the data into the admin queue
                DataQueue.objects.filter(data=data).update(queue=admin_queue)

        # update redis to reflect the queue changes
        irr_queue = Queue.objects.get(project=project, type="irr")
        settings.REDIS.srem(redis_serialize_set(irr_queue), redis_serialize_data(data))

        if not agree:
            settings.REDIS.sadd(
                redis_serialize_set(admin_queue), redis_serialize_data(data)
            )
