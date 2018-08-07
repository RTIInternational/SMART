from django.shortcuts import render
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.db.models import Max, Min, FloatField
from django.db import connection
from django.contrib.postgres.fields import ArrayField
from django.utils.html import escape
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction


import csv
import io
import os
import math
import random
import pandas as pd
import zipfile
import tempfile
import numpy as np
from django.utils import timezone

from postgres_stats.aggregates import Percentile

from core.serializers import (ProfileSerializer, AuthUserGroupSerializer,
                              AuthUserSerializer, ProjectSerializer,
                              CoreModelSerializer, LabelSerializer, DataSerializer,
                              DataLabelSerializer, DataPredictionSerializer,
                              QueueSerializer, AssignedDataSerializer,
                              LabelChangeLogSerializer)
from core.models import (Profile, Project, Model, Data, Label, DataLabel,
                         DataPrediction, Queue, DataQueue, AssignedData, TrainingSet,
                         LabelChangeLog, RecycleBin, IRRLog, ProjectPermissions)
import core.util as util
from core.pagination import SmartPagination
from core.templatetags import project_extras


class IsAdminOrCreator(permissions.BasePermission):
    """
    Checks if the requestor of the endpoint is admin or creator of a project
    """
    message = 'Invalid permission. Must be an admin'


    def has_permission(self, request, view):
        if 'project_pk' in view.kwargs:
            project = Project.objects.get(pk=view.kwargs['project_pk'])
        elif 'data_pk' in view.kwargs:
            project = Data.objects.get(pk=view.kwargs['data_pk']).project
        else:
            return False

        return project_extras.proj_permission_level(project, request.user.profile) > 1


class IsCoder(permissions.BasePermission):
    """
    Checks if the requestor of the endpoint is coder (or higher permission) of a project

    Use pk_kwarg_mapping dictionary to map from the request.path to the appropriate type of pk
    """
    message = 'Account disabled by administrator.  Please contact project owner for details'

    def has_permission(self, request, view):
        if 'project_pk' in view.kwargs:
            project = Project.objects.get(pk=view.kwargs['project_pk'])
        elif 'data_pk' in view.kwargs:
            project = Data.objects.get(pk=view.kwargs['data_pk']).project
        else:
            return False

        return project_extras.proj_permission_level(project, request.user.profile) > 0


############################################
#        FRONTEND USER API ENDPOINTS       #
############################################
@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def download_data(request, project_pk):
    """This function gets the labeled data and makes it available for download

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        an HttpResponse containing the requested data
    """
    data_objs = Data.objects.filter(project=project_pk)
    project_labels = Label.objects.filter(project=project_pk)
    data = []
    for label in project_labels:
        labeled_data = DataLabel.objects.filter(label=label)
        for d in labeled_data:
            temp = {}
            temp['ID'] = d.data.upload_id
            temp['Text'] = d.data.text
            temp['Label'] = label.name
            data.append(temp)

    buffer = io.StringIO()
    wr = csv.DictWriter(buffer, fieldnames=['ID','Text', 'Label'], quoting=csv.QUOTE_ALL)
    wr.writeheader()
    wr.writerows(data)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment;'

    return response


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def download_model(request, pk):
    """This function gets the labeled data and makes it available for download

    Args:
        request: The POST request
        pk: Primary key of the project
    Returns:
        an HttpResponse containing the requested data
    """
    project = Project.objects.get(pk=pk)
    data_objs = Data.objects.filter(project=pk)
    project_labels = Label.objects.filter(project=pk)

    #https://stackoverflow.com/questions/12881294/django-create-a-zip-of-multiple-files-and-make-it-downloadable
    zip_subdir = 'model_project'+str(pk)
    zip_filename = 'model_project'+str(pk)+".zip"

    #readme_file = 'README.txt'
    num_proj_files = len([f for f in os.listdir(settings.PROJECT_FILE_PATH)
                          if f.startswith('project_'+str(pk))])

    tfidf_path = os.path.join(settings.TF_IDF_PATH, str(pk) + '.npz')
    readme_path = './core/data/README.txt'
    current_training_set = project.get_current_training_set()
    model_path = os.path.join(settings.MODEL_PICKLE_PATH, 'project_' + str(pk) + '_training_' + str(current_training_set.set_number - 1) + '.pkl')

    #get the data labels
    data = []
    for label in project_labels:
        labeled_data = DataLabel.objects.filter(label=label)
        for d in labeled_data:
            temp = {}
            temp['ID'] = d.data.upload_id
            temp['Text'] = d.data.text
            temp['Label'] = label.name
            data.append(temp)

    #open the tempfile and write the label data to it
    temp_labelfile = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=settings.DATA_DIR)
    temp_labelfile.seek(0)
    wr = csv.DictWriter(temp_labelfile, fieldnames=['ID','Text', 'Label'], quoting=csv.QUOTE_ALL)
    wr.writeheader()
    wr.writerows(data)
    temp_labelfile.flush()
    temp_labelfile.close()

    s = io.BytesIO()
    #open the zip folder
    zip_file =  zipfile.ZipFile(s, "w")
    for path in [tfidf_path, readme_path, model_path, temp_labelfile.name]:
        fdir, fname = os.path.split(path)
        if path == temp_labelfile.name:
            fname = "project_"+str(pk)+"_labels.csv"
        #write the file to the zip folder
        zip_path = os.path.join(zip_subdir, fname)
        zip_file.write(path, zip_path)
    zip_file.close()

    response = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'attachment;'

    return response

