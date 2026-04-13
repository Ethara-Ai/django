from django.contrib.gis.gdal import SpatialReference
from django.db import DEFAULT_DB_ALIAS, connections


def add_srs_entry(
    srs, auth_name="EPSG", auth_srid=None, ref_sys_name=None, database=None
):
    """
    Take a GDAL SpatialReference system and add its information to the
    `spatial_ref_sys` table of the spatial backend. Doing this enables
    database-level spatial transformations for the backend. Thus, this utility
    is useful for adding spatial reference systems not included by default with
    the backend:

    >>> from django.contrib.gis.utils import add_srs_entry
    >>> add_srs_entry(3857)

    Keyword Arguments:
     auth_name:
       This keyword may be customized with the value of the `auth_name` field.
       Defaults to 'EPSG'.

     auth_srid:
       This keyword may be customized with the value of the `auth_srid` field.
       Defaults to the SRID determined by GDAL.

     ref_sys_name:
       For SpatiaLite users only, sets the value of the `ref_sys_name` field.
       Defaults to the name determined by GDAL.

     database:
      The name of the database connection to use; the default is the value
      of `django.db.DEFAULT_DB_ALIAS` (at the time of this writing, its value
      is 'default').
    """
    pass
