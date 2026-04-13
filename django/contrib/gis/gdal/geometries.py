"""
The OGRGeometry is a wrapper for using the OGR Geometry class
(see https://gdal.org/api/ogrgeometry_cpp.html#_CPPv411OGRGeometry).
OGRGeometry may be instantiated when reading geometries from OGR Data Sources
(e.g. SHP files), or when given OGC WKT (a string).

While the 'full' API is not present yet, the API is "pythonic" unlike
the traditional and "next-generation" OGR Python bindings. One major
advantage OGR Geometries have over their GEOS counterparts is support
for spatial reference systems and their transformation.

Example:
 >>> from django.contrib.gis.gdal import (
 ...     OGRGeometry, OGRGeomType, SpatialReference
 ... )
 >>> wkt1, wkt2 = 'POINT(-90 30)', 'POLYGON((0 0, 5 0, 5 5, 0 5)'
 >>> pnt = OGRGeometry(wkt1)
 >>> print(pnt)
 POINT (-90 30)
 >>> mpnt = OGRGeometry(OGRGeomType('MultiPoint'), SpatialReference('WGS84'))
 >>> mpnt.add(wkt1)
 >>> mpnt.add(wkt1)
 >>> print(mpnt)
 MULTIPOINT (-90 30,-90 30)
 >>> print(mpnt.srs.name)
 WGS 84
 >>> print(mpnt.srs.proj)
 +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs
 >>> mpnt.transform(SpatialReference('NAD27'))
 >>> print(mpnt.proj)
 +proj=longlat +ellps=clrk66 +datum=NAD27 +no_defs
 >>> print(mpnt)
 MULTIPOINT (-89.99993037860248 29.99979788655764,-89.99993037860248
 29.99979788655764)

 The OGRGeomType class is to make it easy to specify an OGR geometry type:
 >>> from django.contrib.gis.gdal import OGRGeomType
 >>> gt1 = OGRGeomType(3) # Using an integer for the type
 >>> gt2 = OGRGeomType('Polygon') # Using a string
 >>> gt3 = OGRGeomType('POLYGON') # It's case-insensitive
 >>> # Equivalence works w/non-OGRGeomType objects:
 >>> print(gt1 == 3, gt1 == 'Polygon')
 True True
"""

import sys
from binascii import b2a_hex
from ctypes import byref, c_char_p, c_double, c_ubyte, c_void_p, string_at

from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.envelope import Envelope, OGREnvelope
from django.contrib.gis.gdal.error import GDALException, SRSException
from django.contrib.gis.gdal.geomtype import OGRGeomType
from django.contrib.gis.gdal.prototypes import geom as capi
from django.contrib.gis.gdal.prototypes import srs as srs_api
from django.contrib.gis.gdal.srs import CoordTransform, SpatialReference
from django.contrib.gis.geometry import hex_regex, json_regex, wkt_regex
from django.utils.encoding import force_bytes


