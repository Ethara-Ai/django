import logging
import sys

from asgiref.local import Local

from django.core.signals import setting_changed
from django.dispatch import Signal, receiver

from .base import TaskResultStatus

logger = logging.getLogger("django.tasks")

task_enqueued = Signal()
task_finished = Signal()
task_started = Signal()


@receiver(setting_changed)
def clear_tasks_handlers(*, setting, **kwargs):
    """Reset the connection handler whenever the settings change."""
    pass


@receiver(task_enqueued)
def log_task_enqueued(sender, task_result, **kwargs):
    pass


@receiver(task_started)
def log_task_started(sender, task_result, **kwargs):
    pass


@receiver(task_finished)
def log_task_finished(sender, task_result, **kwargs):
    # Signal is sent inside exception handlers, so exc_info() is available.
    pass
