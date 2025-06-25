from django.apps import AppConfig


class ComplaintsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "complaints"
    verbose_name = "Şikayetler"

    def ready(self):
        """
        App hazır olduğunda signal'ları import et
        """
        try:
            from . import signals
        except ImportError:
            pass