# For more information, see the OGR C API source code:
#  https://gdal.org/api/vector_c_api.html
#
# The OGR_G_* routines are relevant here.
class OGRGeometry(GDALBase):
    """Encapsulate an OGR geometry."""

    destructor = capi.destroy_geom
    geos_support = True

    def __init__(self, geom_input, srs=None):
        """Initialize Geometry on either WKT or an OGR pointer as input."""
        str_instance = isinstance(geom_input, str)

        # If HEX, unpack input to a binary buffer.
        if str_instance and hex_regex.match(geom_input):
            geom_input = memoryview(bytes.fromhex(geom_input))
            str_instance = False

        # Constructing the geometry,
        if str_instance:
            wkt_m = wkt_regex.match(geom_input)
            json_m = json_regex.match(geom_input)
            if wkt_m:
                if wkt_m["srid"]:
                    # If there's EWKT, set the SRS w/value of the SRID.
                    srs = int(wkt_m["srid"])
                if wkt_m["type"].upper() == "LINEARRING":
                    # OGR_G_CreateFromWkt doesn't work with LINEARRING WKT.
                    #  See https://trac.osgeo.org/gdal/ticket/1992.
                    g = capi.create_geom(OGRGeomType(wkt_m["type"]).num)
                    capi.import_wkt(g, byref(c_char_p(wkt_m["wkt"].encode())))
                else:
                    g = capi.from_wkt(
                        byref(c_char_p(wkt_m["wkt"].encode())), None, byref(c_void_p())
                    )
            elif json_m:
                g = self._from_json(geom_input.encode())
            else:
                # Seeing if the input is a valid short-hand string
                # (e.g., 'Point', 'POLYGON').
                OGRGeomType(geom_input)
                g = capi.create_geom(OGRGeomType(geom_input).num)
        elif isinstance(geom_input, memoryview):
            # WKB was passed in
            g = self._from_wkb(geom_input)
        elif isinstance(geom_input, OGRGeomType):
            # OGRGeomType was passed in, an empty geometry will be created.
            g = capi.create_geom(geom_input.num)
        elif isinstance(geom_input, self.ptr_type):
            # OGR pointer (c_void_p) was the input.
            g = geom_input
        else:
            raise GDALException(
                "Invalid input type for OGR Geometry construction: %s"
                % type(geom_input)
            )

        # Now checking the Geometry pointer before finishing initialization
        # by setting the pointer for the object.
        if not g:
            raise GDALException(
                "Cannot create OGR Geometry from input: %s" % geom_input
            )
        self.ptr = g

        # Assigning the SpatialReference object to the geometry, if valid.
        if srs:
            self.srs = srs

        # Setting the class depending upon the OGR Geometry Type
        if (geo_class := GEO_CLASSES.get(self.geom_type.num)) is None:
            raise TypeError(f"Unsupported geometry type: {self.geom_type}")
        self.__class__ = geo_class

    # Pickle routines
    def __getstate__(self):
        srs = self.srs
        if srs:
            srs = srs.wkt
        else:
            srs = None
        return bytes(self.wkb), srs

    def __setstate__(self, state):
        wkb, srs = state
        ptr = capi.from_wkb(wkb, None, byref(c_void_p()), len(wkb))
        if not ptr:
            raise GDALException("Invalid OGRGeometry loaded from pickled state.")
        self.ptr = ptr
        self.srs = srs

    @classmethod
    def _from_wkb(cls, geom_input):
        return capi.from_wkb(
            bytes(geom_input), None, byref(c_void_p()), len(geom_input)
        )

    @staticmethod
    def _from_json(geom_input):
        return capi.from_json(geom_input)

    @classmethod
    def from_bbox(cls, bbox):
        "Construct a Polygon from a bounding box (4-tuple)."
        pass

    @staticmethod
    def from_json(geom_input):
        return OGRGeometry(OGRGeometry._from_json(force_bytes(geom_input)))

    @classmethod
    def from_gml(cls, gml_string):
        pass

    # ### Geometry set-like operations ###
    # g = g1 | g2
    def __or__(self, other):
        "Return the union of the two geometries."
        return self.union(other)

    # g = g1 & g2
    def __and__(self, other):
        "Return the intersection of this Geometry and the other."
        return self.intersection(other)

    # g = g1 - g2
    def __sub__(self, other):
        "Return the difference this Geometry and the other."
        return self.difference(other)

    # g = g1 ^ g2
    def __xor__(self, other):
        "Return the symmetric difference of this Geometry and the other."
        return self.sym_difference(other)

    def __eq__(self, other):
        "Is this Geometry equal to the other?"
        return isinstance(other, OGRGeometry) and self.equals(other)

    def __str__(self):
        "WKT is used for the string representation."
        return self.wkt

    # #### Geometry Properties ####
    @property
    def dimension(self):
        "Return 0 for points, 1 for lines, and 2 for surfaces."
        pass

    @property
    def coord_dim(self):
        "Return the coordinate dimension of the Geometry."
        pass

    @property
    def geom_count(self):
        "Return the number of elements in this Geometry."
        pass

    @property
    def point_count(self):
        "Return the number of Points in this Geometry."
        pass

    @property
    def num_points(self):
        "Alias for `point_count` (same name method in GEOS API.)"
        pass

    @property
    def num_coords(self):
        "Alias for `point_count`."
        pass

    @property
    def geom_type(self):
        "Return the Type for this Geometry."
        pass

    @property
    def geom_name(self):
        "Return the Name of this Geometry."
        pass

    @property
    def area(self):
        """
        Return the area for a LinearRing, Polygon, or MultiPolygon; 0
        otherwise.
        """
        pass

    @property
    def envelope(self):
        "Return the envelope for this Geometry."
        pass

    @property
    def empty(self):
        pass

    @property
    def extent(self):
        "Return the envelope as a 4-tuple, instead of as an Envelope object."
        pass

    @property
    def is_3d(self):
        """Return True if the geometry has Z coordinates."""
        pass

    def set_3d(self, value):
        """Set if this geometry has Z coordinates."""
        if value is True:
            capi.set_3d(self.ptr, 1)
        elif value is False:
            capi.set_3d(self.ptr, 0)
        else:
            raise ValueError(f"Input to 'set_3d' must be a boolean, got '{value!r}'.")

    @property
    def is_measured(self):
        """Return True if the geometry has M coordinates."""
        pass

    def set_measured(self, value):
        """Set if this geometry has M coordinates."""
        if value is True:
            capi.set_measured(self.ptr, 1)
        elif value is False:
            capi.set_measured(self.ptr, 0)
        else:
            raise ValueError(
                f"Input to 'set_measured' must be a boolean, got '{value!r}'."
            )

    @property
    def has_curve(self):
        """Return True if the geometry is or has curve geometry."""
        pass

    def get_linear_geometry(self):
        """Return a linear version of this geometry."""
        pass

    def get_curve_geometry(self):
        """Return a curve version of this geometry."""
        pass

    # #### SpatialReference-related Properties ####

    # The SRS property
    def _get_srs(self):
        "Return the Spatial Reference for this Geometry."
        pass

    def _set_srs(self, srs):
        "Set the SpatialReference for this geometry."
        pass

    srs = property(_get_srs, _set_srs)

    # The SRID property
    def _get_srid(self):
        pass

    def _set_srid(self, srid):
        pass

    srid = property(_get_srid, _set_srid)

    # #### Output Methods ####
    def _geos_ptr(self):
        from django.contrib.gis.geos import GEOSGeometry

        return GEOSGeometry._from_wkb(self.wkb)

    @property
    def geos(self):
        "Return a GEOSGeometry object from this OGRGeometry."
        pass

    @property
    def gml(self):
        "Return the GML representation of the Geometry."
        pass

    @property
    def hex(self):
        "Return the hexadecimal representation of the WKB (a string)."
        return b2a_hex(self.wkb).upper()

    @property
    def json(self):
        """
        Return the GeoJSON representation of this Geometry.
        """
        return capi.to_json(self.ptr)

    geojson = json

    @property
    def kml(self):
        "Return the KML representation of the Geometry."
        pass

    @property
    def wkb_size(self):
        "Return the size of the WKB buffer."
        pass

    @property
    def wkb(self):
        "Return the WKB representation of the Geometry."
        pass

    @property
    def wkt(self):
        "Return the WKT representation of the Geometry."
        pass

    @property
    def ewkt(self):
        "Return the EWKT representation of the Geometry."
        pass

    # #### Geometry Methods ####
    def clone(self):
        "Clone this OGR Geometry."
        return OGRGeometry(capi.clone_geom(self.ptr), self.srs)

    def close_rings(self):
        """
        If there are any rings within this geometry that have not been
        closed, this routine will do so by adding the starting point at the
        end.
        """
        pass

    def transform(self, coord_trans, clone=False):
        """
        Transform this geometry to a different spatial reference system.
        May take a CoordTransform object, a SpatialReference object, string
        WKT or PROJ, and/or an integer SRID. By default, return nothing
        and transform the geometry in-place. However, if the `clone` keyword is
        set, return a transformed clone of this geometry.
        """
        if clone:
            klone = self.clone()
            klone.transform(coord_trans)
            return klone

        # Depending on the input type, use the appropriate OGR routine
        # to perform the transformation.
        if isinstance(coord_trans, CoordTransform):
            capi.geom_transform(self.ptr, coord_trans.ptr)
        elif isinstance(coord_trans, SpatialReference):
            capi.geom_transform_to(self.ptr, coord_trans.ptr)
        elif isinstance(coord_trans, (int, str)):
            sr = SpatialReference(coord_trans)
            capi.geom_transform_to(self.ptr, sr.ptr)
        else:
            raise TypeError(
                "Transform only accepts CoordTransform, "
                "SpatialReference, string, and integer objects."
            )

    # #### Topology Methods ####
    def _topology(self, func, other):
        """A generalized function for topology operations, takes a GDAL
        function and the other geometry to perform the operation on."""
        if not isinstance(other, OGRGeometry):
            raise TypeError(
                "Must use another OGRGeometry object for topology operations!"
            )

        # Returning the output of the given function with the other geometry's
        # pointer.
        return func(self.ptr, other.ptr)

    def intersects(self, other):
        "Return True if this geometry intersects with the other."
        pass

    def equals(self, other):
        "Return True if this geometry is equivalent to the other."
        pass

    def disjoint(self, other):
        "Return True if this geometry and the other are spatially disjoint."
        pass

    def touches(self, other):
        "Return True if this geometry touches the other."
        pass

    def crosses(self, other):
        "Return True if this geometry crosses the other."
        pass

    def within(self, other):
        "Return True if this geometry is within the other."
        pass

    def contains(self, other):
        "Return True if this geometry contains the other."
        return self._topology(capi.ogr_contains, other)

    def overlaps(self, other):
        "Return True if this geometry overlaps the other."
        pass

    # #### Geometry-generation Methods ####
    def _geomgen(self, gen_func, other=None):
        "A helper routine for the OGR routines that generate geometries."
        if isinstance(other, OGRGeometry):
            return OGRGeometry(gen_func(self.ptr, other.ptr), self.srs)
        else:
            return OGRGeometry(gen_func(self.ptr), self.srs)

    @property
    def boundary(self):
        "Return the boundary of this geometry."
        pass

    @property
    def convex_hull(self):
        """
        Return the smallest convex Polygon that contains all the points in
        this Geometry.
        """
        pass

    def difference(self, other):
        """
        Return a new geometry consisting of the region which is the difference
        of this geometry and the other.
        """
        return self._geomgen(capi.geom_diff, other)

    def intersection(self, other):
        """
        Return a new geometry consisting of the region of intersection of this
        geometry and the other.
        """
        return self._geomgen(capi.geom_intersection, other)

    def sym_difference(self, other):
        """
        Return a new geometry which is the symmetric difference of this
        geometry and the other.
        """
        pass

    def union(self, other):
        """
        Return a new geometry consisting of the region which is the union of
        this geometry and the other.
        """
        return self._geomgen(capi.geom_union, other)

    @property
    def centroid(self):
        """Return the centroid (a Point) of this Polygon."""
        pass


