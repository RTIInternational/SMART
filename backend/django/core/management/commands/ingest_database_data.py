from django.core.management.base import BaseCommand

from core.models import ExternalDatabase, Project
from core.utils.utils_external_db import load_ingest_table


class Command(BaseCommand):
    help = "Pulls any new data from the ingest database table."

    def handle(self, *args, **kwargs):
        ingest_projects = ExternalDatabase.objects.filter(cron_ingest=True).values_list(
            flat=True
        )
        if len(ingest_projects) == 0:
            print("No projects have cron_ingest set to True.")
        for pk in ingest_projects:
            print("Ingesting project", pk)
            project = Project.objects.get(pk=pk)
            response = {}
            response = load_ingest_table(project, response)
            if "num_added" in response:
                print("Imported", response["num_added"], "new items")
            if "error" in response:
                print(response["error"])
