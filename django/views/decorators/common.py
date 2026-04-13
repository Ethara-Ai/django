from functools import wraps
from inspect import iscoroutinefunction


def no_append_slash(view_func):
    """
    Mark a view function as excluded from CommonMiddleware's APPEND_SLASH
    redirection.
    """

    # view_func.should_append_slash = False would also work, but decorators are
    # nicer if they don't have side effects, so return a new function.

    if iscoroutinefunction(view_func):

        async def _view_wrapper(request, *args, **kwargs):
            pass

    else:

        def _view_wrapper(request, *args, **kwargs):
            pass

    _view_wrapper.should_append_slash = False

    return wraps(view_func)(_view_wrapper)
