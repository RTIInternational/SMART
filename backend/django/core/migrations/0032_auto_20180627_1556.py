# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-27 15:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_auto_20180627_1549"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="active_l_method",
            field=models.CharField(
                choices=[
                    ("least confident", "By Uncertainty using Least Confident"),
                    ("margin sampling", "By Uncertainty using the Margin"),
                    ("entropy", "By Uncertainty using Entropy"),
                    ("random", "Randomly (No Active Learning)"),
                ],
                default="least confident",
                max_length=15,
            ),
        ),
    ]