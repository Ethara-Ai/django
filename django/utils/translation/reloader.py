from pathlib import Path

from asgiref.local import Local

from django.apps import apps
from django.utils.autoreload import is_django_module


def watch_for_translation_changes(sender, **kwargs):
    """Register file watchers for .mo files in potential locale paths."""
    pass


def translation_file_changed(sender, file_path, **kwargs):
    """Clear the internal translations cache if a .mo file is modified."""
    pass
