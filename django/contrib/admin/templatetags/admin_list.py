import datetime

from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import (
    display_for_field,
    display_for_value,
    get_fields_from_path,
    label_for_field,
    lookup_field,
)
from django.contrib.admin.views.main import (
    ALL_VAR,
    IS_FACETS_VAR,
    IS_POPUP_VAR,
    ORDER_VAR,
    PAGE_VAR,
    SEARCH_VAR,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.template import Library
from django.template.loader import get_template
from django.templatetags.static import static
from django.urls import NoReverseMatch
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from .base import InclusionAdminNode

register = Library()


@register.simple_tag
def paginator_number(cl, i):
    """
    Generate an individual page index link in a paginated list.
    """
    pass


def pagination(cl):
    """
    Generate the series of links to the pages in a paginated list.
    """
    pass


@register.tag(name="pagination")
def pagination_tag(parser, token):
    pass


def result_headers(cl):
    """
    Generate the list column headers.
    """
    pass


def _boolean_icon(field_val):
    pass


def _coerce_field_name(field_name, field_index):
    """
    Coerce a field_name (which may be a callable) to a string.
    """
    pass


def items_for_result(cl, result, form):
    """
    Generate the actual list of data.
    """
    pass


class ResultList(list):
    """
    Wrapper class used to return items in a list_editable changelist, annotated
    with the form object for error reporting purposes. Needed to maintain
    backwards compatibility with existing admin templates.
    """

    def __init__(self, form, *items):
        self.form = form
        super().__init__(*items)


def results(cl):
    pass


def result_hidden_fields(cl):
    pass


def result_list(cl):
    """
    Display the headers and data list together.
    """
    pass


@register.tag(name="result_list")
def result_list_tag(parser, token):
    pass


def date_hierarchy(cl):
    """
    Display the date hierarchy for date drill-down functionality.
    """
    pass


@register.tag(name="date_hierarchy")
def date_hierarchy_tag(parser, token):
    pass


def search_form(cl):
    """
    Display a search form for searching the list.
    """
    pass


@register.tag(name="search_form")
def search_form_tag(parser, token):
    pass


@register.simple_tag
def admin_list_filter(cl, spec):
    pass


def admin_actions(context):
    """
    Track the number of times the action field has been rendered on the page,
    so we know which value to use.
    """
    pass


@register.tag(name="admin_actions")
def admin_actions_tag(parser, token):
    pass


@register.tag(name="change_list_object_tools")
def change_list_object_tools_tag(parser, token):
    """Display the row of change list object tools."""
    pass