@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def label_distribution_inverted(request, project_pk):
    """This function finds and returns the number of each label. The format
    is more focussed on showing the total amount of each label then the user
    label distribution, so the data is inverted from the function below.
    This is used by a graph on the front end admin page.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of the amount each label has been used
    """
    project = Project.objects.get(pk=project_pk)
    labels = [l for l in project.labels.all()]
    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    all_counts = []
    for u in users:
        temp_data = {'key':u.__str__()}
        temp_values = []
        for l in labels:
            label_count = DataLabel.objects.filter(profile=u, label=l).count()
            all_counts.append(label_count)
            temp_values.append({'x':l.name, 'y':label_count})
        dataset.append({'key':u.__str__(), 'values':temp_values})


    if not any(count > 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def label_distribution(request, project_pk):
    """This function finds and returns the number of each label per user.
    This is used by a graph on the front end admin page.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of the amount of labels per person per type
    """
    project = Project.objects.get(pk=project_pk)
    labels = [l for l in project.labels.all()]
    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    all_counts = []
    for l in labels:
        temp_data = {'key':l.name}
        temp_values = []
        for u in users:
            label_count = DataLabel.objects.filter(profile=u, label=l).count()
            all_counts.append(label_count)
            temp_values.append({'x':u.__str__(), 'y': label_count})
        dataset.append({'key':l.name, 'values': temp_values})

    if not any(count > 0 for count in all_counts):
        dataset = []

    return Response(dataset)


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def label_timing(request, project_pk):
    """This function finds and returns the requested label time metrics. This is
    used by the graphs on the admin page to show how long each labeler is taking.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of label timing information.
    """
    project = Project.objects.get(pk=project_pk)

    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    dataset = []
    yDomain = 0
    for u in users:
        result = DataLabel.objects.filter(data__project=project_pk, profile=u)\
                    .aggregate(quartiles=Percentile('time_to_label', [0.05, 0.25, 0.5, 0.75, 0.95],
                               continuous=False,
                               output_field=ArrayField(FloatField())))

        if result['quartiles']:
            if result['quartiles'][4] > yDomain:
                yDomain = result['quartiles'][4] + 10
            temp = {
                'label': u.__str__(),
                'values': {
                    'Q1': result['quartiles'][1],
                    'Q2': result['quartiles'][2],
                    'Q3': result['quartiles'][3],
                    'whisker_low': result['quartiles'][0],
                    'whisker_high': result['quartiles'][4]
                }
            }
            dataset.append(temp)

    return Response({'data': dataset, 'yDomain': yDomain})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def model_metrics(request, project_pk):
    """This function finds and returns the requested metrics. This is
    used by the graphs on the front end admin page.
    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of model metric information
    """
    metric = request.GET.get('metric', 'accuracy')

    project = Project.objects.get(pk=project_pk)
    models = Model.objects.filter(project=project).order_by('training_set__set_number')

    if metric == 'accuracy':
        values = []
        for model in models:
            values.append({
                'x': model.training_set.set_number,
                'y': model.cv_accuracy
            })

        dataset = [
            {
                'key': 'Accuracy',
                'values': values
            }
        ]
    else:
        labels = {str(label.pk): label.name for label in  project.labels.all()}
        dataset = []
        for label in labels:
            values = []
            for model in models:
                current_metric = model.cv_metrics[metric][label]
                values.append({
                    'x':  model.training_set.set_number,
                    'y': current_metric
                  })
            dataset.append({
                'key': labels[label],
                'values': values
            })

    return Response(dataset)


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def data_coded_table(request, project_pk):
    """This returns the labeled data

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)

    data_objs = DataLabel.objects.filter(data__project=project)

    data = []
    for d in data_objs:
        temp = {
            'Text': escape(d.data.text),
            'Label': d.label.name,
            'Coder': d.profile.__str__()
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def data_change_log_table(request, project_pk):
    """This returns the data of the label change log for visualization in a table

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    data_objs = LabelChangeLog.objects.filter(project=project)
    data = []
    for d in data_objs:
        if d.change_timestamp:
            if d.change_timestamp.minute < 10:
                minute = "0" + str(d.change_timestamp.minute)
            else:
                minute = str(d.change_timestamp.minute)
            new_timestamp = str(d.change_timestamp.date()) + ", " + str(d.change_timestamp.hour)\
            + ":" + minute + "." + str(d.change_timestamp.second)
        else:
            new_timestamp = "None"

        temp = {
            'Text': escape(d.data.text),
            'Coder': escape(d.profile.user),
            'Old Label': d.old_label,
            'New Label': d.new_label,
            'Timestamp': new_timestamp
        }

        data.append(temp)
    return Response({'data': data})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def data_predicted_table(request, project_pk):
    """This returns the predictions for the unlabeled data

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    previous_run = project.get_current_training_set().set_number - 1

    sql = """
    SELECT d.{data_text_col}, l.{label_name_col}, dp.{pred_prob_col}
    FROM (
        SELECT {pred_data_id_col}, MAX({pred_prob_col}) AS max_prob
        FROM {pred_table}
        GROUP BY {pred_data_id_col}
        ) as tmp
    LEFT JOIN {pred_table} as dp
    ON dp.{pred_data_id_col} = tmp.{pred_data_id_col} AND dp.{pred_prob_col} = tmp.max_prob
    LEFT JOIN {label_table} as l
    ON l.{label_pk_col} = dp.{pred_label_id_col}
    LEFT JOIN {data_table} as d
    ON d.{data_pk_col} = dp.{pred_data_id_col}
    LEFT JOIN {model_table} as m
    ON m.{model_pk_col} = dp.{pred_model_id_col}
    LEFT JOIN {trainingset_table} as ts
    ON ts.{trainingset_pk_col} = m.{model_trainingset_id_col}
    WHERE ts.{trainingset_setnumber_col} = {previous_run} AND d.{data_project_id_col} = {project_pk}
    """.format(
            data_text_col=Data._meta.get_field('text').column,
            label_name_col=Label._meta.get_field('name').column,
            pred_prob_col=DataPrediction._meta.get_field('predicted_probability').column,
            pred_data_id_col=DataPrediction._meta.get_field('data').column,
            pred_table=DataPrediction._meta.db_table,
            label_table=Label._meta.db_table,
            label_pk_col=Label._meta.pk.name,
            pred_label_id_col=DataPrediction._meta.get_field('label').column,
            data_table=Data._meta.db_table,
            data_pk_col=Data._meta.pk.name,
            model_table=Model._meta.db_table,
            model_pk_col=Model._meta.pk.name,
            pred_model_id_col=DataPrediction._meta.get_field('model').column,
            trainingset_table=TrainingSet._meta.db_table,
            trainingset_pk_col=TrainingSet._meta.pk.name,
            model_trainingset_id_col=Model._meta.get_field('training_set').column,
            trainingset_setnumber_col=TrainingSet._meta.get_field('set_number').column,
            previous_run=previous_run,
            data_project_id_col=Data._meta.get_field('project').column,
            project_pk=project.pk)

    with connection.cursor() as c:
        result = c.execute(sql)
        data_objs = c.fetchall()

    data = []
    for d in data_objs:
        temp = {
            'Text': escape(d[0]),
            'Label': d[1],
            'Probability': d[2]
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def data_unlabeled_table(request, project_pk):
    """This returns the unlebeled data not in a queue for the skew table

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)

    stuff_in_queue = DataQueue.objects.filter(queue__project=project)
    queued_ids = [queued.data.id for queued in stuff_in_queue]

    recycle_ids = RecycleBin.objects.filter(data__project=project).values_list('data__pk',flat=True)
    unlabeled_data = project.data_set.filter(datalabel__isnull=True).exclude(id__in=queued_ids).exclude(id__in=recycle_ids)
    data = []
    for d in unlabeled_data:
        temp = {
            'Text': escape(d.text),
            'ID':d.id
        }
        data.append(temp)

    return Response({'data': data})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def data_admin_table(request, project_pk):
    """This returns the elements in the admin queue for annotation

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    queue = Queue.objects.filter(project=project,type="admin")

    data_objs = DataQueue.objects.filter(queue=queue)

    data = []
    for d in data_objs:
        temp = {
            'Text': d.data.text,
            'ID': d.data.id,
            'IRR': str(d.data.irr_ind)
        }
        data.append(temp)

    return Response({'data': data})

@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def recycle_bin_table(request, project_pk):
    """This returns the elements in the recycle bin

    Args:
        request: The POST request
        pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)
    data_objs = RecycleBin.objects.filter(data__project=project)

    data = []
    for d in data_objs:
        temp = {
            'Text': d.data.text,
            'ID': d.data.id
        }
        data.append(temp)

    return Response({'data': data})