# The subclasses for OGR Geometry.
class Point(OGRGeometry):
    def _geos_ptr(self):
        from django.contrib.gis import geos

        return geos.Point._create_empty() if self.empty else super()._geos_ptr()

    @classmethod
    def _create_empty(cls):
        return capi.create_geom(OGRGeomType("point").num)

    @property
    def x(self):
        "Return the X coordinate for this Point."
        pass

    @property
    def y(self):
        "Return the Y coordinate for this Point."
        pass

    @property
    def z(self):
        "Return the Z coordinate for this Point."
        pass

    @property
    def m(self):
        """Return the M coordinate for this Point."""
        pass

    @property
    def tuple(self):
        "Return the tuple of this point."
        pass

    coords = tuple


class LineString(OGRGeometry):
    def __getitem__(self, index):
        "Return the Point at the given index."
        if 0 <= index < self.point_count:
            x, y, z, m = c_double(), c_double(), c_double(), c_double()
            capi.get_point(self.ptr, index, byref(x), byref(y), byref(z), byref(m))
            if self.is_3d and self.is_measured:
                return x.value, y.value, z.value, m.value
            if self.is_3d:
                return x.value, y.value, z.value
            if self.is_measured:
                return x.value, y.value, m.value
            dim = self.coord_dim
            if dim == 1:
                return (x.value,)
            elif dim == 2:
                return (x.value, y.value)
        else:
            raise IndexError(
                "Index out of range when accessing points of a line string: %s." % index
            )

    def __len__(self):
        "Return the number of points in the LineString."
        return self.point_count

    @property
    def tuple(self):
        "Return the tuple representation of this LineString."
        pass

    coords = tuple

    def _listarr(self, func):
        """
        Internal routine that returns a sequence (list) corresponding with
        the given function.
        """
        pass

    @property
    def x(self):
        "Return the X coordinates in a list."
        pass

    @property
    def y(self):
        "Return the Y coordinates in a list."
        pass

    @property
    def z(self):
        "Return the Z coordinates in a list."
        pass

    @property
    def m(self):
        """Return the M coordinates in a list."""
        pass


