import pytz
from django.contrib.auth.models import Group
from django.contrib.auth.models import User as AuthUser
from rest_framework import serializers

from core.models import (
    AdjudicateDescription,
    AssignedData,
    Data,
    DataLabel,
    DataPrediction,
    IRRLog,
    Label,
    LabelChangeLog,
    Model,
    Profile,
    Project,
    Queue,
)
from smart.settings import TIME_ZONE_FRONTEND


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ("labeled_data", "user")


class AuthUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AuthUser
        fields = ("url", "username", "email", "groups")


class AuthUserGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ("url", "name")


class ProjectSerializer(serializers.ModelSerializer):
    labels = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = ("name", "labels", "learning_method", "classifier")


class CoreModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Model
        fields = ("pickle_path", "project", "predictions")


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ("pk", "name", "project", "description")


class DataSerializer(serializers.ModelSerializer):
    metadata = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Data
        fields = (
            "pk",
            "text",
            "project",
            "irr_ind",
            "hash",
            "upload_id_hash",
            "metadata",
        )


class DataMetadataIDSerializer(serializers.ModelSerializer):
    metadata = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Data
        fields = ("metadata",)


class DataLabelModelSerializer(serializers.ModelSerializer):
    profile = serializers.StringRelatedField(many=False, read_only=True)
    timestamp = serializers.DateTimeField(
        default_timezone=pytz.timezone(TIME_ZONE_FRONTEND), format="%Y-%m-%d, %I:%m %p"
    )

    class Meta:
        model = DataLabel
        fields = ("data", "profile", "label", "timestamp")


class DataLabelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataLabel
        fields = ("data", "profile", "label", "timestamp")


class IRRLogModelSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(
        default_timezone=pytz.timezone(TIME_ZONE_FRONTEND), format="%Y-%m-%d, %I:%m %p"
    )

    class Meta:
        model = IRRLog
        fields = ("data", "profile", "label", "timestamp")


class IRRLog(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IRRLog
        fields = ("data", "profile", "label", "timestamp")


class LabelChangeLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LabelChangeLog
        fields = (
            "project",
            "data",
            "profile",
            "old_label",
            "new_label",
            "change_timestamp",
        )


class DataPredictionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPrediction
        fields = ("data", "model", "predicted_class", "predicted_probability")


class QueueSerializer(serializers.HyperlinkedModelSerializer):
    data = serializers.StringRelatedField(many=True)

    class Meta:
        model = Queue
        fields = ("profile", "project", "admin", "length", "data")


class AssignedDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AssignedData
        fields = ("profile", "data", "queue", "assigned_timestamp")


class AdjudicateDescriptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AdjudicateDescription
        fields = ("project", "data", "message", "isResolved")
