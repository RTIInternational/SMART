# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-19 17:51
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0041_irrlog_timestamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="irrlog",
            name="label",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="core.Label"
            ),
        ),
    ]
