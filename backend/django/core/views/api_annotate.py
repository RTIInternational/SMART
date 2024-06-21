import math
import random

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from psycopg2.errors import UniqueViolation
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from sentence_transformers import SentenceTransformer, util

from core.models import (
    AdjudicateDescription,
    AdminProgress,
    AssignedData,
    Data,
    DataLabel,
    DataQueue,
    IRRLog,
    Label,
    LabelChangeLog,
    LabelEmbeddings,
    MetaData,
    MetaDataField,
    Project,
    Queue,
    RecycleBin,
    VerifiedDataLabel,
)
from core.pagination import LabelViewPagination
from core.permissions import IsAdminOrCreator, IsCoder
from core.serializers import (
    DataLabelModelSerializer,
    DataMetadataIDSerializer,
    DataSerializer,
    IRRLogModelSerializer,
    LabelSerializer,
)
from core.templatetags import project_extras
from core.utils.utils_annotate import (
    cache_embeddings,
    createUnresolvedAdjudicateMessage,
    get_assignments,
    get_embeddings,
    get_unlabeled_data,
    label_data,
    leave_coding_page,
    move_skipped_to_admin_queue,
    process_irr_label,
    update_last_action,
)
from core.utils.utils_model import check_and_trigger_model
from core.utils.utils_queue import fill_queue
from core.utils.utils_redis import redis_serialize_data, redis_serialize_set
from smart.settings import ADMIN_TIMEOUT_MINUTES

# Using a prebuilt model
# How this model was built: https://github.com/dsteedRTI/csv-to-embeddings-model
# Sbert Model can be found here: https://www.sbert.net/docs/pretrained_models.html
# Sbert Model Card: https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1
model_path = "core/smart_embeddings_model"
embeddings_model = SentenceTransformer(model_path)


@permission_classes((IsCoder,))
class SearchLabelsView(ListAPIView):
    serializer_class = LabelSerializer
    pagination_class = LabelViewPagination

    def get_queryset(self):
        """This view should return a list of all the labels which contain a particular
        string."""
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        filter_text = self.request.GET.get("searchString")

        return Label.objects.filter(project=project).filter(
            Q(name__icontains=filter_text) | Q(description__icontains=filter_text)
        )


@api_view(["GET"])
@permission_classes((IsCoder,))
def get_labels(request, project_pk):
    """Get the set of labels in the project.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
    """
    project = Project.objects.get(pk=project_pk)
    labels = Label.objects.all().filter(project=project)

    # If the number of labels is > 100, just return the first 100
    serialized_labels = LabelSerializer(labels, many=True).data
    if len(serialized_labels) > 100:
        serialized_labels = serialized_labels[:100]

    return Response(
        {
            "labels": serialized_labels,
        }
    )


@api_view(["GET"])
@permission_classes((IsCoder,))
def get_card_deck(request, project_pk):
    """Grab data using get_assignments and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        data: The data in the queue
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # Calculate queue parameters
    data = get_assignments(profile, project, project.batch_size)
    if len(data) == 0:
        if project.queue_set.filter(type="irr").exists():
            irr_queue = project.queue_set.get(type="irr")
        else:
            irr_queue = None
        fill_queue(
            queue=project.queue_set.get(type="normal"),
            orderby=project.learning_method,
            irr_queue=irr_queue,
            batch_size=project.batch_size,
            irr_percent=project.percentage_irr,
        )
        data = get_assignments(profile, project, project.batch_size)

    # shuffle so the irr is not all at the front
    random.shuffle(data)

    return Response(
        {
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
    labels = list(project.labels.all())
    users = [
        project.creator,
        *[perm.profile for perm in project.projectpermissions_set.all()],
    ]
    dataset = []
    all_counts = []
    for u in users:
        temp_values = []
        for label in labels:
            label_count = DataLabel.objects.filter(profile=u, label=label).count()
            all_counts.append(label_count)
            temp_values.append({"x": label.name, "y": label_count})
        dataset.append({"key": u.__str__(), "values": temp_values})

    if all(count <= 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(["POST"])
@permission_classes((IsCoder,))
def unassign_data(request, data_pk):
    """Take a datum that is in the assigneddata queue for that user and remove it from
    the assignedData queue.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}
    if AssignedData.objects.filter(data=data, profile=profile).exists():
        assignment = AssignedData.objects.get(data=data, profile=profile)
        assignment.delete()

    return Response(response)


