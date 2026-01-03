"""
Django app configuration for the API module.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'API'
    
    def ready(self):
        """
        Initialize app when Django starts.
        Import signal handlers here if needed.
        """
        pass
