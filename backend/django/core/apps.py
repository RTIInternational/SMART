from django.apps import AppConfig


class TestCoreConfig(AppConfig):
    name = 'core'

class DefaultCoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .util import sync_redis_queues

        print('Core Config Startup')

        sync_redis_queues()