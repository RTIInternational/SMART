from django.contrib.auth.models import Group
from django.contrib.auth.models import User as AuthUser
from rest_framework import permissions, viewsets

from core.models import (
    AssignedData,
    Data,
    DataLabel,
    DataPrediction,
    Label,
    Model,
    Profile,
    Project,
    Queue,
)
from core.pagination import SmartPagination
from core.serializers import (
    AssignedDataSerializer,
    AuthUserGroupSerializer,
    AuthUserSerializer,
    CoreModelSerializer,
    DataLabelSerializer,
    DataPredictionSerializer,
    DataSerializer,
    LabelSerializer,
    ProfileSerializer,
    ProjectSerializer,
    QueueSerializer,
)

# TODO establish more restrictive permissions
# AuthUsers should be write-only for unauthenticated users
# Creation/update/deletion of certain objects that will be
# managed by the server probably shouldn't be exposed via the API
# (ex. Queues, Models, AssignedData, many-to-many join fields)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().order_by("id")
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AuthUserGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("id")
    serializer_class = AuthUserGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AuthUserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.all().order_by("id")
    serializer_class = AuthUserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by("id")
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CoreModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all().order_by("id")
    serializer_class = CoreModelSerializer
    permission_classes = (permissions.IsAuthenticated,)


class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all().order_by("id")
    serializer_class = DataSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SmartPagination


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all().order_by("id")
    serializer_class = LabelSerializer
    permission_classes = (permissions.IsAuthenticated,)


class DataLabelViewSet(viewsets.ModelViewSet):
    queryset = DataLabel.objects.all().order_by("id")
    serializer_class = DataLabelSerializer
    permission_classes = (permissions.IsAuthenticated,)


class DataPredictionViewSet(viewsets.ModelViewSet):
    queryset = DataPrediction.objects.all().order_by("id")
    serializer_class = DataPredictionSerializer
    permission_classes = (permissions.IsAuthenticated,)


class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all().order_by("id")
    serializer_class = QueueSerializer
    permission_classes = (permissions.IsAuthenticated,)


class AssignedDataViewSet(viewsets.ModelViewSet):
    queryset = AssignedData.objects.all().order_by("id")
    serializer_class = AssignedDataSerializer
    permission_classes = (permissions.IsAuthenticated,)
