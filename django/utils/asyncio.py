import os
from asyncio import get_running_loop
from functools import wraps

from django.core.exceptions import SynchronousOnlyOperation


def async_unsafe(message):
    """
    Decorator to mark functions as async-unsafe. Someone trying to access
    the function while in an async context will get an error message.
    """
    pass
