from django.conf import STATICFILES_STORAGE_ALIAS, settings
from django.contrib.staticfiles.finders import get_finders
from django.core.checks import Error

E005 = Error(
    f"The STORAGES setting must define a '{STATICFILES_STORAGE_ALIAS}' storage.",
    id="staticfiles.E005",
)


def check_finders(app_configs, **kwargs):
    """Check all registered staticfiles finders."""
    pass


def check_storages(app_configs, **kwargs):
    """Ensure staticfiles is defined in STORAGES setting."""
    pass
