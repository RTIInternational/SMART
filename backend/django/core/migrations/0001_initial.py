# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-19 20:05
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Data",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="DataLabel",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.TextField()),
                (
                    "data",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Data"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataPrediction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("predicted_class", models.TextField()),
                ("predicted_probability", models.FloatField()),
                (
                    "data",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Data"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataQueue",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "data",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Data"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Model",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "pickle_path",
                    models.FilePathField(
                        path="/Users/jnance/projects/smart/django/smart/models"
                    ),
                ),
                (
                    "predictions",
                    models.ManyToManyField(
                        related_name="models",
                        through="core.DataPrediction",
                        to="core.Data",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Queue",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("length", models.IntegerField()),
                (
                    "data",
                    models.ManyToManyField(
                        related_name="queues", through="core.DataQueue", to="core.Data"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.Project"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "auth_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "labels",
                    models.ManyToManyField(
                        related_name="labelers",
                        through="core.DataLabel",
                        to="core.Data",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="queue",
            name="user",
            field=models.ForeignKey(
                blank=True, on_delete=django.db.models.deletion.CASCADE, to="core.User"
            ),
        ),
        migrations.AddField(
            model_name="model",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.Project"
            ),
        ),
        migrations.AddField(
            model_name="dataqueue",
            name="queue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.Queue"
            ),
        ),
        migrations.AddField(
            model_name="dataprediction",
            name="model",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.Model"
            ),
        ),
        migrations.AddField(
            model_name="datalabel",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.User"
            ),
        ),
        migrations.AddField(
            model_name="data",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.Project"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="dataqueue",
            unique_together=set([("queue", "data")]),
        ),
        migrations.AlterUniqueTogether(
            name="dataprediction",
            unique_together=set([("data", "model")]),
        ),
        migrations.AlterUniqueTogether(
            name="datalabel",
            unique_together=set([("data", "user")]),
        ),
    ]