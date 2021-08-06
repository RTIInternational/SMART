# Generated by Django 3.2.3 on 2021-08-05 18:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0053_metadata_metadatafield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="metadata",
            name="data",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="metadata",
                to="core.data",
            ),
        ),
    ]
