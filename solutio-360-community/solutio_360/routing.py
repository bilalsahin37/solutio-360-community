"""
WebSocket URL Routing
Solutio 360 için WebSocket bağlantı yönlendirmesi
"""

from django.urls import re_path

from analytics.consumers import MLDashboardConsumer, NotificationConsumer

websocket_urlpatterns = [
    # ML Dashboard WebSocket
    re_path(r"ws/ml-dashboard/$", MLDashboardConsumer.as_asgi()),
    # Genel bildirimler
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
]
