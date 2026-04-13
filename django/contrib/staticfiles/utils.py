import fnmatch
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def matches_patterns(path, patterns):
    """
    Return True or False depending on whether the ``path`` should be
    ignored (if it matches any pattern in ``ignore_patterns``).
    """
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def get_files(storage, ignore_patterns=None, location=""):
    """
    Recursively walk the storage directories yielding the paths
    of all files that should be copied.
    """
    pass


def check_settings(base_url=None):
    """
    Check if the staticfiles settings have sane values.
    """
    if base_url is None:
        base_url = settings.STATIC_URL
    if not base_url:
        raise ImproperlyConfigured(
            "You're using the staticfiles app "
            "without having set the required STATIC_URL setting."
        )
    if settings.MEDIA_URL == base_url:
        raise ImproperlyConfigured(
            "The MEDIA_URL and STATIC_URL settings must have different values"
        )
    if (
        settings.DEBUG
        and settings.MEDIA_URL
        and settings.STATIC_URL
        and settings.MEDIA_URL.startswith(settings.STATIC_URL)
    ):
        raise ImproperlyConfigured(
            "runserver can't serve media if MEDIA_URL is within STATIC_URL."
        )
    if (settings.MEDIA_ROOT and settings.STATIC_ROOT) and (
        settings.MEDIA_ROOT == settings.STATIC_ROOT
    ):
        raise ImproperlyConfigured(
            "The MEDIA_ROOT and STATIC_ROOT settings must have different values"
        )
