# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-27 16:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0032_auto_20180627_1556"),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="active_l_method",
            new_name="learning_method",
        ),
    ]
