import math
import random

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.models import (
    AdminProgress,
    AssignedData,
    Data,
    DataLabel,
    DataQueue,
    IRRLog,
    Label,
    LabelChangeLog,
    Project,
    Queue,
    RecycleBin,
)
from core.permissions import IsAdminOrCreator, IsCoder
from core.serializers import DataSerializer, LabelSerializer
from core.templatetags import project_extras
from core.utils.utils_annotate import (
    get_assignments,
    label_data,
    move_skipped_to_admin_queue,
    process_irr_label,
    unassign_datum,
)
from core.utils.utils_model import check_and_trigger_model
from core.utils.utils_redis import redis_serialize_data, redis_serialize_set


@api_view(["GET"])
@permission_classes((IsCoder,))
def get_card_deck(request, project_pk):
    """Grab data using get_assignments and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
        data: The data in the queue
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # Calculate queue parameters
    batch_size = project.batch_size
    num_coders = len(project.projectpermissions_set.all()) + 1
    coder_size = math.ceil(batch_size / num_coders)

    data = get_assignments(profile, project, coder_size)

    # shuffle so the irr is not all at the front
    random.shuffle(data)
    labels = Label.objects.all().filter(project=project)

    return Response(
        {
            "labels": LabelSerializer(labels, many=True).data,
            "data": DataSerializer(data, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def label_distribution_inverted(request, project_pk):
    """This function finds and returns the number of each label. The format is more
    focussed on showing the total amount of each label then the user label distribution,
    so the data is inverted from the function below. This is used by a graph on the
    front end admin page.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of the amount each label has been used
    """
    project = Project.objects.get(pk=project_pk)
    labels = [label for label in project.labels.all()]
    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    all_counts = []
    for u in users:
        temp_values = []
        for label in labels:
            label_count = DataLabel.objects.filter(profile=u, label=label).count()
            all_counts.append(label_count)
            temp_values.append({"x": label.name, "y": label_count})
        dataset.append({"key": u.__str__(), "values": temp_values})

    if not any(count > 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(["POST"])
@permission_classes((IsCoder,))
def skip_data(request, data_pk):
    """Take a datum that is in the assigneddata queue for that user and place it in the
    admin queue. Remove it from the assignedData queue.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    project = data.project
    response = {}

    # if the data is IRR or processed IRR, dont add to admin queue yet
    num_history = IRRLog.objects.filter(data=data).count()

    if RecycleBin.objects.filter(data=data).count() > 0:
        assignment = AssignedData.objects.get(data=data, profile=profile)
        assignment.delete()
    elif data.irr_ind or num_history > 0:
        # unassign the skipped item
        assignment = AssignedData.objects.get(data=data, profile=profile)
        assignment.delete()

        # log the data and check IRR but don't put in admin queue yet
        IRRLog.objects.create(
            data=data, profile=profile, label=None, timestamp=timezone.now()
        )
        # if the IRR history has more than the needed number of labels , it is
        # already processed so don't do anything else
        if num_history <= project.num_users_irr:
            process_irr_label(data, None)
    else:
        # the data is not IRR so treat it as normal
        move_skipped_to_admin_queue(data, profile, project)

    # for all data, check if we need to refill queue
    check_and_trigger_model(data, profile)

    return Response(response)


