from django.core.management.base import BaseCommand

from core.models import Project
from core.utils.utils_external_db import load_ingest_table


class Command(BaseCommand):
    help = "Pulls any new data from the ingest database table."

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            type=int,
            help="The project ID to pull for.",
        )

    def handle(self, *args, **kwargs):
        response = {}
        pk = int(kwargs["pk"])
        try:
            project = Project.objects.get(pk=pk)
            response = load_ingest_table(project, response)
            if "num_added" in response:
                print("Imported", response["num_added"], "new items")
            if "error" in response:
                print(response["error"])
        except Project.DoesNotExist:
            print("PK:", pk, "does not exist")
