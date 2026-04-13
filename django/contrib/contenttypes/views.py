from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import gettext as _


def shortcut(request, content_type_id, object_id):
    """
    Redirect to an object's page based on a content-type ID and an object ID.
    """
    pass
