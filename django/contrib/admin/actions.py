"""
Built-in, globally-available admin actions.
"""

from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.decorators import action
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy


@action(
    permissions=["delete"],
    description=gettext_lazy("Delete selected %(verbose_name_plural)s"),
)
def delete_selected(modeladmin, request, queryset):
    """
    Default action which deletes the selected objects.

    This action first displays a confirmation page which shows all the
    deletable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change
    list.
    """
    pass