@api_view(['POST'])
@permission_classes((IsAdminOrCreator, ))
def label_skew_label(request, data_pk):
    """This is called when an admin manually labels a datum on the skew page. It
    annotates a single datum with the given label, and profile with null as the time.

    Args:
        request: The request to the endpoint
        data_pk: Primary key of data
    Returns:
        {}
    """

    datum = Data.objects.get(pk=data_pk)
    project = datum.project
    label = Label.objects.get(pk=request.data['labelID'])
    profile = request.user.profile

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set,
                                time_to_label=None,
                                timestamp = timezone.now())

    return Response({'test':'success'})


@api_view(['POST'])
@permission_classes((IsAdminOrCreator, ))
def label_admin_label(request, data_pk):
    """This is called when an admin manually labels a datum on the admin
    annotation page. It labels a single datum with the given label and profile,
    with null as the time.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    datum = Data.objects.get(pk=data_pk)
    project = datum.project
    label = Label.objects.get(pk=request.data['labelID'])
    profile = request.user.profile

    current_training_set = project.get_current_training_set()

    with transaction.atomic():
        queue = project.queue_set.get(type="admin")
        DataLabel.objects.create(data=datum,
                                label=label,
                                profile=profile,
                                training_set=current_training_set,
                                time_to_label=None,
                                timestamp=timezone.now())

        DataQueue.objects.filter(data=datum, queue=queue).delete()

        #make sure the data is no longer irr
        if datum.irr_ind:
            Data.objects.filter(pk=datum.pk).update(irr_ind=False)

    #NOTE: this checks if the model needs to be triggered, but not if the
    #queues need to be refilled. This is because for something to be in the
    #admin queue, annotate or skip would have already checked for an empty queue
    util.check_and_trigger_model(datum)
    return Response({'test':'success'})


############################################
#    REACT API ENDPOINTS FOR CODING VIEW   #
############################################
@api_view(['GET'])
@permission_classes((IsCoder, ))
def get_card_deck(request, project_pk):
    """Grab data using get_assignments and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
        data: The data in the queue
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # Calculate queue parameters
    batch_size = project.batch_size
    num_coders = len(project.projectpermissions_set.all()) + 1
    coder_size = math.ceil(batch_size / num_coders)

    data = util.get_assignments(profile, project, coder_size)
    #shuffle so the irr is not all at the front
    random.shuffle(data)
    labels = Label.objects.all().filter(project=project)

    return Response({'labels': LabelSerializer(labels, many=True).data, 'data': DataSerializer(data, many=True).data})


