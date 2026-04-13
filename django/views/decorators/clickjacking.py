from functools import wraps
from inspect import iscoroutinefunction


def xframe_options_deny(view_func):
    """
    Modify a view function so its response has the X-Frame-Options HTTP
    header set to 'DENY' as long as the response doesn't already have that
    header set. Usage:

    @xframe_options_deny
    def some_view(request):
        ...
    """
    pass


def xframe_options_sameorigin(view_func):
    """
    Modify a view function so its response has the X-Frame-Options HTTP
    header set to 'SAMEORIGIN' as long as the response doesn't already have
    that header set. Usage:

    @xframe_options_sameorigin
    def some_view(request):
        ...
    """
    pass


def xframe_options_exempt(view_func):
    """
    Modify a view function by setting a response variable that instructs
    XFrameOptionsMiddleware to NOT set the X-Frame-Options HTTP header. Usage:

    @xframe_options_exempt
    def some_view(request):
        ...
    """
    pass
