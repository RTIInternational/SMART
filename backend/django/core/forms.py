from django import forms
from django.core.exceptions import ValidationError
from .models import Project, ProjectPermissions, Label
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from django.forms.widgets import RadioSelect
import copy



def clean_data_helper(data, supplied_labels):
    ALLOWED_TYPES = [
        'text/csv',
        'text/tab-separated-values',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
        'application/vnd.ms-excel.sheet.macroenabled.12',
        'application/vnd.ms-excel.template.macroenabled.12',
        'application/vnd.ms-excel.addin.macroenabled.12',
        'application/vnd.ms-excel.sheet.binary.macroenabled.12'
    ]
    ALLOWED_HEADER = ['Text', 'Label']
    MAX_FILE_SIZE = 4 * 1000 * 1000 * 1000

    if data.size > MAX_FILE_SIZE:
        raise ValidationError("File is too large.  Received {0} but max size is {1}."\
                              .format(data.size, MAX_FILE_SIZE))

    try:
        if data.content_type == 'text/tab-separated-values':
            data = pd.read_csv(data, sep='\t')
        elif data.content_type == 'text/csv':
            data = pd.read_csv(data)
        elif data.content_type.startswith('application/vnd') and data.name.endswith('.csv'):
            data = pd.read_csv(data)
        elif data.content_type.startswith('application/vnd') and data.name.endswith('.xlsx'):
            data = pd.read_excel(data)
        else:
            raise ValidationError("File type is not supported.  Received {0} but only {1} are supported."\
                              .format(data.content_type, ', '.join(ALLOWED_TYPES)))
    except ParserError:
        # If there was an error while parsing then raise invalid file error
        raise ValidationError("Unable to read file.  Please ensure it passes all the requirments")
    except UnicodeDecodeError:
        # Some files are not in utf-8, let's just reject those.
        raise ValidationError("Unable to read the file.  Please ensure that the file is encoded in UTF-8.")

    if len(data.columns) != len(ALLOWED_HEADER):
        raise ValidationError("File has incorrect number of columns.  Received {0} but expected {1}."\
                              .format(len(data.columns), len(ALLOWED_HEADER)))

    if data.columns.tolist() != ALLOWED_HEADER:
        raise ValidationError("File headers are incorrect.  Received {0} but header must be {1}."\
                              .format(', '.join(data.columns), ', '.join(ALLOWED_HEADER)))

    if len(data) < 1:
        raise ValidationError("File should contain some data.")

    labels_in_data = data['Label'].dropna(inplace=False).unique()
    if len(labels_in_data) > 0 and set(labels_in_data) != set(supplied_labels):
        raise ValidationError(
            "Labels in file do not match labels created in step 2.  File supplied {0} "
            "but step 2 was given {1}".format(', '.join(labels_in_data), ', '.join(supplied_labels))
        )

    num_unlabeled_data = len(data[pd.isnull(data['Label'])])
    if num_unlabeled_data < 1:
        raise ValidationError(
            "All text in the file already has a label.  SMART needs unlabeled data "
            "to do active learning.  Please upload a file that has less labels."
        )

    return data

def cleanCodebookDataHelper(data):
    if not (data.content_type == "application/pdf"):
        raise ValidationError("File type is not supported. Please upload a PDF.")
    return data


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

    name = forms.CharField()
    description = forms.CharField(required=False)
    data = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        self.project_labels = kwargs.pop('labels', None)
        super(ProjectUpdateForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get('data', False)
        labels = self.project_labels
        if data:
            return clean_data_helper(data, labels)


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = '__all__'

    name = forms.CharField()
    description = forms.CharField(required=False, initial="")

class ProjectPermissionsForm(forms.ModelForm):
    class Meta:
        model = ProjectPermissions
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        self.action = kwargs.pop('action', None)
        self.creator = kwargs.pop('creator', None)
        super(ProjectPermissionsForm, self).__init__(*args, **kwargs)
        # If creator is set, then the project is being updated and we want to make sure to exclude creator
        # If creator is not set, then project is being created and we want to make sure to exclude the current user (as they are the creator)
        if self.creator:
            self.fields['profile']._set_queryset(self.fields['profile'].choices.queryset.exclude(user__profile=self.creator))
        else:
            self.fields['profile']._set_queryset(self.fields['profile'].choices.queryset.exclude(user__profile=self.profile))


LabelFormSet = forms.inlineformset_factory(Project, Label, form=LabelForm, min_num=2, validate_min=True, extra=0, can_delete=True)
PermissionsFormSet = forms.inlineformset_factory(Project, ProjectPermissions, form=ProjectPermissionsForm, extra=1, can_delete=True)

class ProjectWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class AdvancedWizardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['learning_method']

    use_active_learning = forms.BooleanField(initial=False, required=False)
    active_l_choices = copy.deepcopy(Project.ACTIVE_L_CHOICES)
    #remove random from the options
    active_l_choices.remove(("random","Randomly (No Active Learning)"))
    learning_method = forms.ChoiceField(
        widget=RadioSelect(), choices=active_l_choices,
        initial="least confident", required=False
    )

    def clean(self):
        use_active_learning = self.cleaned_data.get("use_active_learning")
        #if they are not using active learning, the selection method is random
        if not use_active_learning:
            self.cleaned_data['learning_method'] = 'random'
        return self.cleaned_data


class DataWizardForm(forms.Form):
    data = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.supplied_labels = kwargs.pop('labels', None)
        super(DataWizardForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get('data', False)
        labels = self.supplied_labels
        return clean_data_helper(data, labels)

class CodeBookWizardForm(forms.Form):
    data = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super(CodeBookWizardForm, self).__init__(*args, **kwargs)

    def clean_data(self):
        data = self.cleaned_data.get('data', False)
        if data:
            return cleanCodebookDataHelper(data)
        else:
            return ""