@api_view(['GET'])
@permission_classes((IsCoder, ))
def get_label_history(request, project_pk):
    """Grab items previously labeled by this user
    and send it to the frontend react app.

    Args:
        request: The request to the endpoint
        project_pk: Primary key of project
    Returns:
        labels: The project labels
        data: DataLabel objects where that user was the one to label them
    """
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    labels = Label.objects.all().filter(project=project)
    data = DataLabel.objects.filter(profile=profile, data__project=project_pk, label__in=labels)

    data_list = []
    results = []
    for d in data:
        #if it is not labeled irr but is in the log, the data is resolved IRR,
        if not d.data.irr_ind and len(IRRLog.objects.filter(data=d.data)) > 0:
            continue

        data_list.append(d.data.id)
        if d.timestamp:
            if d.timestamp.minute < 10:
                minute = "0" + str(d.timestamp.minute)
            else:
                minute = str(d.timestamp.minute)
            if d.timestamp.second < 10:
                second = "0" + str(d.timestamp.second)
            else:
                second = str(d.timestamp.second)
            new_timestamp = str(d.timestamp.date()) + ", " + str(d.timestamp.hour)\
            + ":" + minute + "." + second
        else:
            new_timestamp = "None"
        temp_dict = {"data":d.data.text,
        "id": d.data.id,"label":d.label.name,
        "labelID": d.label.id ,"timestamp":new_timestamp, "edit": "yes"}
        results.append(temp_dict)

    data_irr = IRRLog.objects.filter(profile=profile, data__project=project_pk, label__isnull=False)

    for d in data_irr:
        #if the data was labeled by that person (they were the admin), don't add
        #it twice
        if d.data.id in data_list:
            continue

        if d.timestamp:
            if d.timestamp.minute < 10:
                minute = "0" + str(d.timestamp.minute)
            else:
                minute = str(d.timestamp.minute)
            if d.timestamp.second < 10:
                second = "0" + str(d.timestamp.second)
            else:
                second = str(d.timestamp.second)
            new_timestamp = str(d.timestamp.date()) + ", " + str(d.timestamp.hour)\
            + ":" + minute + "." + second
        else:
            new_timestamp = "None"
        temp_dict = {"data":d.data.text,
        "id": d.data.id,"label":d.label.name,
        "labelID": d.label.id ,"timestamp":new_timestamp, "edit":"no"}
        results.append(temp_dict)

    return Response({'data': results})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def get_irr_metrics(request, project_pk):
    """This function takes the current coded IRR and calculates several
    reliability metrics

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        {}
    """

    #need to take the IRRLog and pull out exactly the max_labelers amount
    #of labels for each datum
    all_data = []
    project = Project.objects.get(pk=project_pk)
    profile = request.user.profile

    try:
        if project.num_users_irr > 2:
            kappa, perc_agreement = util.fleiss_kappa(project)
        else:
            kappa, perc_agreement = util.cohens_kappa(project)
        kappa = round(kappa,3)
        perc_agreement = str(round(perc_agreement,5)*100)+"%"
    except ValueError:
        kappa = "No irr data processed"
        perc_agreement = "No irr data processed"
    return Response({'kappa':kappa, 'percent agreement':perc_agreement})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def perc_agree_table(request, project_pk):
    '''
    Finds the percent agreement between each pair of coders
    to be displayed on the IRR page as a table
    '''
    project = Project.objects.get(pk=project_pk)
    irr_data = set(IRRLog.objects.filter(data__project=project).values_list('data', flat=True))
    profile = request.user.profile

    if len(irr_data) == 0:
        return Response({'data':[]})

    user_agree = util.perc_agreement_table_data(project)
    return Response({'data':user_agree})


