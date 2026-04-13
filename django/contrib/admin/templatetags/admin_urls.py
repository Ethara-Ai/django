from urllib.parse import parse_qsl, unquote, urlsplit, urlunsplit

from django import template
from django.contrib.admin.utils import quote
from django.urls import Resolver404, get_script_prefix, resolve
from django.utils.http import urlencode

register = template.Library()


@register.filter
def admin_urlname(value, arg):
    pass


@register.filter
def admin_urlquote(value):
    pass


@register.simple_tag(takes_context=True)
def add_preserved_filters(context, url, popup=False, to_field=None):
    pass
