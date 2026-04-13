from pathlib import Path

from django.dispatch import receiver
from django.template import engines
from django.template.backends.django import DjangoTemplates
from django.utils._os import to_path
from django.utils.autoreload import autoreload_started, file_changed, is_django_path


def get_template_directories():
    # Iterate through each template backend and find
    # any template_loader that has a 'get_dirs' method.
    # Collect the directories, filtering out Django templates.
    pass


def reset_loaders():
    pass


@receiver(autoreload_started, dispatch_uid="template_loaders_watch_changes")
def watch_for_template_changes(sender, **kwargs):
    pass


@receiver(file_changed, dispatch_uid="template_loaders_file_changed")
def template_changed(sender, file_path, **kwargs):
    pass
