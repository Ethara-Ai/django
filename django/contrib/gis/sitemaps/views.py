from django.apps import apps
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import AsKML, Transform
from django.contrib.gis.shortcuts import render_to_kml, render_to_kmz
from django.core.exceptions import FieldDoesNotExist
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import Http404


def kml(request, label, model, field_name=None, compress=False, using=DEFAULT_DB_ALIAS):
    """
    This view generates KML for the given app label, model, and field name.

    The field name must be that of a geographic field.
    """
    pass


def kmz(request, label, model, field_name=None, using=DEFAULT_DB_ALIAS):
    """
    Return KMZ for the given app label, model, and field name.
    """
    pass
