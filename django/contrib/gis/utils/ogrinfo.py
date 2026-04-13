"""
This module includes some utility functions for inspecting the layout
of a GDAL data source -- the functionality is analogous to the output
produced by the `ogrinfo` utility.
"""

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.geometries import GEO_CLASSES


def ogrinfo(data_source, num_features=10):
    """
    Walk the available layers in the supplied `data_source`, displaying
    the fields for the first `num_features` features.
    """
    pass