@api_view(['GET'])
@permission_classes((IsAdminOrCreator, ))
def heat_map_data(request, project_pk):
    '''
    Calculates the data for the heat map of irr data and returns the
    correct one for the pair of coders given

    Args:
        request: the GET request with the pk of the two users
        project_pk: the Primary key of the project
    Returns:
        a list of dictionaries of form {label1, label2, count}

    '''
    project = Project.objects.get(pk=project_pk)
    profile = request.user.profile

    heatmap_data = util.irr_heatmap_data(project)
    labels = list(Label.objects.all().filter(project=project).values_list('name',flat=True))
    labels.append("Skip")
    coders = []
    profiles = ProjectPermissions.objects.filter(project=project)
    coders.append({'name':str(project.creator),'pk':project.creator.pk})
    for p in profiles:
        coders.append({'name':str(p.profile), 'pk':p.profile.pk})


    return Response({'data':heatmap_data, 'labels':labels , "coders":coders})


@api_view(['POST'])
@permission_classes((IsCoder, ))
def skip_data(request, data_pk):
    """Take a datum that is in the assigneddata queue for that user
    and place it in the admin queue. Remove it from the
    assignedData queue.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    project = data.project
    queue = project.queue_set.get(type="normal")
    response = {}

    #if the data is IRR or processed IRR, dont add to admin queue yet
    num_history = IRRLog.objects.filter(data=data).count()

    if data.irr_ind or num_history > 0:
        #log the data and check IRR but don't put in admin queue yet
        IRRLog.objects.create(data=data, profile=profile, label = None, timestamp = timezone.now())
        #if the IRR history has more than the needed number of labels , it is
        #already processed so don't do anything else
        #unassign the skipped item
        assignment = AssignedData.objects.get(data=data,profile=profile)
        assignment.delete()
        if num_history <= project.num_users_irr:
            util.process_irr_label(data, None)

    else:
        #if it is normal data, move it to the correct places
        util.move_skipped_to_admin_queue(data, profile, project)

    #for all data, check if we need to refill queue
    util.check_and_trigger_model(data, profile)

    return Response(response)


@api_view(['POST'])
@permission_classes((IsCoder, ))
def annotate_data(request, data_pk):
    """Annotate a single datum which is in the assigneddata queue given the user,
       data_id, and label_id.  This will remove it from assigneddata, remove it
       from dataqueue and add it to labeleddata.  Also check if project is ready
       to have model run, if so start that process.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    project = data.project
    profile = request.user.profile
    response = {}
    label = Label.objects.get(pk=request.data['labelID'])
    labeling_time = request.data['labeling_time']

    num_history = IRRLog.objects.filter(data=data).count()
    #if the IRR history has more than the needed number of labels , it is
    #already processed so just add this label to the history.
    if num_history >= project.num_users_irr:
        IRRLog.objects.create(data=data, profile=profile, label=label, timestamp = timezone.now())
        assignment = AssignedData.objects.get(data=data,profile=profile)
        assignment.delete()
    else:
        util.label_data(label, data, profile, labeling_time)
        if data.irr_ind:
            #if it is reliability data, run processing step
            util.process_irr_label(data, label)

    #for all data, check if we need to refill queue
    util.check_and_trigger_model(data, profile)

    return Response(response)


