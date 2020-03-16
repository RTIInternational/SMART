from django.core.management.base import BaseCommand

from core.utils.utils_redis import init_redis


class Command(BaseCommand):
    help = "Syncs Redis with the current state of the database"

    def handle(self, *args, **options):
        init_redis()
