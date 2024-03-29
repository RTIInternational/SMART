# Generated by Django 3.2.9 on 2023-03-05 19:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0074_externaldatabase_export_verified_only"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="datalabel",
            name="verified",
        ),
        migrations.AddField(
            model_name="datalabel",
            name="pre_loaded",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="VerifiedDataLabel",
            fields=[
                (
                    "data_label",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="verified",
                        serialize=False,
                        to="core.datalabel",
                    ),
                ),
                ("verified_timestamp", models.DateTimeField(default=None, null=True)),
                (
                    "verified_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.profile"
                    ),
                ),
            ],
        ),
    ]