@api_view(['POST'])
@permission_classes((IsAdminOrCreator, ))
def discard_data(request, data_pk):
    """Move a datum to the RecycleBin. This removes it from
       the admin dataqueue. This is used only in the skew table by the admin.

    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    project = data.project
    response = {}

    # Make sure coder is an admin
    if project_extras.proj_permission_level(data.project, profile) > 1:
        #remove it from the admin queue
        queue = Queue.objects.get(project=project,admin=True)
        DataQueue.objects.get(data=data, queue=queue).delete()

        RecycleBin.objects.create(data=data, timestamp=timezone.now())
    else:
        response['error'] = 'Invalid credentials. Must be an admin.'

    return Response(response)

@api_view(['POST'])
@permission_classes((IsAdminOrCreator, ))
def restore_data(request, data_pk):
    """Move a datum out of the RecycleBin.
    Args:
        request: The POST request
        pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    project = data.project
    response = {}

    # Make sure coder is an admin
    if project_extras.proj_permission_level(data.project, profile) > 1:
        #remove it from the recycle bin
        RecycleBin.objects.get(data=data).delete()
    else:
        response['error'] = 'Invalid credentials. Must be an admin.'

    return Response(response)

@api_view(['POST'])
@permission_classes((IsCoder, ))
def modify_label(request, data_pk):
    """Take a single datum with a label and change the label in the DataLabel table

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}
    project = data.project

    # Make sure coder still has permissions before labeling data
    label = Label.objects.get(pk=request.data['labelID'])
    old_label = Label.objects.get(pk=request.data['oldLabelID'])
    with transaction.atomic():
        DataLabel.objects.filter(data=data, label=old_label).update(label=label,
        time_to_label=0, timestamp=timezone.now())

        LabelChangeLog.objects.create(project=project, data=data, profile=profile,
        old_label=old_label.name, new_label = label.name, change_timestamp = timezone.now())

    return Response(response)


@api_view(['POST'])
@permission_classes((IsCoder, ))
def modify_label_to_skip(request, data_pk):
    """Take a datum that is in the assigneddata queue for that user
    and place it in the admin queue. Remove it from the assignedData queue.

    Args:
        request: The POST request
        data_pk: Primary key of the data
    Returns:
        {}
    """
    data = Data.objects.get(pk=data_pk)
    profile = request.user.profile
    response = {}
    project = data.project
    old_label = Label.objects.get(pk=request.data['oldLabelID'])
    queue = Queue.objects.get(project=project, type="admin")

    with transaction.atomic():
        DataLabel.objects.filter(data=data, label=old_label).delete()
        if data.irr_ind:
            #if it was irr, add it to the log
            if len(IRRLog.objects.filter(data=data,profile=profile)) == 0:
                IRRLog.objects.create(data=data, profile=profile, label = None, timestamp = timezone.now())
        else:
            #if it's not irr, add it to the admin queue immediately
            DataQueue.objects.create(data=data, queue=queue)
        LabelChangeLog.objects.create(project=project, data=data, profile=profile,
        old_label=old_label.name, new_label = "skip", change_timestamp = timezone.now())


    return Response(response)


@api_view(['GET'])
def leave_coding_page(request):
    """API request meant to be sent when a user navigates away from the coding page
       captured with 'beforeunload' event.  This should use assign_data to remove
       any data currently assigned to the user and re-add it to redis

    Args:
        request: The GET request
    Returns:
        {}
    """
    profile = request.user.profile
    assigned_data = AssignedData.objects.filter(profile=profile)

    for assignment in assigned_data:
        util.unassign_datum(assignment.data, profile)

    return Response({})


################################
#    DRF VIEWSET API CLASSES   #
################################

# TODO establish more restrictive permissions
# AuthUsers should be write-only for unauthenticated users
# Creation/update/deletion of certain objects that will be
# managed by the server probably shouldn't be exposed via the API
# (ex. Queues, Models, AssignedData, many-to-many join fields)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().order_by('id')
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AuthUserGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = AuthUserGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AuthUserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.all().order_by('id')
    serializer_class = AuthUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated,)

class CoreModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all().order_by('id')
    serializer_class = CoreModelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataViewSet(viewsets.ModelViewSet):
    queryset = Data.objects.all().order_by('id')
    serializer_class = DataSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SmartPagination

class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all().order_by('id')
    serializer_class = LabelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataLabelViewSet(viewsets.ModelViewSet):
    queryset = DataLabel.objects.all().order_by('id')
    serializer_class = DataLabelSerializer
    permission_classes = (permissions.IsAuthenticated,)

class DataPredictionViewSet(viewsets.ModelViewSet):
    queryset = DataPrediction.objects.all().order_by('id')
    serializer_class = DataPredictionSerializer
    permission_classes = (permissions.IsAuthenticated,)

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all().order_by('id')
    serializer_class = QueueSerializer
    permission_classes = (permissions.IsAuthenticated,)

class AssignedDataViewSet(viewsets.ModelViewSet):
    queryset = AssignedData.objects.all().order_by('id')
    serializer_class = AssignedDataSerializer
    permission_classes = (permissions.IsAuthenticated,)
