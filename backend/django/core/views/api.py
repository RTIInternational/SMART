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

from core.serializers import (UserSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer, ProjectSerializer,
                              ModelSerializer, LabelSerializer, DataSerializer,
                              DataLabelSerializer, DataPredictionSerializer,
                              QueueSerializer, AssignedDataSerializer)
from core.models import (User, Project, Model, Data, Label, DataLabel,
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
        assigned_data = AssignedData.objects.filter(queue_id=q_pk).filter(user_id=get_user(request).user.pk)
        if len(assigned_data) > 0:
            data = [assigned.data.text for assigned in assigned_data]
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
                data.append(d.text)
                temp.append(AssignedData(queue=queue, data=d, user=get_user(request).user))
            AssignedData.objects.bulk_create(temp)
            DataQueue.objects.filter(data_id__in=[x.pk for x in data_qs]).filter(queue_id=q_pk).delete()

        labels = [label.name for label in Label.objects.all().filter(project=project.pk)]

        return Response({'labels': labels, 'data': data})


################################
#    DRF VIEWSET API CLASSES   #
################################

# TODO establish more restrictive permissions
# AuthUsers should be write-only for unauthenticated users
# Creation/update/deletion of certain objects that will be
# managed by the server probably shouldn't be exposed via the API
# (ex. Queues, Models, AssignedData, many-to-many join fields)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
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
