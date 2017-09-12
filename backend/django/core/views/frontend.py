from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from core.models import (User, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData)
from core.forms import ProjectForm


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

    def form_valid(self, form):
        self.object = form.save()

        f_labels = form.cleaned_data.get('labels', False)
        if f_labels:
            labels = []
            for l in form.cleaned_data['labels'].split(','):
                labels.append(Label(name=l, project=self.object))
            Label.objects.bulk_create(labels)

        f_data = form.cleaned_data.get('data', False)
        if f_data:
            data = []
            for d in f_data[0]:
                data.append(Data(text=d, project=self.object))
            Data.objects.bulk_create(data)

        return HttpResponseRedirect(self.get_success_url())

class ProjectUpdate(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'

    def form_valid(self, form):
        self.object = form.save()

        f_labels = form.cleaned_data.get('labels', False)
        if f_labels:
            labels = []
            for l in form.cleaned_data['labels'].split(','):
                labels.append(Label(name=l, project=self.object))
            Label.objects.bulk_create(labels)

        f_data = form.cleaned_data.get('data', False)
        if f_data:
            data = []
            for d in f_data[0]:
                data.append(Data(text=d, project=self.object))
            Data.objects.bulk_create(data)

        return HttpResponseRedirect(self.get_success_url())

class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')