@api_view(["POST"])
@permission_classes((IsCoder,))
def annotate_data(request, data_pk):
    """Annotate a single datum which is in the assigneddata queue given the user,
    data_id, and label_id.  This will remove it from assigneddata, remove it from
    dataqueue and add it to labeleddata.  Also check if project is ready to have model
    run, if so start that process.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    project = data.project
    profile = request.user.profile
    response = {}
    label = Label.objects.get(pk=request.data["labelID"])
    labeling_time = request.data["labeling_time"]

    num_history = IRRLog.objects.filter(data=data).count()

    if RecycleBin.objects.filter(data=data).count() > 0:
        # this data is no longer in use. delete it
        assignment = AssignedData.objects.get(data=data, profile=profile)
        assignment.delete()
    elif num_history >= project.num_users_irr:
        # if the IRR history has more than the needed number of labels , it is
        # already processed so just add this label to the history.
        IRRLog.objects.create(
            data=data, profile=profile, label=label, timestamp=timezone.now()
        )
        assignment = AssignedData.objects.get(data=data, profile=profile)
        assignment.delete()
    else:
        label_data(label, data, profile, labeling_time)
        if data.irr_ind:
            # if it is reliability data, run processing step
            process_irr_label(data, label)

    # for all data, check if we need to refill queue
    check_and_trigger_model(data, profile)

    return Response(response)


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def discard_data(request, data_pk):
    """Move a datum to the RecycleBin. This removes it from the admin dataqueue. This is
    used only in the skew table by the admin.

    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    project = data.project
    response = {}

    # Make sure coder is an admin
    if project_extras.proj_permission_level(data.project, profile) > 1:
        # remove it from the admin queue
        queue = Queue.objects.get(project=project, type="admin")
        DataQueue.objects.get(data=data, queue=queue).delete()

        # update redis
        settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(data))

        IRRLog.objects.filter(data=data).delete()
        Data.objects.filter(pk=data_pk).update(irr_ind=False)
        RecycleBin.objects.create(data=data, timestamp=timezone.now())

        # remove any IRR log data
        irr_records = IRRLog.objects.filter(data=data)
        irr_records.delete()

    else:
        response["error"] = "Invalid credentials. Must be an admin."

    return Response(response)


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def restore_data(request, data_pk):
    """Move a datum out of the RecycleBin.
    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}

    # Make sure coder is an admin
    if project_extras.proj_permission_level(data.project, profile) > 1:
        # remove it from the recycle bin
        queue = Queue.objects.get(project=data.project, type="admin")
        DataQueue.objects.create(data=data, queue=queue)

        # update redis
        settings.REDIS.sadd(redis_serialize_set(queue), redis_serialize_data(data))

        RecycleBin.objects.get(data=data).delete()
    else:
        response["error"] = "Invalid credentials. Must be an admin."

    return Response(response)


@api_view(["POST"])
@permission_classes((IsCoder,))
def modify_label(request, data_pk):
    """Take a single datum with a label and change the label in the DataLabel table.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}
    project = data.project

    label = Label.objects.get(pk=request.data["labelID"])
    old_label = Label.objects.get(pk=request.data["oldLabelID"])
    with transaction.atomic():
        DataLabel.objects.filter(data=data, label=old_label).update(
            label=label, time_to_label=0, timestamp=timezone.now()
        )

        LabelChangeLog.objects.create(
            project=project,
            data=data,
            profile=profile,
            old_label=old_label.name,
            new_label=label.name,
            change_timestamp=timezone.now(),
        )

    return Response(response)


@api_view(["POST"])
@permission_classes((IsCoder,))
def modify_label_to_skip(request, data_pk):
    """Take a datum that is in the assigneddata queue for that user and place it in the
    admin queue. Remove it from the assignedData queue.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}
    project = data.project
    old_label = Label.objects.get(pk=request.data["oldLabelID"])
    queue = Queue.objects.get(project=project, type="admin")

    with transaction.atomic():
        DataLabel.objects.filter(data=data, label=old_label).delete()
        if data.irr_ind:
            # if it was irr, add it to the log
            if len(IRRLog.objects.filter(data=data, profile=profile)) == 0:
                IRRLog.objects.create(
                    data=data, profile=profile, label=None, timestamp=timezone.now()
                )
        else:
            # if it's not irr, add it to the admin queue immediately
            DataQueue.objects.create(data=data, queue=queue)

            # update redis
            settings.REDIS.sadd(redis_serialize_set(queue), redis_serialize_data(data))
        LabelChangeLog.objects.create(
            project=project,
            data=data,
            profile=profile,
            old_label=old_label.name,
            new_label="skip",
            change_timestamp=timezone.now(),
        )

    return Response(response)


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def check_admin_in_progress(request, project_pk):
    """This api is called by the admin tabs on the annotate page to check if it is
    alright to show the data."""
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # if nobody ELSE is there yet, return True
    if AdminProgress.objects.filter(project=project).count() == 0:
        return Response({"available": 1})
    if AdminProgress.objects.filter(project=project, profile=profile).count() == 0:
        return Response({"available": 0})
    else:
        return Response({"available": 1})


@api_view(["GET"])
def enter_coding_page(request, project_pk):
    """API request meant to be sent when a user navigates onto the coding page
       captured with 'beforeload' event.
    Args:
        request: The GET request
    Returns:
        {}
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)
    # check that no other admin is using it. If they are not, give this admin permission
    if project_extras.proj_permission_level(project, profile) > 1:
        if AdminProgress.objects.filter(project=project).count() == 0:
            AdminProgress.objects.create(
                project=project, profile=profile, timestamp=timezone.now()
            )
    return Response({})


