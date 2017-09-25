from django.contrib.auth.models import Group, User as AuthUser
from django.conf import settings
from rest_framework import serializers
from core.models import (User, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('labeled_data', 'auth_user')

class AuthUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AuthUser
        fields = ('url', 'username', 'email', 'groups')

class AuthUserGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class ProjectSerializer(serializers.ModelSerializer):
    labels = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = ('name','labels')

class ModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Model
        fields = ('pickle_path', 'project', 'predictions')

class LabelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Label
        fields = ('name', 'project')

class DataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Data
        fields = ('text', 'project')

class DataLabelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataLabel
        fields = ('data', 'user', 'label')

class DataPredictionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPrediction
        fields = ('data', 'model', 'predicted_class', 'predicted_probability')

class QueueSerializer(serializers.HyperlinkedModelSerializer):
    data = serializers.StringRelatedField(many=True)
    class Meta:
        model = Queue
        fields = ('user', 'project', 'length', 'data')

class AssignedDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AssignedData
        fields = ('user', 'data', 'queue', 'assigned_timestamp')
