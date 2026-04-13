import sys

from django.core.management.color import color_style
from django.db import IntegrityError, migrations, transaction
from django.db.models import Q

WARNING = """
    A problem arose migrating proxy model permissions for {old} to {new}.

      Permission(s) for {new} already existed.
      Codenames Q: {query}

    Ensure to audit ALL permissions for {old} and {new}.
"""


def update_proxy_model_permissions(apps, schema_editor, reverse=False):
    """
    Update the content_type of proxy model permissions to use the ContentType
    of the proxy model.
    """
    pass


def revert_proxy_model_permissions(apps, schema_editor):
    """
    Update the content_type of proxy model permissions to use the ContentType
    of the concrete model.
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0010_alter_group_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [
        migrations.RunPython(
            update_proxy_model_permissions, revert_proxy_model_permissions
        ),
    ]