@api_view(["GET"])
def leave_coding_page(request, project_pk):
    """API request meant to be sent when a user navigates away from the coding page
    captured with 'beforeunload' event.  This should use assign_data to remove any data
    currently assigned to the user and re-add it to redis.

    Args:
        request: The GET request
    Returns:
        {}
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)
    assigned_data = AssignedData.objects.filter(profile=profile)

    for assignment in assigned_data:
        unassign_datum(assignment.data, profile)

    if project_extras.proj_permission_level(project, profile) > 1:
        if AdminProgress.objects.filter(project=project, profile=profile).count() > 0:
            prog = AdminProgress.objects.get(project=project, profile=profile)
            prog.delete()
    return Response({})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def data_unlabeled_table(request, project_pk):
    """This returns the unlebeled data not in a queue for the skew table.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)

    stuff_in_queue = DataQueue.objects.filter(queue__project=project)
    queued_ids = [queued.data.id for queued in stuff_in_queue]

    recycle_ids = RecycleBin.objects.filter(data__project=project).values_list(
        "data__pk", flat=True
    )
    unlabeled_data = (
        project.data_set.filter(datalabel__isnull=True)
        .exclude(id__in=queued_ids)
        .exclude(id__in=recycle_ids)
    )
    data = []
    for d in unlabeled_data:
        serialized_data = DataSerializer(d, many=False).data
        temp = {
            "Text": serialized_data["text"],
            "metadata": serialized_data["metadata"],
            "ID": d.id,
        }
        data.append(temp)

    return Response({"data": data})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def data_admin_table(request, project_pk):
    """This returns the elements in the admin queue for annotation.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    queue = Queue.objects.get(project=project, type="admin")

    data_objs = DataQueue.objects.filter(queue=queue)

    data = []
    for d in data_objs:
        if d.data.irr_ind:
            reason = "IRR"
        else:
            reason = "Skipped"

        serialized_data = DataSerializer(d.data, many=False).data
        temp = {
            "Text": serialized_data["text"],
            "metadata": serialized_data["metadata"],
            "ID": d.data.id,
            "Reason": reason,
        }
        data.append(temp)

    return Response({"data": data})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def data_admin_counts(request, project_pk):
    """This returns the number of irr and admin objects.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    queue = Queue.objects.get(project=project, type="admin")
    data_objs = DataQueue.objects.filter(queue=queue)
    irr_count = data_objs.filter(data__irr_ind=True).count()
    skip_count = data_objs.filter(data__irr_ind=False).count()
    # only give both counts if both counts are relevent
    if project.percentage_irr == 0:
        return Response({"data": {"SKIP": skip_count}})
    else:
        return Response({"data": {"IRR": irr_count, "SKIP": skip_count}})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def recycle_bin_table(request, project_pk):
    """This returns the elements in the recycle bin.

    Args:
        request: The POST request
        pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    data_objs = RecycleBin.objects.filter(data__project=project)

    data = []
    for d in data_objs:
        serialized_data = DataSerializer(d.data, many=False).data
        temp = {
            "Text": serialized_data["text"],
            "metadata": serialized_data["metadata"],
            "ID": d.data.id,
        }
        data.append(temp)

    return Response({"data": data})


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def label_skew_label(request, data_pk):
    """This is called when an admin manually labels a datum on the skew page. It
    annotates a single datum with the given label, and profile with null as the time.

    Args:
        request: The request to the endpoint
        data_pk: Primary key of data
    Returns:
        {}
    """

    datum = Data.objects.get(pk=data_pk)
    project = datum.project
    label = Label.objects.get(pk=request.data["labelID"])
    profile = request.user.profile
    response = {}

    current_training_set = project.get_current_training_set()
    if project_extras.proj_permission_level(datum.project, profile) >= 2:
        with transaction.atomic():
            DataLabel.objects.create(
                data=datum,
                label=label,
                profile=profile,
                training_set=current_training_set,
                time_to_label=None,
                timestamp=timezone.now(),
            )
    else:
        response["error"] = "Invalid permission. Must be an admin."

    return Response(response)


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def label_admin_label(request, data_pk):
    """This is called when an admin manually labels a datum on the admin annotation
    page. It labels a single datum with the given label and profile, with null as the
    time.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    datum = Data.objects.get(pk=data_pk)
    project = datum.project
    label = Label.objects.get(pk=request.data["labelID"])
    profile = request.user.profile
    response = {}

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        queue = project.queue_set.get(type="admin")
        DataLabel.objects.create(
            data=datum,
            label=label,
            profile=profile,
            training_set=current_training_set,
            time_to_label=None,
            timestamp=timezone.now(),
        )

        DataQueue.objects.filter(data=datum, queue=queue).delete()

        # update redis
        settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))

        # make sure the data is no longer irr
        if datum.irr_ind:
            Data.objects.filter(pk=datum.pk).update(irr_ind=False)

    # NOTE: this checks if the model needs to be triggered, but not if the
    # queues need to be refilled. This is because for something to be in the
    # admin queue, annotate or skip would have already checked for an empty queue
    check_and_trigger_model(datum)
    return Response(response)


