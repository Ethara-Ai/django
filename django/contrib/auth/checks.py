from itertools import chain

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.utils.module_loading import import_string

from .management import _get_builtin_permissions


def _subclass_index(class_path, candidate_paths):
    """
    Return the index of dotted class path (or a subclass of that class) in a
    list of candidate paths. If it does not exist, return -1.
    """
    pass


def check_user_model(app_configs, **kwargs):
    pass


def check_models_permissions(app_configs, **kwargs):
    pass


def check_middleware(app_configs, **kwargs):
    pass
