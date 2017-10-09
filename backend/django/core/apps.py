from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .util import sync_redis_queues


        print('configstartup')

        sync_redis_queues()