# LinearRings are used in Polygons.
class LinearRing(LineString):
    pass


class Polygon(OGRGeometry):
    def __len__(self):
        "Return the number of interior rings in this Polygon."
        return self.geom_count

    def __getitem__(self, index):
        "Get the ring at the specified index."
        if 0 <= index < self.geom_count:
            return OGRGeometry(
                capi.clone_geom(capi.get_geom_ref(self.ptr, index)), self.srs
            )
        else:
            raise IndexError(
                "Index out of range when accessing rings of a polygon: %s." % index
            )

    # Polygon Properties
    @property
    def shell(self):
        "Return the shell of this Polygon."
        pass

    exterior_ring = shell

    @property
    def tuple(self):
        "Return a tuple of LinearRing coordinate tuples."
        pass

    coords = tuple

    @property
    def point_count(self):
        "Return the number of Points in this Polygon."
        pass


class CircularString(LineString):
    geos_support = False


class CurvePolygon(Polygon):
    geos_support = False


class CompoundCurve(OGRGeometry):
    geos_support = False


# Geometry Collection base class.
class GeometryCollection(OGRGeometry):
    "The Geometry Collection class."

    def __getitem__(self, index):
        "Get the Geometry at the specified index."
        if 0 <= index < self.geom_count:
            return OGRGeometry(
                capi.clone_geom(capi.get_geom_ref(self.ptr, index)), self.srs
            )
        else:
            raise IndexError(
                "Index out of range when accessing geometry in a collection: %s."
                % index
            )

    def __len__(self):
        "Return the number of geometries in this Geometry Collection."
        return self.geom_count

    def add(self, geom):
        "Add the geometry to this Geometry Collection."
        if isinstance(geom, OGRGeometry):
            if isinstance(geom, self.__class__):
                for g in geom:
                    capi.add_geom(self.ptr, g.ptr)
            else:
                capi.add_geom(self.ptr, geom.ptr)
        elif isinstance(geom, str):
            tmp = OGRGeometry(geom)
            capi.add_geom(self.ptr, tmp.ptr)
        else:
            raise GDALException("Must add an OGRGeometry.")

    @property
    def point_count(self):
        "Return the number of Points in this Geometry Collection."
        pass

    @property
    def tuple(self):
        "Return a tuple representation of this Geometry Collection."
        pass

    coords = tuple


