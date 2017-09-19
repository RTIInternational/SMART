from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.db import transaction

import hashlib
import pandas as pd

from core.models import (User, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData)
from core.forms import ProjectForm, LabelFormSet


def md5_hash(obj):
    """Return MD5 hash hexdigest of obj; returns None if obj is None"""
    if obj is not None:
        return hashlib.md5(obj.encode('utf-8', errors='ignore')).hexdigest()
    else:
        return None

# Index
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'smart/smart.html'

# Projects
class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    paginate_by = 10

class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'

class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'

    def get_context_data(self, **kwargs):
        data = super(ProjectCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['labels'] = LabelFormSet(self.request.POST)
        else:
            data['labels'] = LabelFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        labels = context['labels']
        with transaction.atomic():
            self.object = form.save()

            if labels.is_valid():
                labels.instance = self.object
                labels.save()

        f_data = form.cleaned_data.get('data', False)
        if isinstance(f_data, pd.DataFrame):
            # Create hash of text and drop duplicates
            f_data['hash'] = f_data[0].apply(md5_hash)
            f_data.drop_duplicates(subset='hash', keep='first', inplace=True)

            # Limit the number of rows to 2mil
            f_data = f_data[:2000000]

            # Create data objects and bulk insert into database
            if len(f_data) > 0:
                f_data['objects'] = f_data.apply(lambda x: Data(text=x[0], project=self.object, hash=x['hash']), axis=1)
                Data.objects.bulk_create(f_data['objects'].tolist())

        return super(ProjectCreate, self).form_valid(form)

class ProjectUpdate(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'

    def get_context_data(self, **kwargs):
        data = super(ProjectUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['labels'] = LabelFormSet(self.request.POST, instance=data['project'])
        else:
            data['labels'] = LabelFormSet(instance=data['project'])
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        labels = context['labels']
        with transaction.atomic():
            self.object = form.save()

            if labels.is_valid():
                labels.instance = self.object
                labels.save()

        f_data = form.cleaned_data.get('data', False)
        if isinstance(f_data, pd.DataFrame):
            # Create hash of text and drop duplicates
            f_data['hash'] = f_data[0].apply(md5_hash)
            f_data.drop_duplicates(subset='hash', keep='first', inplace=True)

            # Drop any duplicates from existing data
            existing_hashes = set(Data.objects.filter(project=self.object).values_list('hash', flat=True))
            f_data = f_data[~f_data['hash'].isin(existing_hashes)]

            # Limit the number of rows to 2mil (including existing data)
            f_data = f_data[:2000000-len(existing_hashes)]

            # Create data objects and bulk insert into database
            if len(f_data) > 0:
                f_data['objects'] = f_data.apply(lambda x: Data(text=x[0], project=self.object, hash=x['hash']), axis=1)
                Data.objects.bulk_create(f_data['objects'].tolist())

        return super(ProjectUpdate, self).form_valid(form)

class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')