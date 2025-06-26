"""
ASGI config for solutio_360 project.
WebSocket desteği ile güncellenmiş ASGI yapılandırması

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")

# Django ASGI application'ını al
django_asgi_app = get_asgi_application()

# WebSocket routing'ini import et
from .routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # HTTP istekleri için Django
        "http": django_asgi_app,
        # WebSocket istekleri için Channels
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
