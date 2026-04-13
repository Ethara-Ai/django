"""
A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the 'context_processors' option of the configuration
of a DjangoTemplates backend and used by RequestContext.
"""

import itertools

from django.conf import settings
from django.middleware.csp import get_nonce
from django.middleware.csrf import get_token
from django.utils.functional import SimpleLazyObject, lazy


def csrf(request):
    """
    Context processor that provides a CSRF token, or the string 'NOTPROVIDED'
    if it has not been provided by either a view decorator or the middleware
    """
    pass


def debug(request):
    """
    Return context variables helpful for debugging.
    """
    context_extras = {}
    if settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS:
        context_extras["debug"] = True
        from django.db import connections

        # Return a lazy reference that computes connection.queries on access,
        # to ensure it contains queries triggered after this function runs.
        context_extras["sql_queries"] = lazy(
            lambda: list(
                itertools.chain.from_iterable(
                    connections[x].queries for x in connections
                )
            ),
            list,
        )
    return context_extras


def i18n(request):
    pass


def tz(request):
    pass


def static(request):
    """
    Add static-related context variables to the context.
    """
    return {"STATIC_URL": settings.STATIC_URL}


def media(request):
    """
    Add media-related context variables to the context.
    """
    pass


def request(request):
    return {"request": request}


def csp(request):
    """
    Add the CSP nonce to the context.
    """
    pass
