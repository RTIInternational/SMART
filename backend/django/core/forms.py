from django import forms
from django.core.exceptions import ValidationError
from .models import Project
import pandas as pd

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'

    name = forms.CharField()
    labels = forms.CharField(required=False)
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

            data = pd.read_csv(data, header=None)

            if len(data.columns) > 1:
                raise ValidationError("File should only contain one column")

            if len(data) < 1:
                raise ValidationError("File should contain some data")

        return data