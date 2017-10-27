from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.db import transaction
from django.core.exceptions import PermissionDenied

import pandas as pd
import math

from core.models import (Profile, Project, ProjectPermissions, Model, Data, Label,
                         DataLabel, DataPrediction, Queue, DataQueue, AssignedData,
                         TrainingSet)
from core.forms import ProjectForm, ProjectUpdateForm, PermissionsFormSet, LabelFormSet
from core.serializers import DataSerializer
from core.templatetags import project_extras
import core.util as util
from core import tasks


# Projects
class ProjectCode(LoginRequiredMixin, TemplateView):
    template_name = 'smart/smart.html'

    def get_context_data(self, **kwargs):
        ctx = super(ProjectCode, self).get_context_data(**kwargs)

        ctx['pk'] = self.kwargs['pk']

        return ctx


class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    paginate_by = 10
    ordering = 'name'

    def get_queryset(self):
        # Projects profile created
        qs1 = Project.objects.filter(creator=self.request.user.profile)

        # Projects profile has permissions for
        qs2 = Project.objects.filter(projectpermissions__profile=self.request.user.profile)

        qs = qs1 | qs2

        return qs.distinct().order_by(self.ordering)


class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'

    def get_object(self, *args, **kwargs):
        obj = super(ProjectDetail, self).get_object(*args, **kwargs)

        # Check profile permissions before showing project detail page
        if project_extras.proj_permission_level(obj, self.request.user.profile) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj


class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'

    def get_context_data(self, **kwargs):
        data = super(ProjectCreate, self).get_context_data(**kwargs)

        # Set the formsets for the create view
        if self.request.POST:
            data['labels'] = LabelFormSet(self.request.POST, prefix='label_set')
            data['permissions'] = PermissionsFormSet(self.request.POST, prefix='permissions_set', form_kwargs={'action': 'create', 'profile': self.request.user.profile})
        else:
            data['labels'] = LabelFormSet(prefix='label_set')
            data['permissions'] = PermissionsFormSet(prefix='permissions_set', form_kwargs={'action': 'create', 'profile': self.request.user.profile})
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        labels = context['labels']
        permissions = context['permissions']
        with transaction.atomic():
            if labels.is_valid() and permissions.is_valid():
                # Save the project with creator
                self.object = form.save(commit=False)
                self.object.creator = self.request.user.profile
                self.object.save()

                # Training Set
                training_set = TrainingSet.objects.create(project=self.object, set_number=0)

                # Labels
                labels.instance = self.object
                labels.save()

                # Permissions
                permissions.instance = self.object
                permissions.save()

                # Queue
                batch_size = 10 * len([x for x in labels if x.cleaned_data != {} and x.cleaned_data['DELETE'] != True])
                num_coders = len([x for x in permissions if x.cleaned_data != {} and x.cleaned_data['DELETE'] != True]) + 1
                q_length = math.ceil(batch_size/num_coders) * num_coders + math.ceil(batch_size/num_coders) * (num_coders - 1)

                queue = util.add_queue(project=self.object, length=q_length)

                # If data exists save attempt to save it
                f_data = form.cleaned_data.get('data', False)
                if isinstance(f_data, pd.DataFrame):
                    data = util.add_data(self.object, f_data)

                    # If data was created then populate queue
                    util.fill_queue(queue, orderby='random')

                    # Create and save tf-idf
                    tasks.send_tfidf_creation_task.delay(DataSerializer(data, many=True).data, self.object.pk)

                    util.save_data_file(f_data, self.object.pk)

                return redirect(self.get_success_url())
            else:
                return self.render_to_response(context)


class ProjectUpdate(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'projects/create.html'

    def get_object(self, *args, **kwargs):
        obj = super(ProjectUpdate, self).get_object(*args, **kwargs)

        # Check profile permissions before showing project update page
        if project_extras.proj_permission_level(obj, self.request.user.profile) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj

    def get_context_data(self, **kwargs):
        data = super(ProjectUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['permissions'] = PermissionsFormSet(self.request.POST, instance=data['project'], prefix='permissions_set', form_kwargs={'action': 'update', 'creator':data['project'].creator, 'profile': self.request.user.profile})
        else:
            data['permissions'] = PermissionsFormSet(instance=data['project'], prefix='permissions_set', form_kwargs={'action': 'update', 'creator':data['project'].creator, 'profile': self.request.user.profile})
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        permissions = context['permissions']
        with transaction.atomic():
            if permissions.is_valid():
                self.object = form.save()
                permissions.instance = self.object
                permissions.save()

                f_data = form.cleaned_data.get('data', False)
                if isinstance(f_data, pd.DataFrame):
                    data = util.add_data(self.object, f_data)

                return redirect(self.get_success_url())
            else:
                return self.render_to_response(context)


class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')

    def get_object(self, *args, **kwargs):
        obj = super(ProjectDelete, self).get_object(*args, **kwargs)

        # Check profile permissions before showing project delete page
        if project_extras.proj_permission_level(obj, self.request.user.profile) == 0:
            raise PermissionDenied('You do not have permission to view this project')
        return obj