@api_view(["POST"])
@permission_classes((IsCoder,))
def verify_label(request, data_pk):
    """Take a data label that was not verified, and verify it.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    response = {}
    # if the coder has been un-assigned from the data
    if not DataLabel.objects.filter(data=data).exists():
        response["error"] = (
            "ERROR: This data has no label to verify. Something must have gone wrong."
        )
        return Response(response)
    elif DataLabel.objects.filter(data=data).count() > 1:
        response["error"] = (
            "ERROR: This data has multiple labels. This shouldn't "
            "be possible with unverified data as it is pre-labeled."
        )
    else:
        VerifiedDataLabel.objects.create(
            data_label=DataLabel.objects.get(data=data),
            verified_timestamp=timezone.now(),
            verified_by=request.user.profile,
        )

    return Response(response)


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

    # if the coder has been un-assigned from the data
    if not AssignedData.objects.filter(data=data, profile=profile).exists():
        response["error"] = (
            "ERROR: Your cards were un-assigned by an administrator. "
            "Please refresh the page to get new assigned items to annotate."
        )
        return Response(response)

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
        createUnresolvedAdjudicateMessage(project, data, request.data["message"])

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

    # if the coder has been un-assigned from the data
    if (
        not AssignedData.objects.filter(data=data, profile=profile).exists()
    ) or DataLabel.objects.filter(data=data, profile=profile).exists():
        response["error"] = (
            "ERROR: this card was no longer assigned. Either "
            "your cards were un-assigned by an administrator or the label was clicked twice. "
            "Please refresh the page to get new assigned items to annotate."
        )
        return Response(response)

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
        try:
            label_data(label, data, profile, labeling_time)
            if data.irr_ind:
                # if it is reliability data, run processing step
                process_irr_label(data, label)
        except UniqueViolation:
            response["error"] = (
                "ERROR: this card was no longer assigned. Either "
                "your cards were un-assigned by an administrator or the label was clicked twice. "
                "Please refresh the page to get new assigned items to annotate."
            )
            return Response(response)

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

    # check if they have the admin lock still.
    # If they don't, then they can't complete the action
    if not AdminProgress.objects.filter(project=project, profile=profile).exists():
        response["error"] = (
            "ERROR: Your access timed out due to inactivity."
            " Another admin is currently using this page."
            " This page will become available when the admin returns to the "
            "project list page, details page, changes projects, or logs out."
        )
        return Response(response)

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

        # set any adjudication message to resolved
        AdjudicateDescription.objects.filter(data_id=data_pk).update(isResolved=True)

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
    project = data.project
    update_last_action(project, profile)
    response = {}

    if not AdminProgress.objects.filter(project=project, profile=profile).exists():
        response["error"] = (
            "ERROR: Your access timed out due to inactivity."
            " Another admin is currently using this page."
            " This page will become available when the admin returns to the "
            "project list page, details page, changes projects, or logs out."
        )
        return Response(response)

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
    normal_queue = Queue.objects.get(project=project, type="normal")

    label = Label.objects.get(pk=request.data["labelID"])

    if (
        not request.data.get("oldLabelID")
        and not DataLabel.objects.filter(data=data).exists()
    ):
        current_training_set = project.get_current_training_set()
        data_in_normal_queue = DataQueue.objects.filter(
            data=data, queue=normal_queue
        ).exists()
        with transaction.atomic():
            DataLabel.objects.create(
                data=data,
                label=label,
                time_to_label=0,
                timestamp=timezone.now(),
                profile=profile,
                training_set=current_training_set,
                pre_loaded=False,
            )
            if data_in_normal_queue:
                DataQueue.objects.get(data=data, queue=normal_queue).delete()

        if data_in_normal_queue:
            settings.REDIS.srem(
                redis_serialize_set(normal_queue), redis_serialize_data(data)
            )

    elif "oldLabelID" in request.data:
        old_label = Label.objects.get(pk=request.data["oldLabelID"])
        with transaction.atomic():
            DataLabel.objects.filter(data=data, label=old_label).update(
                label=label,
                time_to_label=0,
                timestamp=timezone.now(),
                profile=profile,
                pre_loaded=False,
            )

            LabelChangeLog.objects.create(
                project=project,
                data=data,
                profile=profile,
                old_label=old_label.name,
                new_label=label.name,
                change_timestamp=timezone.now(),
            )
    # if there is no previous label but there is a datalabel it's probably a double click so do nothing

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

    queue = Queue.objects.get(project=project, type="admin")
    createUnresolvedAdjudicateMessage(project, data, request.data["message"])

    with transaction.atomic():
        if not request.data.get("oldLabelID"):
            # since it wasn't labeled, it isn't IRR and we don't need to change a label
            DataQueue.objects.create(data=data, queue=queue)
            # update redis
            settings.REDIS.sadd(redis_serialize_set(queue), redis_serialize_data(data))
        else:
            old_label = Label.objects.get(pk=request.data["oldLabelID"])
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
                settings.REDIS.sadd(
                    redis_serialize_set(queue), redis_serialize_data(data)
                )
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
        else:
            # figure out the time from the last time the other admin used the page
            previous_admin_progress = AdminProgress.objects.filter(project=project)
            if previous_admin_progress[0].profile != profile:
                time_since_previous_admin = (
                    timezone.now() - previous_admin_progress[0].last_action
                )
                if time_since_previous_admin.seconds / 60 > ADMIN_TIMEOUT_MINUTES:
                    previous_admin_progress.delete()
                    AdminProgress.objects.create(
                        project=project, profile=profile, timestamp=timezone.now()
                    )

    # NEW leave the coding page for all other projects so they're only in one
    # project at a time
    profile_projects = Project.objects.filter(
        Q(creator=profile) | Q(projectpermissions__profile=profile)
    ).distinct()

    profile_projects = [p for p in profile_projects if p != project]
    for project in profile_projects:
        leave_coding_page(profile, project)

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
    unlabeled_data = get_unlabeled_data(project_pk)[:50]
    serialized_data = DataSerializer(unlabeled_data, many=True).data
    data = [
        {"Text": d["text"], "metadata": d["metadata"], "ID": d["pk"]}
        for d in serialized_data
    ]
    return Response({"data": data})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def search_data_unlabeled_table(request, project_pk):
    """This returns the unlabeled data not in a queue for the skew table filtered for a
    search input.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a filtered list of data information
    """
    project = Project.objects.get(pk=project_pk)
    profile = request.user.profile
    update_last_action(project, profile)
    unlabeled_data = get_unlabeled_data(project_pk)
    text = request.GET.get("text")
    unlabeled_data = unlabeled_data.filter(text__icontains=text.lower())
    serialized_data = DataSerializer(unlabeled_data, many=True).data
    data = [
        {
            "data": d["text"],
            "metadata": d["metadata"],
            "id": d["pk"],
            "project": project_pk,
        }
        for d in serialized_data
    ]
    return Response({"data": data[:50]})


@api_view(["POST"])
@permission_classes([AllowAny])
def embeddings_calculations(request):
    """This calculates embeddings for a given array of strings.

    Args:
        strings: The array of strings
        request: The POST request
    Returns:
        data: a list of data information
    """

    embeddings = embeddings_model.encode(request.data["strings"])

    return Response(embeddings)


@api_view(["GET"])
@permission_classes((IsCoder,))
def embeddings_comparison(request, project_pk):
    """This finds the highest scoring labels when comparing cosine similarity scores of
    their embeddingsfor a given input string.

    Args:
        text: The input string
        request: The GET request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    project_labels = Label.objects.filter(project=project)

    # Request and cache label embeddings
    cached_embeddings = get_embeddings(project_pk)
    if cached_embeddings:
        project_labels_embeddings = cached_embeddings
    else:
        project_labels_embeddings = list(
            LabelEmbeddings.objects.filter(label_id__in=project_labels).values_list(
                "embedding", flat=True
            )
        )
        cache_embeddings(project_pk, project_labels_embeddings)

    text = request.GET.get("text")
    text_embedding = embeddings_model.encode(text)

    cosine_scores = util.pytorch_cos_sim(text_embedding, project_labels_embeddings)
    values, indices = cosine_scores[0].topk(5)

    suggestions = []
    for index in indices:
        suggestions.append(LabelSerializer(project_labels[int(index)]).data)

    return Response({"suggestions": suggestions})


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
    profile = request.user.profile
    update_last_action(project, profile)
    queue = Queue.objects.get(project=project, type="admin")

    messages = list(
        AdjudicateDescription.objects.filter(
            project_id=project_pk, isResolved=False
        ).values("data_id", "message")
    )

    data_objs = DataQueue.objects.filter(queue=queue)

    data = []
    for d in data_objs:
        if d.data.irr_ind:
            reason = "IRR"
        else:
            reason = "Skipped"

        serialized_data = DataSerializer(d.data, many=False).data
        potentialMessage = [x for x in messages if x["data_id"] == d.data.id]
        temp = {
            "Text": serialized_data["text"],
            "metadata": serialized_data["metadata"],
            "ID": d.data.id,
            "Reason": reason,
            "message": None if not potentialMessage else potentialMessage[0]["message"],
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
    profile = request.user.profile
    update_last_action(project, profile)
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
    update_last_action(project, profile)
    normal_queue = Queue.objects.get(project=project, type="normal")
    response = {}

    # check if they have the admin lock still.
    # If they don't, then they can't complete the action
    if not AdminProgress.objects.filter(project=project, profile=profile).exists():
        response["error"] = (
            "ERROR: Your access timed out due to inactivity."
            " Another admin is currently using this page."
            " This page will become available when the admin returns to the "
            "project list page, details page, changes projects, or logs out."
        )
        return Response(response)

    current_training_set = project.get_current_training_set()
    if project_extras.proj_permission_level(datum.project, profile) >= 2:
        data_in_normal_queue = DataQueue.objects.filter(
            data=datum, queue=normal_queue
        ).exists()
        with transaction.atomic():
            dl = DataLabel.objects.create(
                data=datum,
                label=label,
                profile=profile,
                training_set=current_training_set,
                time_to_label=None,
                timestamp=timezone.now(),
            )
            if data_in_normal_queue:
                DataQueue.objects.get(data=datum, queue=normal_queue).delete()
            VerifiedDataLabel.objects.create(
                data_label=dl, verified_timestamp=timezone.now(), verified_by=profile
            )
        if data_in_normal_queue:
            settings.REDIS.srem(
                redis_serialize_set(normal_queue), redis_serialize_data(datum)
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
    update_last_action(project, profile)
    response = {}

    # check if they have the admin lock still.
    # If they don't, then they can't complete the action
    if not AdminProgress.objects.filter(project=project, profile=profile).exists():
        response["error"] = (
            "ERROR: Your access timed out due to inactivity."
            " Another admin is currently using this page."
            " This page will become available when the admin returns to the "
            "project list page, details page, changes projects, or logs out."
        )
        return Response(response)

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        queue = project.queue_set.get(type="admin")
        dl = DataLabel.objects.create(
            data=datum,
            label=label,
            profile=profile,
            training_set=current_training_set,
            time_to_label=None,
            timestamp=timezone.now(),
        )
        VerifiedDataLabel.objects.create(
            data_label=dl, verified_timestamp=timezone.now(), verified_by=profile
        )

        DataQueue.objects.filter(data=datum, queue=queue).delete()

        # update redis
        settings.REDIS.srem(redis_serialize_set(queue), redis_serialize_data(datum))

        # make sure the data is no longer irr
        if datum.irr_ind:
            Data.objects.filter(pk=datum.pk).update(irr_ind=False)

        AdjudicateDescription.objects.filter(data_id=data_pk).update(isResolved=True)

    # NOTE: this checks if the model needs to be triggered, but not if the
    # queues need to be refilled. This is because for something to be in the
    # admin queue, annotate or skip would have already checked for an empty queue
    check_and_trigger_model(datum)
    return Response(response)


@api_view(["GET"])
@permission_classes((IsCoder,))
def get_label_history(request, project_pk):
    """Grab items previously labeled by this user and send it to the frontend react app.
    If this user is the project creator or an admin, get all items previously labeled.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
        data: DataLabel objects where that user was the one to label them
        unlabeled: DataLabel objects without a label
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    labels = Label.objects.all().filter(project=project)
    # irr data gets set to not IRR once it's finalized
    finalized_irr_data = IRRLog.objects.filter(data__irr_ind=False).values_list(
        "data__pk", flat=True
    )
    if (
        project_extras.proj_permission_level(project, profile) >= 2
        or project.allow_coders_view_labels
    ):
        labeled_data = DataLabel.objects.filter(
            data__project=project_pk, label__in=labels
        ).exclude(data__in=finalized_irr_data)
    else:
        labeled_data = DataLabel.objects.filter(
            profile=profile, data__project=project_pk, label__in=labels
        ).exclude(data__in=finalized_irr_data)

    labeled_data_list = list(labeled_data.values_list("data__pk", flat=True))

    # even for an admin, we only get personal IRR data
    personal_irr_data = IRRLog.objects.filter(
        profile=profile, data__project=project_pk, label__isnull=False
    ).exclude(data__pk__in=labeled_data_list)
    irr_data_list = list(personal_irr_data.values_list("data__pk", flat=True))

    # add the unlabeled data if selected
    total_data_list = labeled_data_list + irr_data_list
    if request.GET.get("unlabeled") == "true":
        unlabeled_data = list(
            get_unlabeled_data(project_pk).values_list("pk", flat=True)
        )
        total_data_list += unlabeled_data

    # return the page indicated in the query, get total pages
    current_page = request.GET.get("page")
    if current_page is None:
        current_page = 1
    page = int(current_page) - 1

    page_size = 100
    all_data = Data.objects.filter(pk__in=total_data_list).order_by("text")
    metadata_objects = MetaDataField.objects.filter(project=project)

    # filter the results by the search terms
    text_filter = request.GET.get("Text")
    if text_filter is not None and text_filter != "":
        all_data = all_data.filter(text__icontains=text_filter)

    for m in metadata_objects:
        m_filter = request.GET.get(str(m))
        if m_filter is not None and m_filter != "":
            data_with_metadata_filter = MetaData.objects.filter(
                metadata_field=m, value__icontains=m_filter
            ).values_list("data__pk", flat=True)
            all_data = all_data.filter(pk__in=data_with_metadata_filter)

    total_pages = math.ceil(len(all_data) / page_size)

    page_data = all_data[page * page_size : min((page + 1) * page_size, len(all_data))]
    # get the metadata IDs needed for metadata editing
    page_data_metadata_ids = [
        d["metadata"] for d in DataMetadataIDSerializer(page_data, many=True).data
    ]

    page_data = DataSerializer(page_data, many=True).data

    # derive the metadata fields in the forms needed for the table
    all_metadata = [c.popitem("metadata")[1] for c in page_data]
    all_metadata_formatted = [
        {c.split(":")[0].replace(" ", "_"): c.split(":")[1] for c in inner_list}
        for inner_list in all_metadata
    ]

    data_df = pd.DataFrame(page_data).rename(columns={"pk": "id", "text": "data"})
    if len(data_df) == 0:
        return Response(
            {
                "data": [],
                "total_pages": 1,
                "metadata_fields": [str(field) for field in metadata_objects],
            }
        )

    # get the labeled data into the correct format for returning
    label_dict = {label.pk: label.name for label in labels}
    labeled_data_df = pd.DataFrame(
        DataLabelModelSerializer(
            labeled_data.filter(data__pk__in=data_df["id"].tolist()), many=True
        ).data
    ).rename(columns={"data": "id", "label": "labelID", "verified": "verified_by"})

    irr_data_df = pd.DataFrame(
        IRRLogModelSerializer(
            personal_irr_data.filter(data__pk__in=data_df["id"].tolist()), many=True
        ).data
    ).rename(columns={"data": "id", "label": "labelID"})

    if len(labeled_data_df) > 0:
        labeled_data_df["verified"] = labeled_data_df["verified_by"].apply(
            lambda x: "No" if x is None else "Yes"
        )
        labeled_data_df["pre_loaded"] = labeled_data_df["pre_loaded"].apply(
            lambda x: "Yes" if x else "No"
        )
        labeled_data_df["edit"] = "yes"
        labeled_data_df["label"] = labeled_data_df["labelID"].apply(
            lambda x: label_dict[x]
        )

    if len(irr_data_df) > 0:
        irr_data_df["edit"] = "no"
        irr_data_df["label"] = irr_data_df["labelID"].apply(lambda x: label_dict[x])
        irr_data_df["verified"] = (
            "N/A (IRR)"  # Technically resolved IRR is verified but perhaps not this user's specific label so just NA
        )
        irr_data_df["verified_by"] = None
        irr_data_df["pre_loaded"] = "No"  # IRR only looks at unlabeled data

    all_labeled_stuff = pd.concat([labeled_data_df, irr_data_df], axis=0).reset_index(
        drop=True
    )

    # merge the data info with the label info
    if len(all_labeled_stuff) > 0:
        data_df = data_df.merge(all_labeled_stuff, on=["id"], how="left")
        data_df["edit"] = data_df["edit"].fillna("yes")
    else:
        data_df["edit"] = "yes"
        data_df["label"] = ""
        data_df["profile"] = ""
        data_df["timestamp"] = ""
        data_df["verified"] = ""
        data_df["verified_by"] = ""
        data_df["pre_loaded"] = ""

    # TODO: annotate uses pk while everything else uses ID. Let's fix this
    data_df["pk"] = data_df["id"]

    # now add back on the metadata fields
    results = data_df.fillna("").to_dict(orient="records")
    for i in range(len(results)):
        results[i]["metadata"] = all_metadata[i]
        results[i]["formattedMetadata"] = all_metadata_formatted[i]
        results[i]["metadataIDs"] = page_data_metadata_ids[i]

    return Response(
        {
            "data": results,
            "total_pages": total_pages,
            "metadata_fields": [str(field) for field in metadata_objects],
        }
    )


@api_view(["POST"])
# @permission_classes((IsCoder,))
def modify_metadata_values(request, data_pk):
    """Update metadata values.

    Args:
        request: The POST request
        data_pk: Primary key of the data
        metadatas: {
            key: Metadata field_name,
            value: New value
        }
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    metadata = MetaData.objects.filter(data_id=data.id)
    metadatas = request.data["metadatas"]
    for m in metadatas:
        metadata = MetaData.objects.get(data_id=data.id, value=m["previous"])
        metadata.value = m["value"]
        metadata.save()
    return Response({})
