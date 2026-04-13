from django.core import checks


@checks.register
def check_tasks(app_configs=None, **kwargs):
    """Checks all registered Task backends."""
    pass
