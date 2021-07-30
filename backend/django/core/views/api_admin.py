from django.contrib.postgres.fields import ArrayField
from django.db import connection
from django.db.models import FloatField
from django.utils.html import escape
from postgres_stats.aggregates import Percentile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.models import (
    Data,
    DataLabel,
    DataPrediction,
    IRRLog,
    Label,
    Model,
    Project,
    ProjectPermissions,
    TrainingSet,
)
from core.permissions import IsAdminOrCreator
from core.utils.util import irr_heatmap_data, perc_agreement_table_data
from core.utils.utils_model import cohens_kappa, fleiss_kappa


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def label_distribution(request, project_pk):
    """This function finds and returns the number of each label per user. This is used
    by a graph on the front end admin page.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of the amount of labels per person per type
    """
    project = Project.objects.get(pk=project_pk)
    labels = [label for label in project.labels.all()]
    users = []
    users.append(project.creator)
    users.extend([perm.profile for perm in project.projectpermissions_set.all()])

    # Sort labels by the count
    labels.sort(
        key=lambda label: DataLabel.objects.filter(label=label).count(), reverse=True
    )

    dataset = []
    # Get first labels
    for label in labels[0:5]:
        temp_values = []
        for u in users:
            label_count = DataLabel.objects.filter(profile=u, label=label).count()
            if label_count > 0:
                temp_values.append({"x": u.__str__(), "y": label_count})
        if temp_values != []:
            dataset.append({"key": label.name, "values": temp_values})

    other_values = []
    for u in users:
        other_count = 0
        for label in labels[5:]:
            other_count += DataLabel.objects.filter(profile=u, label=label).count()
        if other_count > 0:
            other_values.append({"x": u.__str__(), "y": other_count})
    if other_values != []:
        dataset.append({"key": "other labels", "values": other_values})

    return Response(dataset)


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def label_timing(request, project_pk):
    """This function finds and returns the requested label time metrics. This is used by
    the graphs on the admin page to show how long each labeler is taking.

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
        result = DataLabel.objects.filter(
            data__project=project_pk, profile=u
        ).aggregate(
            quartiles=Percentile(
                "time_to_label",
                [0.05, 0.25, 0.5, 0.75, 0.95],
                continuous=False,
                output_field=ArrayField(FloatField()),
            )
        )

        if result["quartiles"]:
            if result["quartiles"][4] > yDomain:
                yDomain = result["quartiles"][4] + 10
            temp = {
                "label": u.__str__(),
                "values": {
                    "Q1": result["quartiles"][1],
                    "Q2": result["quartiles"][2],
                    "Q3": result["quartiles"][3],
                    "whisker_low": result["quartiles"][0],
                    "whisker_high": result["quartiles"][4],
                },
            }
            dataset.append(temp)

    return Response({"data": dataset, "yDomain": yDomain})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def model_metrics(request, project_pk):
    """This function finds and returns the requested metrics.

    This is
    used by the graphs on the front end admin page.
    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        a dictionary of model metric information
    """
    metric = request.GET.get("metric", "accuracy")

    project = Project.objects.get(pk=project_pk)
    models = Model.objects.filter(project=project).order_by("training_set__set_number")

    if metric == "accuracy":
        values = []
        for model in models:
            values.append({"x": model.training_set.set_number, "y": model.cv_accuracy})

        dataset = [{"key": "Accuracy", "values": values}]
    else:
        labels = {str(label.pk): label.name for label in project.labels.all()}
        dataset = []
        for label in labels:
            values = []
            for model in models:
                current_metric = model.cv_metrics[metric][label]
                values.append({"x": model.training_set.set_number, "y": current_metric})
            dataset.append({"key": labels[label], "values": values})

    return Response(dataset)


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def data_coded_table(request, project_pk):
    """This returns the labeled data.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        data: a list of data information
    """
    project = Project.objects.get(pk=project_pk)

    data_objs = DataLabel.objects.filter(data__project=project, data__irr_ind=False)

    data = []
    for d in data_objs:
        temp = {
            "Text": escape(d.data.text),
            "Label": d.label.name,
            "Coder": d.profile.__str__(),
        }
        data.append(temp)

    return Response({"data": data})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def data_predicted_table(request, project_pk):
    """This returns the predictions for the unlabeled data.

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
        data_text_col=Data._meta.get_field("text").column,
        label_name_col=Label._meta.get_field("name").column,
        pred_prob_col=DataPrediction._meta.get_field("predicted_probability").column,
        pred_data_id_col=DataPrediction._meta.get_field("data").column,
        pred_table=DataPrediction._meta.db_table,
        label_table=Label._meta.db_table,
        label_pk_col=Label._meta.pk.name,
        pred_label_id_col=DataPrediction._meta.get_field("label").column,
        data_table=Data._meta.db_table,
        data_pk_col=Data._meta.pk.name,
        model_table=Model._meta.db_table,
        model_pk_col=Model._meta.pk.name,
        pred_model_id_col=DataPrediction._meta.get_field("model").column,
        trainingset_table=TrainingSet._meta.db_table,
        trainingset_pk_col=TrainingSet._meta.pk.name,
        model_trainingset_id_col=Model._meta.get_field("training_set").column,
        trainingset_setnumber_col=TrainingSet._meta.get_field("set_number").column,
        previous_run=previous_run,
        data_project_id_col=Data._meta.get_field("project").column,
        project_pk=project.pk,
    )

    with connection.cursor() as c:
        c.execute(sql)
        data_objs = c.fetchall()

    data = []
    for d in data_objs:
        temp = {"Text": escape(d[0]), "Label": d[1], "Probability": d[2]}
        data.append(temp)

    return Response({"data": data})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def get_irr_metrics(request, project_pk):
    """This function takes the current coded IRR and calculates several reliability
    metrics.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        {}
    """

    # need to take the IRRLog and pull out exactly the max_labelers amount
    # of labels for each datum
    project = Project.objects.get(pk=project_pk)

    try:
        if project.num_users_irr > 2:
            kappa, perc_agreement = fleiss_kappa(project)
        else:
            kappa, perc_agreement = cohens_kappa(project)
        kappa = round(kappa, 3)
        perc_agreement = str(round(perc_agreement, 5) * 100) + "%"
    except ValueError:
        kappa = "No irr data processed"
        perc_agreement = "No irr data processed"
    return Response({"kappa": kappa, "percent agreement": perc_agreement})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def perc_agree_table(request, project_pk):
    """Finds the percent agreement between each pair of coders to be displayed on the
    IRR page as a table."""
    project = Project.objects.get(pk=project_pk)
    irr_data = set(
        IRRLog.objects.filter(data__project=project).values_list("data", flat=True)
    )

    if len(irr_data) == 0:
        return Response({"data": []})

    user_agree = perc_agreement_table_data(project)
    return Response({"data": user_agree})


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def heat_map_data(request, project_pk):
    """Calculates the data for the heat map of irr data and returns the correct one for
    the pair of coders given.

    Args:
        request: the GET request with the pk of the two users
        project_pk: the Primary key of the project
    Returns:
        a list of dictionaries of form {label1, label2, count}
    """
    project = Project.objects.get(pk=project_pk)

    heatmap_data = irr_heatmap_data(project)
    labels = list(
        Label.objects.all().filter(project=project).values_list("name", flat=True)
    )
    labels.append("Skip")
    coders = []
    profiles = ProjectPermissions.objects.filter(project=project)
    coders.append({"name": str(project.creator), "pk": project.creator.pk})
    for p in profiles:
        coders.append({"name": str(p.profile), "pk": p.profile.pk})

    return Response({"data": heatmap_data, "labels": labels, "coders": coders})
