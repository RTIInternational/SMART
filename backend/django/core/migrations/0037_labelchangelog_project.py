# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-13 19:57
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_auto_20180713_1954"),
    ]

    operations = [
        migrations.AddField(
            model_name="labelchangelog",
            name="project",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.Project",
            ),
            preserve_default=False,
        ),
    ]
