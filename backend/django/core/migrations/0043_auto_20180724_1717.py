# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-24 17:17
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0042_auto_20180719_1751"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="percentage_irr",
            field=models.FloatField(
                default=10.0,
                validators=[
                    django.core.validators.MinValueValidator(0.0),
                    django.core.validators.MaxValueValidator(100.0),
                ],
            ),
        ),
    ]