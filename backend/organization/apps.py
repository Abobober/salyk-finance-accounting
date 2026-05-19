from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    name = 'organization'

    def ready(self):
        import organization.signals  # noqa: F401
        try:
            # Autoload tax offices from Excel on app startup if present
            from . import autoload_tax_offices

            autoload_tax_offices.try_autoload()
        except Exception:
            # Keep startup resilient; failures are logged inside the module
            pass
