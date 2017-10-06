from django.shortcuts import render
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

import math

from core.serializers import (ProfileSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer, ProjectSerializer,
                              ModelSerializer, LabelSerializer, DataSerializer,
                              DataLabelSerializer, DataPredictionSerializer,
                              QueueSerializer, AssignedDataSerializer)
from core.models import (Profile, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData)
import core.util as util

############################################
#    REACT API ENDPOINTS FOR CODING VIEW   #
############################################

@api_view(['GET'])
def grab_from_queue(request, pk):
    """Grab x data from the queue and add the data to assigned data.

    Args:
        request: The request to the endpoint
        pk: Primary key of queue
    Returns:
        labels: The project labels
        data: The data in the queue
        <errors>: Only exists if there is an error, the error message.
    """
    if request.method == 'GET':
        q_pk = pk
        try:
            queue = Queue.objects.get(pk=q_pk)
            project = Project.objects.get(pk=queue.project.pk)
        except ObjectDoesNotExist:
            return Response({'error': 'There is no queue matching that primary key.'})

        # Check if data is already assigned to user
        assigned_data = AssignedData.objects.filter(queue=queue, profile=request.user.profile)
        if len(assigned_data) > 0:
            data = [[assigned.data.pk, assigned.data.text] for assigned in assigned_data]
        else:
            # Calculate queue parameters
            batch_size = len(project.labels.all()) * 10
            num_coders = len(project.projectpermissions_set.all()) + 1
            coder_size = math.ceil(batch_size / num_coders)

            # Find coding data, remove from queue, add to assigned data
            data_qs = queue.data.all()[:coder_size]
            data = []
            temp = []
            for d in data_qs:
                data.append([d.pk, d.text])
                temp.append(AssignedData(queue=queue, data=d, profile=request.user.profile))
            AssignedData.objects.bulk_create(temp)
            DataQueue.objects.filter(data_id__in=[x.pk for x in data_qs], queue=queue).delete()

        labels = [[label.pk, label.name] for label in Label.objects.all().filter(project=project)]

        return Response({'labels': labels, 'data': data, 'queue_id': q_pk})

@api_view(['POST'])
def annotate_data(request, pk):
    """Annotate a single datum which is in the assigneddata queue given the user,
       data_id, queue_id, and label_id.  This will remove it from assigneddata
       and add it to labeleddata.
    """
    queue_id = request.data['queueID']
    label_id = request.data['labelID']
    data_id = pk
    profile = request.user.profile

    if request.method == 'POST':
        assignedDatum = AssignedData.objects.get(data_id=data_id, queue_id=queue_id, profile=profile)

        DataLabel.objects.create(data=assignedDatum.data,
                                 profile=assignedDatum.profile,
                                 label=Label.objects.get(pk=label_id))

        assignedDatum.delete()

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

class ModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all().order_by('id')
    serializer_class = ModelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all().order_by('id')
    serializer_class = DataSerializer
    permission_classes = (permissions.IsAuthenticated,)

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
