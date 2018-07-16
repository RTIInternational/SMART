from django.shortcuts import render
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.db.models import Max, Min, FloatField
from django.db import connection
from django.contrib.postgres.fields import ArrayField
from django.utils.html import escape
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

import csv
import io
import os
import math
import random
import pandas as pd
from postgres_stats.aggregates import Percentile

from core.serializers import (ProfileSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer, ProjectSerializer,
                              CoreModelSerializer, LabelSerializer, DataSerializer,
                              DataLabelSerializer, DataPredictionSerializer,
                              QueueSerializer, AssignedDataSerializer)
from core.models import (Profile, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData, TrainingSet)
import core.util as util
from core.pagination import SmartPagination
from core.templatetags import project_extras


############################################
#        FRONTEND USER API ENDPOINTS       #
############################################
@api_view(['GET'])
def download_data(request, pk):
    data_objs = Data.objects.filter(project=pk)
    project_labels = Label.objects.filter(project=pk)
    data = []
    for label in project_labels:
        labeled_data = DataLabel.objects.filter(label=label)
        for d in labeled_data:
            temp = {}
            temp['Text'] = d.data.text
            temp['Label'] = label.name
            data.append(temp)

    buffer = io.StringIO()
    wr = csv.DictWriter(buffer, fieldnames=['Text', 'Label'], quoting=csv.QUOTE_ALL)
    wr.writeheader()
    wr.writerows(data)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;'

    return response

