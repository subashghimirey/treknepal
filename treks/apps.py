from django.apps import AppConfig


class TreksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treks'

    def ready(self):
        # register signals
        from . import signals  # noqa: F401
