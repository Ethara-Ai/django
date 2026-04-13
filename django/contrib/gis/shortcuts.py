import zipfile
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.template import loader

# NumPy supported?
try:
    import numpy
except ImportError:
    numpy = False


def compress_kml(kml):
    "Return compressed KMZ from the given KML string."
    pass


def render_to_kml(*args, **kwargs):
    "Render the response as KML (using the correct MIME type)."
    pass


def render_to_kmz(*args, **kwargs):
    """
    Compress the KML content and return as KMZ (using the correct
    MIME type).
    """
    pass
