import pathlib

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.core.cache.backends.filebased import FileBasedCache

from . import Error, Tags, Warning, register

E001 = Error(
    "You must define a '%s' cache in your CACHES setting." % DEFAULT_CACHE_ALIAS,
    id="caches.E001",
)


@register(Tags.caches)
def check_default_cache_is_configured(app_configs, **kwargs):
    pass


@register(Tags.caches, deploy=True)
def check_cache_location_not_exposed(app_configs, **kwargs):
    pass


@register(Tags.caches)
def check_file_based_cache_is_absolute(app_configs, **kwargs):
    pass
