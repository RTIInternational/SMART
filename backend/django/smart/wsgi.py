"""WSGI config for smart project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

from configurations.wsgi import get_wsgi_application

from core.utils.utils_redis import init_redis

init_redis()

application = get_wsgi_application()
