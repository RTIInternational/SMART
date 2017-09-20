from django import forms
from django.core.exceptions import ValidationError
from .models import Project, ProjectPermissions, Label
import pandas as pd

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

    name = forms.CharField()
    data = forms.FileField(required=False)

    def clean_data(self):
        allowed_types = [
            'text/csv',
            'text/tab-separated-values'
        ]

        max_file_size = 4 * 1000 * 1000 * 1000

        data = self.cleaned_data.get('data', False)

        if data:            
            if data.size > max_file_size:
                raise ValidationError("File is too large")

            if data.content_type not in allowed_types:
                raise ValidationError("File type is not supported")

            if data.content_type == 'text/tab-separated-values':
                data = pd.read_csv(data, header=None, sep='\t')
            elif data.content_type == 'text/csv':
                data = pd.read_csv(data, header=None)
            else:
                raise ValidationError("File type is not supported")

            if len(data.columns) > 1:
                raise ValidationError("File should only contain one column")

            if len(data) < 1:
                raise ValidationError("File should contain some data")

        return data

class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = '__all__'

    name = forms.CharField()

class ProjectPermissionsForm(forms.ModelForm):
    class Meta:
        model = ProjectPermissions
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.action = kwargs.pop('action', None)
        self.creator = kwargs.pop('creator', None)
        super(ProjectPermissionsForm, self).__init__(*args, **kwargs)

    def clean_user(self):
        user = self.cleaned_data.get('user', False)
        if self.action == 'create' and user == self.user:
            raise ValidationError("You are the creator by default, please do not assign yourself any permissions")
        if self.action == 'update' and user == self.creator and self.user != self.creator:
            raise ValidationError("{0} is the creator, please do not assign them any permissions".format(self.creator))
        if self.action == 'update' and user == self.creator and self.user == self.creator:
            raise ValidationError("You are the creator by default, please do not assign yourself any permissions")

        return user

LabelFormSet = forms.inlineformset_factory(Project, Label, form=LabelForm, extra=1, can_delete=True)
PermissionsFormSet = forms.inlineformset_factory(Project, ProjectPermissions, form=ProjectPermissionsForm, extra=1, can_delete=True)