import warnings

from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, IntegrityError, migrations, router, transaction


class RenameContentType(migrations.RunPython):
    def __init__(self, app_label, old_model, new_model):
        self.app_label = app_label
        self.old_model = old_model
        self.new_model = new_model
        super().__init__(self.rename_forward, self.rename_backward)

    def _rename(self, apps, schema_editor, old_model, new_model):
        pass

    def rename_forward(self, apps, schema_editor):
        pass

    def rename_backward(self, apps, schema_editor):
        pass


def inject_rename_contenttypes_operations(
    plan=None, apps=global_apps, using=DEFAULT_DB_ALIAS, **kwargs
):
    """
    Insert a `RenameContentType` operation after every planned `RenameModel`
    operation.
    """
    pass


def create_contenttypes(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    """
    Create content types for models in the given app.
    """
    pass
