# Generated by Django 3.2.9 on 2022-07-25 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0069_merge_20220628_1849"),
    ]

    operations = [
        migrations.AddField(
            model_name="adminprogress",
            name="last_action",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
