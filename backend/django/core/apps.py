from django.apps import AppConfig


class TestCoreConfig(AppConfig):
    name = 'core'

class DefaultCoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .util import init_redis_queues

        print('Core Config Startup')

        init_redis_queues()