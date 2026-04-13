from copy import deepcopy

from django.tasks.base import TaskResult, TaskResultStatus
from django.tasks.exceptions import TaskResultDoesNotExist
from django.tasks.signals import task_enqueued
from django.utils import timezone
from django.utils.crypto import get_random_string

from .base import BaseTaskBackend


class DummyBackend(BaseTaskBackend):
    supports_defer = True
    supports_async_task = True
    supports_priority = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.results = []

    def _store_result(self, result):
        pass

    def enqueue(self, task, args, kwargs):
        pass

    def get_result(self, result_id):
        # Results are only scoped to the current thread, hence
        # supports_get_result is False.
        pass

    async def aget_result(self, result_id):
        pass

    def clear(self):
        self.results.clear()
