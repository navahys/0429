"""
ASGI config for mental_health_project project.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import conversations.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            conversations.routing.websocket_urlpatterns
        )
    ),
})