@api_view(['GET'])
def download_codebook(request, pk):
    """Given the project id, get the codebook file
    """
    project = Project.objects.get(pk=pk)
    fpath = os.path.join(settings.CODEBOOK_FILE_PATH, project.codebook_file)
    if os.path.isfile(fpath):
        with open(fpath,"rb") as file:
            codebook = file.read()
            response = HttpResponse(codebook, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment;'
            return response
    else:
        raise ValueError('There was no codebook for the project: ' + str(pk))

@api_view(['GET'])
def label_distribution_inverted(request, pk):
    project = Project.objects.get(pk=pk)

    labels = [l for l in project.labels.all()]

    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    all_counts = []
    for u in users:
        temp_data = {'key':u.__str__()}
        temp_values = []
        for l in labels:
            label_count = DataLabel.objects.filter(profile=u, label=l).count()
            all_counts.append(label_count)
            temp_values.append({'x':l.name, 'y':label_count})
        dataset.append({'key':u.__str__(), 'values':temp_values})


    if not any(count > 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(['GET'])
def label_distribution(request, pk):
    project = Project.objects.get(pk=pk)

    labels = [l for l in project.labels.all()]

    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    all_counts = []
    for l in labels:
        temp_data = {'key':l.name}
        temp_values = []
        for u in users:
            label_count = DataLabel.objects.filter(profile=u, label=l).count()
            all_counts.append(label_count)
            temp_values.append({'x':u.__str__(), 'y': label_count})
        dataset.append({'key':l.name, 'values': temp_values})

    if not any(count > 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(['GET'])
def label_timing(request, pk):
    project = Project.objects.get(pk=pk)

    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    yDomain = 0
    for u in users:
        result = DataLabel.objects.filter(data__project=pk, profile=u)\
                    .aggregate(quartiles=Percentile('time_to_label', [0.05, 0.25, 0.5, 0.75, 0.95],
                               continuous=False,
                               output_field=ArrayField(FloatField())))

        if result['quartiles']:
            if result['quartiles'][4] > yDomain:
                yDomain = result['quartiles'][4] + 10

            temp = {
                'label': u.__str__(),
                'values': {
                    'Q1': result['quartiles'][1],
                    'Q2': result['quartiles'][2],
                    'Q3': result['quartiles'][3],
                    'whisker_low': result['quartiles'][0],
                    'whisker_high': result['quartiles'][4]
                }
            }
            dataset.append(temp)

    return Response({'data': dataset, 'yDomain': yDomain})

@api_view(['GET'])
def model_metrics(request, pk):
    metric = request.GET.get('metric', 'accuracy')

    project = Project.objects.get(pk=pk)
    models = Model.objects.filter(project=project).order_by('training_set__set_number')

    if metric == 'accuracy':
        values = []
        for model in models:
            values.append({
                'x': model.training_set.set_number,
                'y': model.cv_accuracy
            })

        dataset = [
            {
                'key': 'Accuracy',
                'values': values
            }
        ]
    else:
        labels = {str(label.pk): label.name for label in  project.labels.all()}
        dataset = []
        for label in labels:
            values = []
            for model in models:
                current_metric = model.cv_metrics[metric][label]
                values.append({
                    'x':  model.training_set.set_number,
                    'y': current_metric
                  })
            dataset.append({
                'key': labels[label],
                'values': values
            })

    return Response(dataset)



@api_view(['GET'])
def data_coded_table(request, pk):
    project = Project.objects.get(pk=pk)

    data_objs = DataLabel.objects.filter(data__project=project)

    data = []
    for d in data_objs:
        temp = {
            'Text': escape(d.data.text),
            'Label': d.label.name,
            'Coder': d.profile.__str__()
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
def data_predicted_table(request, pk):
    project = Project.objects.get(pk=pk)
    previous_run = project.get_current_training_set().set_number - 1

    sql = """
    SELECT d.{data_text_col}, l.{label_name_col}, dp.{pred_prob_col}
    FROM (
        SELECT {pred_data_id_col}, MAX({pred_prob_col}) AS max_prob
        FROM {pred_table}
        GROUP BY {pred_data_id_col}
        ) as tmp
    LEFT JOIN {pred_table} as dp
    ON dp.{pred_data_id_col} = tmp.{pred_data_id_col} AND dp.{pred_prob_col} = tmp.max_prob
    LEFT JOIN {label_table} as l
    ON l.{label_pk_col} = dp.{pred_label_id_col}
    LEFT JOIN {data_table} as d
    ON d.{data_pk_col} = dp.{pred_data_id_col}
    LEFT JOIN {model_table} as m
    ON m.{model_pk_col} = dp.{pred_model_id_col}
    LEFT JOIN {trainingset_table} as ts
    ON ts.{trainingset_pk_col} = m.{model_trainingset_id_col}
    WHERE ts.{trainingset_setnumber_col} = {previous_run} AND d.{data_project_id_col} = {project_pk}
    """.format(
            data_text_col=Data._meta.get_field('text').column,
            label_name_col=Label._meta.get_field('name').column,
            pred_prob_col=DataPrediction._meta.get_field('predicted_probability').column,
            pred_data_id_col=DataPrediction._meta.get_field('data').column,
            pred_table=DataPrediction._meta.db_table,
            label_table=Label._meta.db_table,
            label_pk_col=Label._meta.pk.name,
            pred_label_id_col=DataPrediction._meta.get_field('label').column,
            data_table=Data._meta.db_table,
            data_pk_col=Data._meta.pk.name,
            model_table=Model._meta.db_table,
            model_pk_col=Model._meta.pk.name,
            pred_model_id_col=DataPrediction._meta.get_field('model').column,
            trainingset_table=TrainingSet._meta.db_table,
            trainingset_pk_col=TrainingSet._meta.pk.name,
            model_trainingset_id_col=Model._meta.get_field('training_set').column,
            trainingset_setnumber_col=TrainingSet._meta.get_field('set_number').column,
            previous_run=previous_run,
            data_project_id_col=Data._meta.get_field('project').column,
            project_pk=project.pk)

    with connection.cursor() as c:
        result = c.execute(sql)
        data_objs = c.fetchall()

    data = []
    for d in data_objs:
        temp = {
            'Text': escape(d[0]),
            'Label': d[1],
            'Probability': d[2]
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
def data_unlabeled_table(request, pk):
    project = Project.objects.get(pk=pk)

    stuff_in_queue = DataQueue.objects.filter(queue__project=project)
    queued_ids = [queued.data.id for queued in stuff_in_queue]

    unlabeled_data = project.data_set.filter(datalabel__isnull=True).exclude(id__in=queued_ids)
    data = []
    for d in unlabeled_data:
        temp = {
            'Text': escape(d.text),
            'ID':d.id
        }
        data.append(temp)

    return Response({'data': data})

@api_view(['GET'])
def data_admin_table(request, pk):
    project = Project.objects.get(pk=pk)
    queue = Queue.objects.filter(project=project,admin=True)

    data_objs = DataQueue.objects.filter(queue=queue)

    data = []
    for d in data_objs:
        temp = {
            'Text': d.data.text,
            'ID': d.data.id
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
def get_labels(request, pk):
    project = Project.objects.get(pk=pk)
    labels = Label.objects.filter(project=project)
    return Response({'labels': LabelSerializer(labels, many=True).data})


@api_view(['POST'])
def label_skew_label(request, pk):
    '''This is called when an admin manually labels a datum on the skew page. It
    annotates a single datum with the given label, and profile with null as the time.
    '''
    datum = Data.objects.get(pk=pk)
    project = datum.project
    label = Label.objects.get(pk=request.data['labelID'])
    profile = request.user.profile

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set,
                                time_to_label=None
                                )

    return Response({'test':'success'})

@api_view(['POST'])
def label_admin_label(request, pk):
    '''This is called when an admin manually labels a datum on the admin
    annotation page. It labels a single datum with the given label and profile,
    with null as the time.
    It also removes the data from the admin queue.
    '''
    datum = Data.objects.get(pk=pk)
    project = datum.project
    label = Label.objects.get(pk=request.data['labelID'])
    profile = request.user.profile

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        queue = project.queue_set.get(admin=True)
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set,
                                time_to_label=None
                                )

        DataQueue.objects.filter(data=datum, queue=queue).delete()

    util.check_and_trigger_model(datum)
    return Response({'test':'success'})


############################################
#    REACT API ENDPOINTS FOR CODING VIEW   #
############################################

@api_view(['GET'])
def get_card_deck(request, pk):
    """Grab data using get_assignments and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        pk: Primary key of project
    Returns:
        labels: The project labels
        data: The data in the queue
    """
    profile = request.user.profile
    project = Project.objects.get(pk=pk)

    # Calculate queue parameters
    batch_size = project.batch_size
    num_coders = len(project.projectpermissions_set.all()) + 1
    coder_size = math.ceil(batch_size / num_coders)

    data = util.get_assignments(profile, project, coder_size)
    labels = Label.objects.all().filter(project=project)

    return Response({'labels': LabelSerializer(labels, many=True).data, 'data': DataSerializer(data, many=True).data})

@api_view(['POST'])
def skip_data(request, pk):
    """Take a datum that is in the assigneddata queue for that user
    and place it in the admin queue. Remove it from the
    assignedData queue.

    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=pk)
    profile = request.user.profile
    project = data.project
    queue = project.queue_set.get(admin=False)
    response = {}

    # Make sure coder still has permissions before labeling data
    if project_extras.proj_permission_level(project, profile) > 0:
        util.move_skipped_to_admin_queue(data, profile, project)
    else:
        response['error'] = 'Account disabled by administrator.  Please contact project owner for details'

    util.fill_queue(queue,project.learning_method)
    return Response(response)

@api_view(['POST'])
def annotate_data(request, pk):
    """Annotate a single datum which is in the assigneddata queue given the user,
       data_id, and label_id.  This will remove it from assigneddata, remove it
       from dataqueue and add it to labeleddata.  Also check if project is ready
       to have model run, if so start that process.

    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=pk)
    profile = request.user.profile
    response = {}

    # Make sure coder still has permissions before labeling data
    if project_extras.proj_permission_level(data.project, profile) > 0:
        label = Label.objects.get(pk=request.data['labelID'])
        labeling_time = request.data['labeling_time']
        util.label_data(label, data, profile, labeling_time)

        util.check_and_trigger_model(data)
    else:
        response['error'] = 'Account disabled by administrator.  Please contact project owner for details'

    return Response(response)


@api_view(['GET'])
def leave_coding_page(request):
    """API request meant to be sent when a user navigates away from the coding page
       captured with 'beforeunload' event.  This should use assign_data to remove
       any data currently assigned to the user and re-add it to redis

    Args:
        request: The GET request
    Returns:
        {}
    """
    profile = request.user.profile
    assigned_data = AssignedData.objects.filter(profile=profile)

    for assignment in assigned_data:
        util.unassign_datum(assignment.data, profile)

    return Response({})


################################
#    DRF VIEWSET API CLASSES   #
################################

# TODO establish more restrictive permissions
# AuthUsers should be write-only for unauthenticated users
# Creation/update/deletion of certain objects that will be
# managed by the server probably shouldn't be exposed via the API
# (ex. Queues, Models, AssignedData, many-to-many join fields)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().order_by('id')
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AuthUserGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = AuthUserGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AuthUserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.all().order_by('id')
    serializer_class = AuthUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated,)

class CoreModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all().order_by('id')
    serializer_class = CoreModelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all().order_by('id')
    serializer_class = DataSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SmartPagination

class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all().order_by('id')
    serializer_class = LabelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataLabelViewSet(viewsets.ModelViewSet):
    queryset = DataLabel.objects.all().order_by('id')
    serializer_class = DataLabelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataPredictionViewSet(viewsets.ModelViewSet):
    queryset = DataPrediction.objects.all().order_by('id')
    serializer_class = DataPredictionSerializer
    permission_classes = (permissions.IsAuthenticated,)

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all().order_by('id')
    serializer_class = QueueSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AssignedDataViewSet(viewsets.ModelViewSet):
    queryset = AssignedData.objects.all().order_by('id')
    serializer_class = AssignedDataSerializer
    permission_classes = (permissions.IsAuthenticated,)
