from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher
from django.template import Library
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext

register = Library()


@register.simple_tag
def render_password_as_hash(value):
    pass
