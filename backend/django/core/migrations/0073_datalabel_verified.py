# Generated by Django 3.2.9 on 2022-12-16 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0072_externaldatabase_cron_export"),
    ]

    operations = [
        migrations.AddField(
            model_name="datalabel",
            name="verified",
            field=models.BooleanField(default=True),
        ),
    ]