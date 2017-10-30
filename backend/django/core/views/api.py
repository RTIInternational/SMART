from django.shortcuts import render
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.db.models import Max
from django.db import connection
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

import csv
import io
import math
import random
import pandas as pd

from core.serializers import (ProfileSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer, ProjectSerializer,
                              CoreModelSerializer, LabelSerializer, DataSerializer,
                              DataLabelSerializer, DataPredictionSerializer,
                              QueueSerializer, AssignedDataSerializer)
from core.models import (Profile, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData, TrainingSet)
import core.util as util
from core.pagination import SmartPagination


############################################
#        FRONTEND USER API ENDPOINTS       #
############################################
@api_view(['GET'])
def download_data(request, pk):
    data_objs = Data.objects.filter(project=pk)

    data = []
    for d in data_objs:
        temp = {}
        temp['text'] = d.text

        if d.datalabel_set.count() >= 1:
            label = d.datalabel_set.first().label.name
        elif d.dataprediction_set.count() >= 1:
            newest_model = Model.objects.filter(project=pk).order_by('-pk')[0]
            label = d.dataprediction_set.filter(model=newest_model).order_by('-predicted_probability')[0].predicted_class
        else:
            label = None

        temp['label'] = label

        data.append(temp)

    buffer = io.StringIO()
    wr = csv.DictWriter(buffer, fieldnames=['text', 'label'], quoting=csv.QUOTE_ALL)
    wr.writerows(data)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;'

    return response


@api_view(['GET'])
def label_distribution(request, pk):
    project = Project.objects.get(pk=pk)

    labels = [l for l in project.labels.all()]

    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    datasets = []
    for l in labels:
        temp_data = []
        for u in users:
            temp_data.append(DataLabel.objects.filter(profile=u, label=l).count())
        datasets.append({'label':l.name, 'data':temp_data})

    chart_data = {
        'labels': [u.__str__() for u in users],
        'datasets': [ds for ds in datasets]
    }

    return Response(chart_data)


@api_view(['GET'])
def data_coded_table(request, pk):
    project = Project.objects.get(pk=pk)

    data_objs = DataLabel.objects.filter(data__project=project)

    data = []
    for d in data_objs:
        temp = {
            'Text': d.data.text,
            'Label': d.label.name,
            'Coder': d.profile.__str__()
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
def data_predicted_table(request, pk):
    project = Project.objects.get(pk=pk)
    previous_run = project.get_current_training_set().set_number - 1
    print(previous_run)

    sql = """
    SELECT d.{data_text_col}, l.{label_name_col}, dp.{pred_prob_col}
    FROM (
        SELECT {pred_data_id_col}, MAX({pred_prob_col}) AS max_prob
        FROM {pred_table}
        GROUP BY {pred_data_id_col}
        ) as tmp
    JOIN {pred_table} as dp
    ON dp.{pred_data_id_col} = tmp.{pred_data_id_col} AND dp.{pred_prob_col} = tmp.max_prob
    JOIN {label_table} as l
    ON l.{label_pk_col} = dp.{pred_label_id_col}
    JOIN {data_table} as d
    ON d.{data_pk_col} = dp.{pred_data_id_col}
    JOIN {model_table} as m
    ON m.{model_pk_col} = dp.{pred_model_id_col}
    JOIN {trainingset_table} as ts
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
            'Text': d[0],
            'Label': d[1],
            'Probability': d[2]
        }
        data.append(temp)

    return Response({'data': data})


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
    batch_size = len(project.labels.all()) * 10
    num_coders = len(project.projectpermissions_set.all()) + 1
    coder_size = math.ceil(batch_size / num_coders)

    data = util.get_assignments(profile, project, coder_size)
    labels = Label.objects.all().filter(project=project)

    return Response({'labels': LabelSerializer(labels, many=True).data, 'data': DataSerializer(data, many=True).data})


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
    label = Label.objects.get(pk=request.data['labelID'])
    util.label_data(label, data, profile)

    util.check_and_trigger_model(data)

    return Response({})

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