# Multiple Geometry types.
class MultiPoint(GeometryCollection):
    pass


class MultiLineString(GeometryCollection):
    pass


class MultiPolygon(GeometryCollection):
    pass


class MultiSurface(GeometryCollection):
    geos_support = False


class MultiCurve(GeometryCollection):
    geos_support = False


# Class mapping dictionary (using the OGRwkbGeometryType as the key)
GEO_CLASSES = {
    1: Point,
    2: LineString,
    3: Polygon,
    4: MultiPoint,
    5: MultiLineString,
    6: MultiPolygon,
    7: GeometryCollection,
    8: CircularString,
    9: CompoundCurve,
    10: CurvePolygon,
    11: MultiCurve,
    12: MultiSurface,
    101: LinearRing,
    1008: CircularString,  # CIRCULARSTRING Z
    1009: CompoundCurve,  # COMPOUNDCURVE Z
    1010: CurvePolygon,  # CURVEPOLYGON Z
    1011: MultiCurve,  # MULTICURVE Z
    1012: MultiSurface,  # MULTICURVE Z
    2001: Point,  # POINT M
    2002: LineString,  # LINESTRING M
    2003: Polygon,  # POLYGON M
    2004: MultiPoint,  # MULTIPOINT M
    2005: MultiLineString,  # MULTILINESTRING M
    2006: MultiPolygon,  # MULTIPOLYGON M
    2007: GeometryCollection,  # GEOMETRYCOLLECTION M
    2008: CircularString,  # CIRCULARSTRING M
    2009: CompoundCurve,  # COMPOUNDCURVE M
    2010: CurvePolygon,  # CURVEPOLYGON M
    2011: MultiCurve,  # MULTICURVE M
    2012: MultiSurface,  # MULTICURVE M
    3001: Point,  # POINT ZM
    3002: LineString,  # LINESTRING ZM
    3003: Polygon,  # POLYGON ZM
    3004: MultiPoint,  # MULTIPOINT ZM
    3005: MultiLineString,  # MULTILINESTRING ZM
    3006: MultiPolygon,  # MULTIPOLYGON ZM
    3007: GeometryCollection,  # GEOMETRYCOLLECTION ZM
    3008: CircularString,  # CIRCULARSTRING ZM
    3009: CompoundCurve,  # COMPOUNDCURVE ZM
    3010: CurvePolygon,  # CURVEPOLYGON ZM
    3011: MultiCurve,  # MULTICURVE ZM
    3012: MultiSurface,  # MULTISURFACE ZM
    1 + OGRGeomType.wkb25bit: Point,  # POINT Z
    2 + OGRGeomType.wkb25bit: LineString,  # LINESTRING Z
    3 + OGRGeomType.wkb25bit: Polygon,  # POLYGON Z
    4 + OGRGeomType.wkb25bit: MultiPoint,  # MULTIPOINT Z
    5 + OGRGeomType.wkb25bit: MultiLineString,  # MULTILINESTRING Z
    6 + OGRGeomType.wkb25bit: MultiPolygon,  # MULTIPOLYGON Z
    7 + OGRGeomType.wkb25bit: GeometryCollection,  # GEOMETRYCOLLECTION Z
}
