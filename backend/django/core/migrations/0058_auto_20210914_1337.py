# Generated by Django 3.2.3 on 2021-09-14 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0057_datalabelsimilaritypairs"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="datalabelsimilaritypairs",
            options={"ordering": ["-similarity_score"]},
        ),
        migrations.AlterField(
            model_name="datalabelsimilaritypairs",
            name="similarity_score",
            field=models.FloatField(),
        ),
    ]
