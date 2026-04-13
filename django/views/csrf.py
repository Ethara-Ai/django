from pathlib import Path

from django.conf import settings
from django.http import HttpResponseForbidden
from django.template import Context, Engine, TemplateDoesNotExist, loader
from django.utils.translation import gettext as _
from django.utils.version import get_docs_version

CSRF_FAILURE_TEMPLATE_NAME = "403_csrf.html"


def builtin_template_path(name):
    """
    Return a path to a builtin template.

    Avoid calling this function at the module level or in a class-definition
    because __file__ may not exist, e.g. in frozen environments.
    """
    return Path(__file__).parent / "templates" / name


def csrf_failure(request, reason="", template_name=CSRF_FAILURE_TEMPLATE_NAME):
    """
    Default view used when request fails CSRF protection
    """
    pass
