from django.urls import include, path

from . import views

app_name = "api"

urlpatterns = [
    # Bildirim API'leri
    path("notifications/", views.get_notifications, name="notifications"),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
    # Global arama
    path("search/", views.search_global, name="search_global"),
    # 🆓 FREE AI Provider Management APIs
    path("ai/", include("analytics.urls")),
    # 💬 Simple Chat API
    path("chat/", views.simple_chat_api, name="simple_chat"),
]
