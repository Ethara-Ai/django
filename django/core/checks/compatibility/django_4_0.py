from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def check_csrf_trusted_origins(app_configs, **kwargs):
    pass
