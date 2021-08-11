import copy
from io import StringIO

import numpy as np
import pandas as pd
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect, Select, Textarea, TextInput
from pandas.errors import ParserError

from core.utils.util import md5_hash

from .models import Label, Project, ProjectPermissions


def clean_data_helper(data, supplied_labels, metadata_fields=[]):
    ALLOWED_TYPES = [
        "text/csv",
        "text/tab-separated-values",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
        "application/vnd.ms-excel.sheet.macroenabled.12",
        "application/vnd.ms-excel.template.macroenabled.12",
        "application/vnd.ms-excel.addin.macroenabled.12",
        "application/vnd.ms-excel.sheet.binary.macroenabled.12",
    ]
    REQUIRED_HEADERS = ["Text", "Label"]
    MAX_FILE_SIZE = 500 * 1000 * 1000

    if data.size > MAX_FILE_SIZE:
        raise ValidationError(
            "File is too large.  Received {0} but max size is {1}.".format(
                data.size, MAX_FILE_SIZE
            )
        )

    try:
        if data.content_type == "text/tab-separated-values":
            data = pd.read_csv(
                StringIO(data.read().decode("utf8", "ignore")),
                sep="\t",
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data.content_type == "text/csv":
            data = pd.read_csv(
                StringIO(data.read().decode("utf8", "ignore")),
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data.content_type.startswith("application/vnd") and data.name.endswith(
            ".csv"
        ):
            data = pd.read_csv(
                StringIO(data.read().decode("utf8", "ignore")),
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data.content_type.startswith("application/vnd") and data.name.endswith(
            ".xlsx"
        ):
            data = pd.read_excel(data, dtype=str).dropna(axis=0, how="all")
        else:
            raise ValidationError(
                "File type is not supported.  Received {0} but only {1} are supported.".format(
                    data.content_type, ", ".join(ALLOWED_TYPES)
                )
            )
    except ParserError:
        # If there was an error while parsing then raise invalid file error
        raise ValidationError(
            "Unable to read file.  Please ensure it passes all the requirments"
        )
    except UnicodeDecodeError:
        # Some files are not in utf-8, let's just reject those.
        raise ValidationError(
            "Unable to read the file.  Please ensure that the file is encoded in UTF-8."
        )

    for col in REQUIRED_HEADERS:
        if col not in data.columns:
            raise ValidationError(f"File is missing required field {col}.")

    if len(data) < 1:
        raise ValidationError("File should contain some data.")

    found_metadata_fields = [
        c for c in data.columns if c.lower() not in ["text", "label", "id"]
    ]
    if metadata_fields is not None and (
        len(metadata_fields) > 0
        and (set(metadata_fields) != set(found_metadata_fields))
    ):
        raise ValidationError(
            "There were metadata fields provided in the "
            "initial data upload that are missing from this data."
            f" Original fields: {', '.join(metadata_fields)}."
            f" Found fields: {', '.join(found_metadata_fields)}."
        )

    labels_in_data = data["Label"].dropna(inplace=False).unique()
    if len(labels_in_data) > 0 and len(set(labels_in_data) - set(supplied_labels)) > 0:
        raise ValidationError(
            "There are extra labels in the file which were not created in step 2.  File supplied {0} "
            "but step 2 was given {1}".format(
                ", ".join(labels_in_data), ", ".join(supplied_labels)
            )
        )

    num_unlabeled_data = len(data[pd.isnull(data["Label"])])
    if num_unlabeled_data < 1:
        raise ValidationError(
            "All text in the file already has a label.  SMART needs unlabeled data "
            "to do active learning.  Please upload a file that has less labels."
        )

    if "ID" in data.columns:
        # there should be no null values
        if data["ID"].isnull().sum() > 0:
            raise ValidationError("Unique ID field cannot have missing values.")

        data_lens = data["ID"].astype(str).apply(lambda x: len(x))
        # check that the ID follow the character limit
        if np.any(np.greater(data_lens, [128] * len(data_lens))):
            raise ValidationError(
                "Unique ID should not be greater than 128 characters."
            )

        data["id_hash"] = data["ID"].astype(str).apply(md5_hash)
        # they have an id column, check for duplicates
        if len(data["id_hash"].tolist()) > len(data["id_hash"].unique()):
            raise ValidationError("Unique ID provided contains duplicates.")

    return data


def cleanCodebookDataHelper(data):
    if not (data.content_type == "application/pdf"):
        raise ValidationError("File type is not supported. Please upload a PDF.")
    return data


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]

    name = forms.CharField()
    description = forms.CharField(required=False)
    data = forms.FileField(required=False)
    cb_data = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        self.project_labels = kwargs.pop("labels", None)
        self.project_metadata = kwargs.pop("metadata", None)
        super(ProjectUpdateForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get("data", False)
        labels = self.project_labels
        metadata_fields = self.project_metadata
        cb_data = self.cleaned_data.get("cb_data", False)
        if data:
            return clean_data_helper(data, labels, metadata_fields)
        if cb_data:
            return cleanCodebookDataHelper(cb_data)


class ProjectUpdateOverviewForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]

    name = forms.CharField()
    description = forms.CharField(required=False)


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = "__all__"

    name = forms.CharField(widget=TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(
        required=False,
        initial="",
        widget=Textarea(attrs={"class": "form-control", "rows": "5"}),
    )


class LabelDescriptionForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ["name", "description"]

    name = forms.CharField(
        disabled=True, widget=TextInput(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        required=False, widget=Textarea(attrs={"class": "form-control", "rows": "5"})
    )

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop("action", None)
        super(LabelDescriptionForm, self).__init__(*args, **kwargs)


class ProjectPermissionsForm(forms.ModelForm):
    class Meta:
        model = ProjectPermissions
        fields = "__all__"
        widgets = {
            "profile": Select(attrs={"class": "form-control"}),
            "permission": Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        self.action = kwargs.pop("action", None)
        self.creator = kwargs.pop("creator", None)
        super(ProjectPermissionsForm, self).__init__(*args, **kwargs)
        # If creator is set, then the project is being updated and we want to make sure to exclude creator
        # If creator is not set, then project is being created and we want to make sure to exclude the current user (as they are the creator)
        if self.creator:
            self.fields["profile"]._set_queryset(
                self.fields["profile"].choices.queryset.exclude(
                    user__profile=self.creator
                )
            )
        else:
            self.fields["profile"]._set_queryset(
                self.fields["profile"].choices.queryset.exclude(
                    user__profile=self.profile
                )
            )


LabelFormSet = forms.inlineformset_factory(
    Project,
    Label,
    form=LabelForm,
    min_num=2,
    validate_min=True,
    extra=0,
    can_delete=True,
    absolute_max=10000,
)
LabelDescriptionFormSet = forms.inlineformset_factory(
    Project, Label, form=LabelDescriptionForm, can_delete=False, extra=0
)
PermissionsFormSet = forms.inlineformset_factory(
    Project, ProjectPermissions, form=ProjectPermissionsForm, extra=1, can_delete=True
)


class ProjectWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]


class AdvancedWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "learning_method",
            "percentage_irr",
            "num_users_irr",
            "batch_size",
            "classifier",
        ]

    use_active_learning = forms.BooleanField(initial=True, required=False)
    active_l_choices = copy.deepcopy(Project.ACTIVE_L_CHOICES)
    # remove random from the options
    active_l_choices.remove(("random", "Randomly (No Active Learning)"))
    learning_method = forms.ChoiceField(
        widget=RadioSelect(),
        choices=active_l_choices,
        initial="least confident",
        required=False,
    )
    use_irr = forms.BooleanField(initial=False, required=False)
    percentage_irr = forms.FloatField(initial=10.0, min_value=0.0, max_value=100.0)
    num_users_irr = forms.IntegerField(initial=2, min_value=2)
    use_default_batch_size = forms.BooleanField(initial=True, required=False)
    batch_size = forms.IntegerField(initial=30, min_value=10, max_value=10000)

    use_model = forms.BooleanField(initial=True, required=False)
    classifier = forms.ChoiceField(
        widget=RadioSelect(),
        choices=Project.CLASSIFIER_CHOICES,
        initial="logistic regression",
        required=False,
    )

    def clean(self):
        use_active_learning = self.cleaned_data.get("use_active_learning")
        use_default_batch_size = self.cleaned_data.get("use_default_batch_size")
        use_irr = self.cleaned_data.get("use_irr")
        use_model = self.cleaned_data.get("use_model")

        # if they are not using active learning, the selection method is random
        if not use_active_learning:
            self.cleaned_data["learning_method"] = "random"

        # if they are not using a model, they cannot use active learning
        if not use_model:
            self.cleaned_data["classifier"] = None
            self.cleaned_data["learning_method"] = "random"

        if use_default_batch_size:
            self.cleaned_data["batch_size"] = 0
        if not use_irr:
            self.cleaned_data["percentage_irr"] = 0
        return self.cleaned_data


class DataWizardForm(forms.Form):
    data = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.supplied_labels = kwargs.pop("labels", None)
        self.supplied_metadata = kwargs.pop("metadata", None)
        super(DataWizardForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get("data", False)
        labels = self.supplied_labels
        metadata = self.supplied_metadata
        return clean_data_helper(data, labels, metadata)


class CodeBookWizardForm(forms.Form):
    data = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super(CodeBookWizardForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get("data", False)
        if data:
            return cleanCodebookDataHelper(data)
        else:
            return ""
