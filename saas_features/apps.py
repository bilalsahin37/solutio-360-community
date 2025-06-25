from django.apps import AppConfig


class SaasFeaturesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "saas_features"
    verbose_name = "SaaS Features"

    def ready(self):
        # SaaS signals'ları import et
        try:
            import saas_features.signals
        except ImportError:
            pass
