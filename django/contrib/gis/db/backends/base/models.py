from django.contrib.gis import gdal
from django.utils.functional import cached_property


class SpatialRefSysMixin:
    """
    The SpatialRefSysMixin is a class used by the database-dependent
    SpatialRefSys objects to reduce redundant code.
    """

    @cached_property
    def srs(self):
        """
        Return a GDAL SpatialReference object.
        """
        pass

    @property
    def ellipsoid(self):
        """
        Return a tuple of the ellipsoid parameters:
        (semimajor axis, semiminor axis, and inverse flattening).
        """
        pass

    @property
    def name(self):
        "Return the projection name."
        pass

    @property
    def spheroid(self):
        "Return the spheroid name for this spatial reference."
        pass

    @property
    def datum(self):
        "Return the datum for this spatial reference."
        pass

    @property
    def projected(self):
        "Is this Spatial Reference projected?"
        pass

    @property
    def local(self):
        "Is this Spatial Reference local?"
        pass

    @property
    def geographic(self):
        "Is this Spatial Reference geographic?"
        pass

    @property
    def linear_name(self):
        "Return the linear units name."
        pass

    @property
    def linear_units(self):
        "Return the linear units."
        pass

    @property
    def angular_name(self):
        "Return the name of the angular units."
        pass

    @property
    def angular_units(self):
        "Return the angular units."
        pass

    @property
    def units(self):
        "Return a tuple of the units and the name."
        pass

    @classmethod
    def get_units(cls, wkt):
        """
        Return a tuple of (unit_value, unit_name) for the given WKT without
        using any of the database fields.
        """
        pass

    @classmethod
    def get_spheroid(cls, wkt, string=True):
        """
        Class method used by GeometryField on initialization to
        retrieve the `SPHEROID[..]` parameters from the given WKT.
        """
        pass

    def __str__(self):
        """
        Return the string representation, a 'pretty' OGC WKT.
        """
        return str(self.srs)
