"""
Creates the default Site object.
"""

from django.apps import apps as global_apps
from django.conf import settings
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, router


def create_default_site(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    pass
