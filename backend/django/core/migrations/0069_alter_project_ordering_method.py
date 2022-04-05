# Generated by Django 3.2.9 on 2022-04-04 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0068_auto_20220401_1857"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="ordering_method",
            field=models.CharField(
                choices=[
                    ("random", "Randomly"),
                    ("newest", "By date added to SMART - newest first"),
                    ("oldest", "By date added to SMART - oldest first"),
                    (
                        "least confident",
                        "By Uncertainty using Least Confident (Active Learning)",
                    ),
                    (
                        "margin sampling",
                        "By Uncertainty using the Margin (Active Learning)",
                    ),
                    ("entropy", "By Uncertainty using Entropy (Active Learning)"),
                ],
                default="least confident",
                max_length=15,
            ),
        ),
    ]
