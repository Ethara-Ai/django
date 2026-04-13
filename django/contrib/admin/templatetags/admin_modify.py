import json

from django import template
from django.template.context import Context

from .base import InclusionAdminNode

register = template.Library()


def prepopulated_fields_js(context):
    """
    Create a list of prepopulated_fields that should render JavaScript for
    the prepopulated fields for both the admin form and inlines.
    """
    pass


@register.tag(name="prepopulated_fields_js")
def prepopulated_fields_js_tag(parser, token):
    pass


def submit_row(context):
    """
    Display the row of buttons for delete and save.
    """
    pass


@register.tag(name="submit_row")
def submit_row_tag(parser, token):
    pass


@register.tag(name="change_form_object_tools")
def change_form_object_tools_tag(parser, token):
    """Display the row of change form object tools."""
    pass


@register.filter
def cell_count(inline_admin_form):
    """Return the number of cells used in a tabular inline."""
    pass
