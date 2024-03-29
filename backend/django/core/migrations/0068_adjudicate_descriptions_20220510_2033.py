# Generated by Django 3.2.9 on 2022-05-10 20:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0067_merge_20220216_1953"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="label",
            options={"ordering": ("id",)},
        ),
        migrations.AlterModelOptions(
            name="labelembeddings",
            options={"ordering": ("label_id",)},
        ),
        migrations.CreateModel(
            name="AdjudicateDescription",
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
                ("message", models.TextField()),
                ("isResolved", models.BooleanField(default=False)),
                (
                    "data",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.data"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.project"
                    ),
                ),
            ],
        ),
    ]
