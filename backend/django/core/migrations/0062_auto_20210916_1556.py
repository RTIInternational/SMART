# Generated by Django 3.2.3 on 2021-09-16 15:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0061_merge_20210915_1627"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="datalabelsimilaritypairs",
            options={"ordering": ["-similarity_score"]},
        ),
        migrations.AddField(
            model_name="project",
            name="is_umbrella",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="umbrella_project",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.project",
            ),
        ),
    ]