@api_view(["GET"])
@permission_classes((IsCoder,))
def get_label_history(request, project_pk):
    """Grab items previously labeled by this user and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
        data: DataLabel objects where that user was the one to label them
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    labels = Label.objects.all().filter(project=project)
    data = DataLabel.objects.filter(
        profile=profile, data__project=project_pk, label__in=labels
    )

    data_list = []
    results = []
    for d in data:
        # if it is not labeled irr but is in the log, the data is resolved IRR,
        if not d.data.irr_ind and len(IRRLog.objects.filter(data=d.data)) > 0:
            continue

        data_list.append(d.data.id)
        if d.timestamp:
            if d.timestamp.minute < 10:
                minute = "0" + str(d.timestamp.minute)
            else:
                minute = str(d.timestamp.minute)
            if d.timestamp.second < 10:
                second = "0" + str(d.timestamp.second)
            else:
                second = str(d.timestamp.second)
            new_timestamp = (
                str(d.timestamp.date())
                + ", "
                + str(d.timestamp.hour)
                + ":"
                + minute
                + "."
                + second
            )
        else:
            new_timestamp = "None"

        serialized_data = DataSerializer(d.data, many=False).data
        temp_dict = {
            "data": serialized_data["text"],
            "metadata": serialized_data["metadata"],
            "id": d.data.id,
            "label": d.label.name,
            "labelID": d.label.id,
            "timestamp": new_timestamp,
            "edit": "yes",
        }
        results.append(temp_dict)

    data_irr = IRRLog.objects.filter(
        profile=profile, data__project=project_pk, label__isnull=False
    )

    for d in data_irr:
        # if the data was labeled by that person (they were the admin), don't add
        # it twice
        if d.data.id in data_list:
            continue

        if d.timestamp:
            if d.timestamp.minute < 10:
                minute = "0" + str(d.timestamp.minute)
            else:
                minute = str(d.timestamp.minute)
            if d.timestamp.second < 10:
                second = "0" + str(d.timestamp.second)
            else:
                second = str(d.timestamp.second)
            new_timestamp = (
                str(d.timestamp.date())
                + ", "
                + str(d.timestamp.hour)
                + ":"
                + minute
                + "."
                + second
            )
        else:
            new_timestamp = "None"
        temp_dict = {
            "data": d.data.text,
            "id": d.data.id,
            "label": d.label.name,
            "labelID": d.label.id,
            "timestamp": new_timestamp,
            "edit": "no",
        }
        results.append(temp_dict)

    return Response({"data": results})
