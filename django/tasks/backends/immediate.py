import logging
from traceback import format_exception

from django.tasks.base import TaskContext, TaskError, TaskResult, TaskResultStatus
from django.tasks.signals import task_enqueued, task_finished, task_started
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.json import normalize_json

from .base import BaseTaskBackend

logger = logging.getLogger(__name__)


class ImmediateBackend(BaseTaskBackend):
    supports_async_task = True
    supports_priority = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.worker_id = get_random_string(32)

    def _execute_task(self, task_result):
        """
        Execute the Task for the given TaskResult, mutating it with the
        outcome.
        """
        pass

    def enqueue(self, task, args, kwargs):
        pass
