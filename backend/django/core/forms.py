import copy
from io import StringIO

import numpy as np
import pandas as pd
from django import forms
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect, Select, Textarea, TextInput
from pandas.errors import ParserError

from core.utils.util import calculate_hash, md5_hash
from core.utils.utils_external_db import (
    get_connection,
    get_full_table,
    test_connection,
    test_schema_exists,
)

from .models import Data, ExternalDatabase, Label, Project, ProjectPermissions


def read_data_file(data_file):
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
    MAX_FILE_SIZE = 500 * 1000 * 1000
    if data_file is None:
        raise ValidationError("ERROR: no file specified.")

    if data_file.size > MAX_FILE_SIZE:
        raise ValidationError(
            "File is too large.  Received {0} but max size is {1}.".format(
                data_file.size, MAX_FILE_SIZE
            )
        )

    try:
        if data_file.content_type == "text/tab-separated-values":
            data = pd.read_csv(
                StringIO(data_file.read().decode("utf8", "ignore")),
                sep="\t",
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data_file.content_type == "text/csv":
            data = pd.read_csv(
                StringIO(data_file.read().decode("utf8", "ignore")),
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data_file.content_type.startswith(
            "application/vnd"
        ) and data_file.name.endswith(".csv"):
            data = pd.read_csv(
                StringIO(data_file.read().decode("utf8", "ignore")),
                dtype=str,
            ).dropna(axis=0, how="all")
        elif data_file.content_type.startswith(
            "application/vnd"
        ) and data_file.name.endswith(".xlsx"):
            data = pd.read_excel(data_file, dtype=str).dropna(axis=0, how="all")
        else:
            raise ValidationError(
                "File type is not supported.  Received {0} but only {1} are supported.".format(
                    data_file.content_type, ", ".join(ALLOWED_TYPES)
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
    return data


def clean_data_helper(
    data, supplied_labels, dedup_on, dedup_fields, metadata_fields=None
):

    # correct for differences in capitalization
    for col in data.columns:
        for field, field_lower in zip(["Text", "Label", "ID"], ["text", "label", "id"]):
            if col != field and col == field_lower:
                data.rename(columns={col: field}, inplace=True)

    if "Text" not in data.columns:
        raise ValidationError("Data is missing required field 'Text'.")

    if "Label" not in data.columns:
        data["Label"] = None

    if len(data) < 1:
        raise ValidationError("Data is empty.")

    found_metadata_fields = [
        c for c in data.columns if c not in ["Text", "Label", "ID"]
    ]

    # this option is only true if we're adding data to an existing project
    if (
        metadata_fields is not None
        and len(metadata_fields) > 0
        and (set(metadata_fields) != set(found_metadata_fields))
    ):
        raise ValidationError(
            "There were metadata fields provided in the "
            "initial data upload that are missing from this data."
            f" Original fields: {', '.join(metadata_fields)}."
            f" Found fields: {', '.join(found_metadata_fields)}."
        )

    # validating the dedup list being sent
    if dedup_on == "Text_Some_Metadata" and len(dedup_fields) == 0:
        raise ValidationError(
            "The 'Text and Metadata fields'"
            " option was selected but no metadata fields were specified."
        )

    if len(dedup_fields) > 0:
        dedup_list = [
            d.strip() for d in dedup_fields.strip().split(";") if len(d.strip()) > 0
        ]
        if metadata_fields is not None:
            compare_list = metadata_fields
        else:
            compare_list = found_metadata_fields

        # if there is no metadata then there can't be dedup fields
        if len(set(dedup_list) - set(compare_list)) > 0:
            raise ValidationError(
                "The dedup fields specified should be a subset of"
                " the data's provided metadata fields. "
                f"Dedup fields: {dedup_list},"
                f" Metadata fields: {compare_list}"
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
        self.dedup_on = kwargs.pop("dedup_on", None)
        self.dedup_fields = kwargs.pop("dedup_fields", None)
        super(ProjectUpdateForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get("data", False)
        labels = self.project_labels
        metadata_fields = self.project_metadata
        dedup_on = self.dedup_on
        dedup_fields = self.dedup_fields
        cb_data = self.cleaned_data.get("cb_data", False)
        if data:
            data_df = read_data_file(data)
            return clean_data_helper(
                data_df, labels, dedup_on, dedup_fields, metadata_fields
            )
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
        self.fields["profile"]._set_queryset(
            self.fields["profile"].choices.queryset.order_by("user__username")
        )


LabelFormSet = forms.inlineformset_factory(
    Project,
    Label,
    form=LabelForm,
    min_num=2,
    validate_min=True,
    extra=0,
    can_delete=True,
    absolute_max=55000,
)
LabelDescriptionFormSet = forms.inlineformset_factory(
    Project,
    Label,
    form=LabelDescriptionForm,
    can_delete=False,
    extra=0,
    absolute_max=55000,
)
PermissionsFormSet = forms.inlineformset_factory(
    Project, ProjectPermissions, form=ProjectPermissionsForm, extra=1, can_delete=True
)


class ProjectWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "umbrella_string"]


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

    use_active_learning = forms.BooleanField(initial=False, required=False)
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
    batch_size = forms.IntegerField(initial=30, min_value=10, max_value=55000)

    use_model = forms.BooleanField(initial=False, required=False)
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


class DataWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["dedup_on", "dedup_fields"]

    data_source = forms.ChoiceField(
        widget=RadioSelect(),
        choices=(
            ("File_Upload", "File Upload"),
            ("Database_Ingest", "Connect to Database and Import Table"),
        ),
        initial="File_Upload"
        if cache.get("ext_db") != "microsoft"
        else "Database_Ingest",
        required=True,
    )

    data = forms.FileField(required=False)

    dedup_on = forms.ChoiceField(
        widget=RadioSelect(),
        choices=Project.DEDUP_CHOICES,
        initial="Text",
        required=True,
    )

    dedup_fields = forms.CharField(required=False, initial="", max_length=50)

    def __init__(self, *args, **kwargs):
        self.supplied_labels = kwargs.pop("labels", None)
        self.engine_database = kwargs.pop("engine_database", None)
        self.ingest_schema = kwargs.pop("ingest_schema", None)
        self.ingest_table_name = kwargs.pop("ingest_table_name", None)
        super(DataWizardForm, self).__init__(*args, **kwargs)

    def clean(self):
        data_source = self.cleaned_data.get("data_source", False)
        if data_source == "File_Upload":
            data_df = read_data_file(self.cleaned_data.get("data", False))
        elif data_source == "Database_Ingest":
            if self.ingest_schema is None:
                raise ValidationError(
                    "No ingest table specified. Please add an ingest "
                    "schema and table to the external database connection."
                )
            data_df = get_full_table(
                self.engine_database, self.ingest_schema, self.ingest_table_name
            )
        else:
            raise ValidationError(
                f"Unrecognized value for data source type: {data_source}"
            )

        dedup_on = self.cleaned_data.get("dedup_on", False)
        dedup_fields = ""
        if dedup_on == "Text_Some_Metadata":
            dedup_fields = self.cleaned_data.get("dedup_fields", False)

        labels = self.supplied_labels
        self.cleaned_data["data"] = clean_data_helper(
            data_df, labels, dedup_on, dedup_fields
        )
        return self.cleaned_data


class DataUpdateWizardForm(forms.Form):

    data = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        self.supplied_labels = kwargs.pop("labels", None)
        self.supplied_metadata = kwargs.pop("metadata", None)
        self.dedup_on = kwargs.pop("dedup_on", None)
        self.dedup_fields = kwargs.pop("dedup_fields", None)
        super(DataUpdateWizardForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data_df = read_data_file(self.cleaned_data.get("data", False))
        dedup_on = self.dedup_on
        dedup_fields = ""
        if dedup_on == "Text_Some_Metadata":
            dedup_fields = self.dedup_fields

        labels = self.supplied_labels
        metadata = self.supplied_metadata

        project = self.project

        return self.clean_update_data_helper(
            project, data_df, labels, dedup_on, dedup_fields, metadata
        )

    def clean_update_data_helper(
        self,
        project,
        data,
        supplied_labels,
        dedup_on,
        dedup_fields,
        metadata_fields=None,
    ):
        # Validate using default data cleaner
        data = clean_data_helper(
            data, supplied_labels, dedup_on, dedup_fields, metadata_fields
        )

        # Check which hashes are already in the db
        data_hashes = calculate_hash(project, data)
        exiting_hashes = list(
            Data.objects.filter(project=project).values_list("hash", flat=True)
        )
        dup_data = data.loc[data_hashes.isin(exiting_hashes)]

        if not dup_data.empty:
            # Find rows where Label is not none
            overwrite_data = dup_data.loc[~dup_data["Label"].isnull()]

            # Throw error containing rows which are going to overwritten
            if not overwrite_data.empty:
                error_str = "The following uploaded text + metadata combinations are already in the database and the uploaded labels will not be reflected in the database:\n\n"
                df_str = overwrite_data.head(10).to_csv(index=False)
                size = overwrite_data.shape[0]
                remaining_str = (
                    f"----{size-10} rows remaining----\n\n" if size > 10 else "\n\n"
                )
                hint_str = "Please delete the labels or remove the rows before uploading the data"
                raise ValidationError(error_str + df_str + remaining_str + hint_str)


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


class ExternalDatabaseWizardForm(forms.ModelForm):
    class Meta:
        model = ExternalDatabase
        fields = [
            "database_type",
            "ingest_schema",
            "ingest_table_name",
            "export_schema",
            "export_table_name",
        ]

    database_type = forms.ChoiceField(
        widget=RadioSelect(),
        choices=ExternalDatabase.DB_TYPE_CHOICES,
        initial="none",
        required=True,
    )
    ingest_table_name = forms.CharField(initial="", required=False, max_length=50)
    ingest_schema = forms.CharField(initial="", required=False, max_length=50)
    export_table_name = forms.CharField(initial="", required=False, max_length=1024)
    export_schema = forms.CharField(initial="", required=False, max_length=1024)
    username = forms.CharField(initial="", required=False, max_length=50)
    password = forms.CharField(
        initial="", required=False, max_length=200, widget=forms.PasswordInput()
    )
    host = forms.CharField(initial="", required=False, max_length=50)
    port = forms.IntegerField(required=False)
    dbname = forms.CharField(initial="", required=False, max_length=50)
    driver = forms.CharField(
        initial="ODBC Driver 17 for SQL Server", required=False, max_length=200
    )

    def __init__(self, *args, **kwargs):
        super(ExternalDatabaseWizardForm, self).__init__(*args, **kwargs)

    def clean(self):
        required_for_all_db = [
            "ingest_table_name",
            "ingest_schema",
            "export_table_name",
            "export_schema",
            "username",
            "password",
            "host",
            "port",
            "dbname",
        ]
        required_for_ms_sql = ["driver"]
        db_type = self.cleaned_data.get("database_type")

        field_error = False
        if db_type != "none":
            for field in required_for_all_db:
                if self.cleaned_data.get(field) in ["", None]:
                    self._errors[field] = self.error_class(
                        ["This field is required for a database connection."]
                    )
                    field_error = True
            if db_type == "microsoft":
                for field in required_for_ms_sql:
                    if self.cleaned_data.get(field) in ["", None]:
                        self._errors[field] = self.error_class(
                            ["This field is required for a MS SQL database connection."]
                        )
                        field_error = True
            if field_error:
                raise ValidationError("Please fix field errors before resubmitting.")

            # Cache database type for update data view
            cache.set("ext_db", db_type)

            engine_database = get_connection(db_type, self.cleaned_data)

            self.cleaned_data["has_ingest"] = False
            self.cleaned_data["has_export"] = False

            # need to specify both schema and table for ingest/export if using it
            if (
                len(self.cleaned_data["ingest_schema"]) > 0
                or len(self.cleaned_data["ingest_table_name"]) > 0
            ):
                if len(self.cleaned_data["ingest_table_name"]) == 0:
                    raise ValueError(
                        "ERROR: need to specify ingest table if schema is set."
                    )
                if len(self.cleaned_data["ingest_schema"]) == 0:
                    raise ValueError(
                        "ERROR: need to specify ingest schema if table name is set."
                    )

                self.cleaned_data["has_ingest"] = True

                # for ingest, schema and table should exist and table should have fields needed
                test_schema_exists(engine_database, self.cleaned_data["ingest_schema"])
                test_connection(
                    engine_database,
                    self.cleaned_data["ingest_schema"],
                    self.cleaned_data["ingest_table_name"],
                )

            if (
                len(self.cleaned_data["export_schema"]) > 0
                or len(self.cleaned_data["export_table_name"]) > 0
            ):
                if len(self.cleaned_data["export_table_name"]) == 0:
                    raise ValueError(
                        "ERROR: need to specify export table if schema is set."
                    )
                if len(self.cleaned_data["export_schema"]) == 0:
                    raise ValueError(
                        "ERROR: need to specify export schema if table name is set."
                    )

                self.cleaned_data["has_export"] = True

                # for export, table may not exist but schema should exist
                test_schema_exists(engine_database, self.cleaned_data["export_schema"])

            self.cleaned_data["engine_database"] = engine_database
