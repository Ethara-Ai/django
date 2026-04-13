from abc import ABCMeta, abstractmethod
from inspect import iscoroutinefunction

from asgiref.sync import sync_to_async

from django.conf import settings
from django.tasks import DEFAULT_TASK_QUEUE_NAME
from django.tasks.base import (
    DEFAULT_TASK_PRIORITY,
    TASK_MAX_PRIORITY,
    TASK_MIN_PRIORITY,
    Task,
)
from django.tasks.exceptions import InvalidTask
from django.utils import timezone
from django.utils.inspect import get_func_args, is_module_level_function


class BaseTaskBackend(metaclass=ABCMeta):
    task_class = Task

    # Does the backend support Tasks to be enqueued with the run_after
    # attribute?
    supports_defer = False

    # Does the backend support coroutines to be enqueued?
    supports_async_task = False

    # Does the backend support results being retrieved (from any
    # thread/process)?
    supports_get_result = False

    # Does the backend support executing Tasks in a given
    # priority order?
    supports_priority = False

    def __init__(self, alias, params):
        self.alias = alias
        self.queues = set(params.get("QUEUES", [DEFAULT_TASK_QUEUE_NAME]))
        self.options = params.get("OPTIONS", {})

    def validate_task(self, task):
        """
        Determine whether the provided Task can be executed by the backend.
        """
        pass

    @abstractmethod
    def enqueue(self, task, args, kwargs):
        """Queue up a task to be executed."""

    async def aenqueue(self, task, args, kwargs):
        """Queue up a task function (or coroutine) to be executed."""
        pass

    def get_result(self, result_id):
        """
        Retrieve a task result by id.

        Raise TaskResultDoesNotExist if such result does not exist.
        """
        raise NotImplementedError(
            "This backend does not support retrieving or refreshing results."
        )

    async def aget_result(self, result_id):
        """See get_result()."""
        pass

    def check(self, **kwargs):
        return []
