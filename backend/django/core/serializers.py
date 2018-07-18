from django.contrib.auth.models import Group, User as AuthUser
from django.conf import settings
from rest_framework import serializers
from core.models import (Profile, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData, LabelChangeLog)


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ('labeled_data', 'user')

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
        fields = ('name','labels','learning_method', 'classifier')

class CoreModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Model
        fields = ('pickle_path', 'project', 'predictions')

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('pk', 'name', 'project', 'description')

class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = ('pk', 'text', 'project', 'hash', 'df_idx')

class DataLabelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataLabel
        fields = ('data', 'profile', 'label', 'timestamp')

class LabelChangeLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LabelChangeLog
        fields = ('project','data','profile', 'old_label', 'new_label' ,'change_timestamp')

class DataPredictionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPrediction
        fields = ('data', 'model', 'predicted_class', 'predicted_probability')

class QueueSerializer(serializers.HyperlinkedModelSerializer):
    data = serializers.StringRelatedField(many=True)
    class Meta:
        model = Queue
        fields = ('profile', 'project','admin' ,'length', 'data')

class AssignedDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AssignedData
        fields = ('profile', 'data', 'queue', 'assigned_timestamp')
