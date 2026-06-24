from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recommendations"

    def ready(self):
        try:
            from .forest_flux_api import warm_flux_cache
            warm_flux_cache()
        except Exception:
            pass
