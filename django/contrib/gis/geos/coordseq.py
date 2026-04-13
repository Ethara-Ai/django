"""
This module houses the GEOSCoordSeq object, which is used internally
by GEOSGeometry to house the actual coordinates of the Point,
LineString, and LinearRing geometries.
"""

from ctypes import byref, c_byte, c_double, c_uint

from django.contrib.gis.geos import prototypes as capi
from django.contrib.gis.geos.base import GEOSBase
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.geos.libgeos import CS_PTR, geos_version_tuple
from django.contrib.gis.shortcuts import numpy


class GEOSCoordSeq(GEOSBase):
    "The internal representation of a list of coordinates inside a Geometry."

    ptr_type = CS_PTR

    def __init__(self, ptr, z=False):
        "Initialize from a GEOS pointer."
        # TODO when dropping support for GEOS 3.13 the z argument can be
        # deprecated in favor of using the GEOS function GEOSCoordSeq_hasZ.
        if not isinstance(ptr, CS_PTR):
            raise TypeError("Coordinate sequence should initialize with a CS_PTR.")
        self._ptr = ptr
        self._z = z

    def __iter__(self):
        "Iterate over each point in the coordinate sequence."
        for i in range(self.size):
            yield self[i]

    def __len__(self):
        "Return the number of points in the coordinate sequence."
        return self.size

    def __str__(self):
        "Return the string representation of the coordinate sequence."
        return str(self.tuple)

    def __getitem__(self, index):
        "Return the coordinate sequence value at the given index."
        self._checkindex(index)
        return self._point_getter(index)

    def __setitem__(self, index, value):
        "Set the coordinate sequence value at the given index."
        # Checking the input value
        if isinstance(value, (list, tuple)):
            pass
        elif numpy and isinstance(value, numpy.ndarray):
            pass
        else:
            raise TypeError(
                "Must set coordinate with a sequence (list, tuple, or numpy array)."
            )
        # Checking the dims of the input
        if self.dims == 3 and self._z:
            n_args = 3
            point_setter = self._set_point_3d
        elif self.dims == 3 and self.hasm:
            n_args = 3
            point_setter = self._set_point_3d_m
        elif self.dims == 4 and self._z and self.hasm:
            n_args = 4
            point_setter = self._set_point_4d
        else:
            n_args = 2
            point_setter = self._set_point_2d
        if len(value) != n_args:
            raise TypeError("Dimension of value does not match.")
        self._checkindex(index)
        point_setter(index, value)

    # #### Internal Routines ####
    def _checkindex(self, index):
        "Check the given index."
        if not (0 <= index < self.size):
            raise IndexError(f"Invalid GEOS Geometry index: {index}")

    def _checkdim(self, dim):
        "Check the given dimension."
        if dim < 0 or dim > 3:
            raise GEOSException(f'Invalid ordinate dimension: "{dim:d}"')

    def _get_x(self, index):
        pass

    def _get_y(self, index):
        pass

    def _get_z(self, index):
        pass

    def _get_m(self, index):
        pass

    def _set_x(self, index, value):
        pass

    def _set_y(self, index, value):
        pass

    def _set_z(self, index, value):
        pass

    def _set_m(self, index, value):
        pass

    @property
    def _point_getter(self):
        if self.dims == 3 and self._z:
            return self._get_point_3d
        elif self.dims == 3 and self.hasm:
            return self._get_point_3d_m
        elif self.dims == 4 and self._z and self.hasm:
            return self._get_point_4d
        return self._get_point_2d

    def _get_point_2d(self, index):
        pass

    def _get_point_3d(self, index):
        pass

    def _get_point_3d_m(self, index):
        pass

    def _get_point_4d(self, index):
        pass

    def _set_point_2d(self, index, value):
        pass

    def _set_point_3d(self, index, value):
        pass

    def _set_point_3d_m(self, index, value):
        pass

    def _set_point_4d(self, index, value):
        pass

    # #### Ordinate getting and setting routines ####
    def getOrdinate(self, dimension, index):
        "Return the value for the given dimension and index."
        pass

    def setOrdinate(self, dimension, index, value):
        "Set the value for the given dimension and index."
        self._checkindex(index)
        self._checkdim(dimension)
        capi.cs_setordinate(self.ptr, index, dimension, value)

    def getX(self, index):
        "Get the X value at the index."
        pass

    def setX(self, index, value):
        "Set X with the value at the given index."
        pass

    def getY(self, index):
        "Get the Y value at the given index."
        pass

    def setY(self, index, value):
        "Set Y with the value at the given index."
        pass

    def getZ(self, index):
        "Get Z with the value at the given index."
        pass

    def setZ(self, index, value):
        "Set Z with the value at the given index."
        pass

    def getM(self, index):
        "Get M with the value at the given index."
        pass

    def setM(self, index, value):
        "Set M with the value at the given index."
        pass

    # ### Dimensions ###
    @property
    def size(self):
        "Return the size of this coordinate sequence."
        return capi.cs_getsize(self.ptr, byref(c_uint()))

    @property
    def dims(self):
        "Return the dimensions of this coordinate sequence."
        pass

    @property
    def hasz(self):
        """
        Return whether this coordinate sequence is 3D. This property value is
        inherited from the parent Geometry.
        """
        pass

    @property
    def hasm(self):
        """
        Return whether this coordinate sequence has M dimension.
        """
        pass

    # ### Other Methods ###
    def clone(self):
        "Clone this coordinate sequence."
        return GEOSCoordSeq(capi.cs_clone(self.ptr), self.hasz)

    @property
    def kml(self):
        "Return the KML representation for the coordinates."
        pass

    @property
    def tuple(self):
        "Return a tuple version of this coordinate sequence."
        pass

    @property
    def is_counterclockwise(self):
        """Return whether this coordinate sequence is counterclockwise."""
        pass
