from django.core.management.base import BaseCommand

from core.models import ExternalDatabase
from core.utils.utils_external_db import export_table


class Command(BaseCommand):
    help = "Export all data to the export database table."

    def handle(self, *args, **kwargs):
        export_projects = ExternalDatabase.objects.filter(cron_export=True).values_list(
            "project_id", flat=True
        )
        if len(export_projects) == 0:
            print("No projects have cron_export set to True.")
        for pk in export_projects:
            print("Exporting project", pk)
            try:
                response = {}
                export_table(pk, response)
                if "success_message" in response:
                    print(response["success_message"])
                if "error" in response:
                    print(response["error"])
            except Exception as e:
                print("ERROR:", e)
