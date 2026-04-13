"""
This module contains the 'base' GEOSGeometry object -- all GEOS Geometries
inherit from this object.
"""

import re
from ctypes import addressof, byref, c_double

from django.contrib.gis import gdal
from django.contrib.gis.geometry import hex_regex, json_regex, wkt_regex
from django.contrib.gis.geos import prototypes as capi
from django.contrib.gis.geos.base import GEOSBase
from django.contrib.gis.geos.coordseq import GEOSCoordSeq
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.geos.libgeos import GEOM_PTR, geos_version_tuple
from django.contrib.gis.geos.mutable_list import ListMixin
from django.contrib.gis.geos.prepared import PreparedGeometry
from django.contrib.gis.geos.prototypes.io import ewkb_w, wkb_r, wkb_w, wkt_r, wkt_w
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_bytes, force_str


class GEOSGeometryBase(GEOSBase):
    _GEOS_CLASSES = None

    ptr_type = GEOM_PTR
    destructor = capi.destroy_geom
    has_cs = False  # Only Point, LineString, LinearRing have coordinate sequences

    def __init__(self, ptr, cls):
        self._ptr = ptr

        # Setting the class type (e.g., Point, Polygon, etc.)
        if type(self) in (GEOSGeometryBase, GEOSGeometry):
            if cls is None:
                if GEOSGeometryBase._GEOS_CLASSES is None:
                    # Inner imports avoid import conflicts with GEOSGeometry.
                    from .collections import (
                        GeometryCollection,
                        MultiLineString,
                        MultiPoint,
                        MultiPolygon,
                    )
                    from .linestring import LinearRing, LineString
                    from .point import Point
                    from .polygon import Polygon

                    GEOSGeometryBase._GEOS_CLASSES = {
                        0: Point,
                        1: LineString,
                        2: LinearRing,
                        3: Polygon,
                        4: MultiPoint,
                        5: MultiLineString,
                        6: MultiPolygon,
                        7: GeometryCollection,
                    }
                cls = GEOSGeometryBase._GEOS_CLASSES[self.geom_typeid]
            self.__class__ = cls
        self._post_init()

    def _post_init(self):
        "Perform post-initialization setup."
        # Setting the coordinate sequence for the geometry (will be None on
        # geometries that do not have coordinate sequences)
        self._cs = (
            GEOSCoordSeq(capi.get_cs(self.ptr), self.hasz) if self.has_cs else None
        )

    def __copy__(self):
        """
        Return a clone because the copy of a GEOSGeometry may contain an
        invalid pointer location if the original is garbage collected.
        """
        return self.clone()

    def __deepcopy__(self, memodict):
        """
        The `deepcopy` routine is used by the `Node` class of
        django.utils.tree; thus, the protocol routine needs to be implemented
        to return correct copies (clones) of these GEOS objects, which use C
        pointers.
        """
        return self.clone()

    def __str__(self):
        "EWKT is used for the string representation."
        return self.ewkt

    def __repr__(self):
        "Short-hand representation because WKT may be very large."
        return "<%s object at %s>" % (self.geom_type, hex(addressof(self.ptr)))

    # Pickling support
    def _to_pickle_wkb(self):
        return bytes(self.wkb)

    def _from_pickle_wkb(self, wkb):
        pass

    def __getstate__(self):
        # The pickled state is simply a tuple of the WKB (in string form)
        # and the SRID.
        return self._to_pickle_wkb(), self.srid

    def __setstate__(self, state):
        # Instantiating from the tuple state that was pickled.
        wkb, srid = state
        ptr = self._from_pickle_wkb(wkb)
        if not ptr:
            raise GEOSException("Invalid Geometry loaded from pickled state.")
        self.ptr = ptr
        self._post_init()
        self.srid = srid

    @classmethod
    def _from_wkb(cls, wkb):
        return wkb_r().read(wkb)

    @staticmethod
    def from_ewkt(ewkt):
        pass

    @staticmethod
    def _from_wkt(wkt):
        return wkt_r().read(wkt)

    @classmethod
    def from_gml(cls, gml_string):
        pass

    # Comparison operators
    def __eq__(self, other):
        """
        Equivalence testing, a Geometry may be compared with another Geometry
        or an EWKT representation.
        """
        if isinstance(other, str):
            try:
                other = GEOSGeometry.from_ewkt(other)
            except (ValueError, GEOSException):
                return False
        return (
            isinstance(other, GEOSGeometry)
            and self.srid == other.srid
            and self.equals_exact(other)
        )

    def __hash__(self):
        return hash((self.srid, self.wkt))

    # ### Geometry set-like operations ###
    # Thanks to Sean Gillies for inspiration:
    #  http://lists.gispython.org/pipermail/community/2007-July/001034.html
    # g = g1 | g2
    def __or__(self, other):
        "Return the union of this Geometry and the other."
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

    # #### Coordinate Sequence Routines ####
    @property
    def coord_seq(self):
        "Return a clone of the coordinate sequence for this Geometry."
        pass

    # #### Geometry Info ####
    @property
    def geom_type(self):
        "Return a string representing the Geometry type, e.g. 'Polygon'"
        pass

    @property
    def geom_typeid(self):
        "Return an integer representing the Geometry type."
        pass

    @property
    def num_geom(self):
        "Return the number of geometries in the Geometry."
        pass

    @property
    def num_coords(self):
        "Return the number of coordinates in the Geometry."
        pass

    @property
    def num_points(self):
        "Return the number of points, or coordinates, in the Geometry."
        pass

    @property
    def dims(self):
        "Return the dimension of this Geometry (0=point, 1=line, 2=surface)."
        pass

    def normalize(self, clone=False):
        """
        Convert this Geometry to normal form (or canonical form).
        If the `clone` keyword is set, then the geometry is not modified and a
        normalized clone of the geometry is returned instead.
        """
        if clone:
            clone = self.clone()
            capi.geos_normalize(clone.ptr)
            return clone
        capi.geos_normalize(self.ptr)

    def make_valid(self):
        """
        Attempt to create a valid representation of a given invalid geometry
        without losing any of the input vertices.
        """
        pass

    # #### Unary predicates ####
    @property
    def empty(self):
        """
        Return a boolean indicating whether the set of points in this Geometry
        are empty.
        """
        pass

    @property
    def hasz(self):
        "Return whether the geometry has a Z dimension."
        pass

    @property
    def hasm(self):
        "Return whether the geometry has a M dimension."
        pass

    @property
    def ring(self):
        "Return whether or not the geometry is a ring."
        pass

    @property
    def simple(self):
        "Return false if the Geometry isn't simple."
        pass

    @property
    def valid(self):
        "Test the validity of this Geometry."
        pass

    @property
    def valid_reason(self):
        """
        Return a string containing the reason for any invalidity.
        """
        pass

    # #### Binary predicates. ####
    def contains(self, other):
        "Return true if other.within(this) returns true."
        return capi.geos_contains(self.ptr, other.ptr)

    def covers(self, other):
        """
        Return True if the DE-9IM Intersection Matrix for the two geometries is
        T*****FF*, *T****FF*, ***T**FF*, or ****T*FF*. If either geometry is
        empty, return False.
        """
        pass

    def crosses(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*T****** (for a point and a curve,a point and an area or a line and
        an area) 0******** (for two curves).
        """
        pass

    def disjoint(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is FF*FF****.
        """
        pass

    def equals(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*F**FFF*.
        """
        pass

    def equals_exact(self, other, tolerance=0):
        """
        Return true if the two Geometries are exactly equal, up to a
        specified tolerance.
        """
        return capi.geos_equalsexact(self.ptr, other.ptr, float(tolerance))

    def equals_identical(self, other):
        """
        Return true if the two Geometries are point-wise equivalent.
        """
        pass

    def intersects(self, other):
        "Return true if disjoint return false."
        pass

    def overlaps(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*T***T** (for two points or two surfaces) 1*T***T** (for two
        curves).
        """
        pass

    def relate_pattern(self, other, pattern):
        """
        Return true if the elements in the DE-9IM intersection matrix for the
        two Geometries match the elements in pattern.
        """
        pass

    def touches(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is FT*******, F**T***** or F***T****.
        """
        pass

    def within(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*F**F***.
        """
        pass

    # #### SRID Routines ####
    @property
    def srid(self):
        "Get the SRID for the geometry. Return None if no SRID is set."
        pass

    @srid.setter
    def srid(self, srid):
        "Set the SRID for the geometry."
        pass

    # #### Output Routines ####
    @property
    def ewkt(self):
        """
        Return the EWKT (SRID + WKT) of the Geometry.
        """
        pass

    @property
    def wkt(self):
        "Return the WKT (Well-Known Text) representation of this Geometry."
        pass

    @property
    def hex(self):
        """
        Return the WKB of this Geometry in hexadecimal form. Please note
        that the SRID is not included in this representation because it is not
        a part of the OGC specification (use the `hexewkb` property instead).
        """
        # A possible faster, all-python, implementation:
        #  str(self.wkb).encode('hex')
        return wkb_w(dim=3 if self.hasz else 2).write_hex(self)

    @property
    def hexewkb(self):
        """
        Return the EWKB of this Geometry in hexadecimal form. This is an
        extension of the WKB specification that includes SRID value that are
        a part of this geometry.
        """
        pass

    @property
    def json(self):
        """
        Return GeoJSON representation of this Geometry.
        """
        return self.ogr.json

    geojson = json

    @property
    def wkb(self):
        """
        Return the WKB (Well-Known Binary) representation of this Geometry
        as a Python memoryview. SRID and Z values are not included, use the
        `ewkb` property instead.
        """
        pass

    @property
    def ewkb(self):
        """
        Return the EWKB representation of this Geometry as a Python memoryview.
        This is an extension of the WKB specification that includes any SRID
        value that are a part of this geometry.
        """
        pass

    @property
    def kml(self):
        "Return the KML representation of this Geometry."
        pass

    @property
    def prepared(self):
        """
        Return a PreparedGeometry corresponding to this geometry -- it is
        optimized for the contains, intersects, and covers operations.
        """
        pass

    # #### GDAL-specific output routines ####
    def _ogr_ptr(self):
        return gdal.OGRGeometry._from_wkb(self.wkb)

    @property
    def ogr(self):
        "Return the OGR Geometry for this Geometry."
        pass

    @property
    def srs(self):
        "Return the OSR SpatialReference for SRID of this Geometry."
        pass

    @property
    def crs(self):
        "Alias for `srs` property."
        pass

    def transform(self, ct, clone=False):
        """
        Requires GDAL. Transform the geometry according to the given
        transformation object, which may be an integer SRID, and WKT or
        PROJ string. By default, transform the geometry in-place and return
        nothing. However if the `clone` keyword is set, don't modify the
        geometry and return a transformed clone instead.
        """
        srid = self.srid

        if ct == srid:
            # short-circuit where source & dest SRIDs match
            if clone:
                return self.clone()
            else:
                return

        if isinstance(ct, gdal.CoordTransform):
            # We don't care about SRID because CoordTransform presupposes
            # source SRS.
            srid = None
        elif srid is None or srid < 0:
            raise GEOSException(
                "Calling transform() with no SRID set is not supported."
            )

        # Creating an OGR Geometry, which is then transformed.
        g = gdal.OGRGeometry(self._ogr_ptr(), srid)
        g.transform(ct)
        # Getting a new GEOS pointer
        ptr = g._geos_ptr()
        if clone:
            # User wants a cloned transformed geometry returned.
            return GEOSGeometry(ptr, srid=g.srid)
        if ptr:
            # Reassigning pointer, and performing post-initialization setup
            # again due to the reassignment.
            capi.destroy_geom(self.ptr)
            self.ptr = ptr
            self._post_init()
            self.srid = g.srid
        else:
            raise GEOSException("Transformed WKB was invalid.")

    # #### Topology Routines ####
    def _topology(self, gptr):
        "Return Geometry from the given pointer."
        return GEOSGeometry(gptr, srid=self.srid)

    @property
    def boundary(self):
        "Return the boundary as a newly allocated Geometry object."
        pass

    def buffer(self, width, quadsegs=8):
        """
        Return a geometry that represents all points whose distance from this
        Geometry is less than or equal to distance. Calculations are in the
        Spatial Reference System of this Geometry. The optional third parameter
        sets the number of segment used to approximate a quarter circle
        (defaults to 8). (Text from PostGIS documentation at ch. 6.1.3)
        """
        pass

    def buffer_with_style(
        self, width, quadsegs=8, end_cap_style=1, join_style=1, mitre_limit=5.0
    ):
        """
        Same as buffer() but allows customizing the style of the memoryview.

        End cap style can be round (1), flat (2), or square (3).
        Join style can be round (1), mitre (2), or bevel (3).
        Mitre ratio limit only affects mitered join style.
        """
        pass

    @property
    def centroid(self):
        """
        The centroid is equal to the centroid of the set of component
        Geometries of highest dimension (since the lower-dimension geometries
        contribute zero "weight" to the centroid).
        """
        pass

    @property
    def convex_hull(self):
        """
        Return the smallest convex Polygon that contains all the points
        in the Geometry.
        """
        pass

    def difference(self, other):
        """
        Return a Geometry representing the points making up this Geometry
        that do not make up other.
        """
        return self._topology(capi.geos_difference(self.ptr, other.ptr))

    @property
    def envelope(self):
        "Return the envelope for this geometry (a polygon)."
        pass

    def intersection(self, other):
        """
        Return a Geometry representing the points shared by this Geometry and
        other.
        """
        return self._topology(capi.geos_intersection(self.ptr, other.ptr))

    @property
    def point_on_surface(self):
        "Compute an interior point of this Geometry."
        pass

    def relate(self, other):
        """
        Return the DE-9IM intersection matrix for this Geometry and the other.
        """
        pass

    def simplify(self, tolerance=0.0, preserve_topology=False):
        """
        Return the Geometry, simplified using the Douglas-Peucker algorithm
        to the specified tolerance (higher tolerance => less points). If no
        tolerance provided, defaults to 0.

        By default, don't preserve topology - e.g. polygons can be split,
        collapse to lines or disappear holes can be created or disappear, and
        lines can cross. By specifying preserve_topology=True, the result will
        have the same dimension and number of components as the input. This is
        significantly slower.
        """
        pass

    def sym_difference(self, other):
        """
        Return a set combining the points in this Geometry not in other,
        and the points in other not in this Geometry.
        """
        pass

    @property
    def unary_union(self):
        "Return the union of all the elements of this geometry."
        pass

    def union(self, other):
        """
        Return a Geometry representing all the points in this Geometry and
        other.
        """
        return self._topology(capi.geos_union(self.ptr, other.ptr))

    # #### Other Routines ####
    @property
    def area(self):
        "Return the area of the Geometry."
        pass

    def distance(self, other):
        """
        Return the distance between the closest points on this Geometry
        and the other. Units will be in those of the coordinate system of
        the Geometry.
        """
        pass

    @property
    def extent(self):
        """
        Return the extent of this geometry as a 4-tuple, consisting of
        (xmin, ymin, xmax, ymax).
        """
        pass

    @property
    def length(self):
        """
        Return the length of this Geometry (e.g., 0 for point, or the
        circumference of a Polygon).
        """
        pass

    def clone(self):
        "Clone this Geometry."
        return GEOSGeometry(capi.geom_clone(self.ptr))


class LinearGeometryMixin:
    """
    Used for LineString and MultiLineString.
    """

    def interpolate(self, distance):
        pass

    def interpolate_normalized(self, distance):
        pass

    def project(self, point):
        pass

    def project_normalized(self, point):
        pass

    @property
    def merged(self):
        """
        Return the line merge of this Geometry.
        """
        pass

    @property
    def closed(self):
        """
        Return whether or not this Geometry is closed.
        """
        pass


@deconstructible
class GEOSGeometry(GEOSGeometryBase, ListMixin):
    "A class that, generally, encapsulates a GEOS geometry."

    def __init__(self, geo_input, srid=None):
        """
        The base constructor for GEOS geometry objects. It may take the
        following inputs:

         * strings:
            - WKT
            - HEXEWKB (a PostGIS-specific canonical form)
            - GeoJSON (requires GDAL)
         * memoryview:
            - WKB

        The `srid` keyword specifies the Source Reference Identifier (SRID)
        number for this Geometry. If not provided, it defaults to None.
        """
        input_srid = None
        if isinstance(geo_input, bytes):
            geo_input = force_str(geo_input)
        if isinstance(geo_input, str):
            wkt_m = wkt_regex.match(geo_input)
            if wkt_m:
                # Handle WKT input.
                if wkt_m["srid"]:
                    input_srid = int(wkt_m["srid"])
                g = self._from_wkt(force_bytes(wkt_m["wkt"]))
            elif hex_regex.match(geo_input):
                # Handle HEXEWKB input.
                g = wkb_r().read(force_bytes(geo_input))
            elif json_regex.match(geo_input):
                # Handle GeoJSON input.
                ogr = gdal.OGRGeometry.from_json(geo_input)
                g = ogr._geos_ptr()
                input_srid = ogr.srid
            else:
                raise ValueError("String input unrecognized as WKT EWKT, and HEXEWKB.")
        elif isinstance(geo_input, GEOM_PTR):
            # When the input is a pointer to a geometry (GEOM_PTR).
            g = geo_input
        elif isinstance(geo_input, memoryview):
            # When the input is a memoryview (WKB).
            g = wkb_r().read(geo_input)
        elif isinstance(geo_input, GEOSGeometry):
            g = capi.geom_clone(geo_input.ptr)
        else:
            raise TypeError("Improper geometry input type: %s" % type(geo_input))

        if not g:
            raise GEOSException("Could not initialize GEOS Geometry with given input.")

        input_srid = input_srid or capi.geos_get_srid(g) or None
        if input_srid and srid and input_srid != srid:
            raise ValueError("Input geometry already has SRID: %d." % input_srid)

        super().__init__(g, None)
        # Set the SRID, if given.
        srid = input_srid or srid
        if srid and isinstance(srid, int):
            self.srid = srid
