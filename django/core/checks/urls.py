from collections import Counter

from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.utils.inspect import signature

from . import Error, Tags, Warning, register


@register(Tags.urls)
def check_url_config(app_configs, **kwargs):
    pass


def check_resolver(resolver):
    """
    Recursively check the resolver.
    """
    check_method = getattr(resolver, "check", None)
    if check_method is not None:
        return check_method()
    elif not hasattr(resolver, "resolve"):
        return get_warning_for_invalid_pattern(resolver)
    else:
        return []


@register(Tags.urls)
def check_url_namespaces_unique(app_configs, **kwargs):
    """
    Warn if URL namespaces used in applications aren't unique.
    """
    pass


def _load_all_namespaces(resolver, parents=()):
    """
    Recursively load all namespaces from URL patterns.
    """
    pass


def get_warning_for_invalid_pattern(pattern):
    """
    Return a list containing a warning that the pattern is invalid.

    describe_pattern() cannot be used here, because we cannot rely on the
    urlpattern having regex or name attributes.
    """
    if isinstance(pattern, str):
        hint = (
            "Try removing the string '{}'. The list of urlpatterns should not "
            "have a prefix string as the first element.".format(pattern)
        )
    elif isinstance(pattern, tuple):
        hint = "Try using path() instead of a tuple."
    else:
        hint = None

    return [
        Error(
            "Your URL pattern {!r} is invalid. Ensure that urlpatterns is a list "
            "of path() and/or re_path() instances.".format(pattern),
            hint=hint,
            id="urls.E004",
        )
    ]


@register(Tags.urls)
def check_url_settings(app_configs, **kwargs):
    pass


def E006(name):
    pass


@register(Tags.urls)
def check_custom_error_handlers(app_configs, **kwargs):
    pass
