# Generated by Django 3.2.3 on 2021-09-12 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0058_project_dedup_on"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="dedup_fields",
            field=models.CharField(default="", max_length=50, null=True),
        ),
    ]
