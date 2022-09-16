from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from . import consumers

# Paths to project-based websockets
websocket_urlpatterns = [
    re_path(r"^projects/(?P<pk>\d+)/code/$", consumers.SMARTConsumer),
]

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
