import functools
from collections import Counter
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from django.utils.module_loading import import_string


class InvalidTemplateEngineError(ImproperlyConfigured):
    pass


class EngineHandler:
    def __init__(self, templates=None):
        """
        templates is an optional list of template engine definitions
        (structured like settings.TEMPLATES).
        """
        self._templates = templates
        self._engines = {}

    @cached_property
    def templates(self):
        pass

    def __getitem__(self, alias):
        try:
            return self._engines[alias]
        except KeyError:
            try:
                params = self.templates[alias]
            except KeyError:
                raise InvalidTemplateEngineError(
                    "Could not find config for '{}' "
                    "in settings.TEMPLATES".format(alias)
                )

            # If importing or initializing the backend raises an exception,
            # self._engines[alias] isn't set and this code may get executed
            # again, so we must preserve the original params. See #24265.
            params = params.copy()
            backend = params.pop("BACKEND")
            engine_cls = import_string(backend)
            engine = engine_cls(params)

            self._engines[alias] = engine
            return engine

    def __iter__(self):
        return iter(self.templates)

    def all(self):
        pass


@functools.lru_cache
def get_app_template_dirs(dirname):
    """
    Return an iterable of paths of directories to load app templates from.

    dirname is the name of the subdirectory containing templates inside
    installed applications.
    """
    # Immutable return value because it will be cached and shared by callers.
    return tuple(
        path
        for app_config in apps.get_app_configs()
        if app_config.path and (path := Path(app_config.path) / dirname).is_dir()
    )
