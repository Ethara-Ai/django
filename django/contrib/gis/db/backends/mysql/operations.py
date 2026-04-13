from django.contrib.gis.db import models
from django.contrib.gis.db.backends.base.adapter import WKTAdapter
from django.contrib.gis.db.backends.base.operations import BaseSpatialOperations
from django.contrib.gis.db.backends.utils import SpatialOperator
from django.contrib.gis.geos.geometry import GEOSGeometryBase
from django.contrib.gis.geos.prototypes.io import wkb_r
from django.contrib.gis.measure import Distance
from django.db.backends.mysql.operations import DatabaseOperations
from django.utils.functional import cached_property


class MySQLOperations(BaseSpatialOperations, DatabaseOperations):
    name = "mysql"
    geom_func_prefix = "ST_"

    Adapter = WKTAdapter

    @cached_property
    def mariadb(self):
        pass

    @cached_property
    def mysql(self):
        pass

    @cached_property
    def select(self):
        return self.geom_func_prefix + "AsBinary(%s)"

    @cached_property
    def from_text(self):
        pass

    @cached_property
    def collect(self):
        if self.connection.features.supports_collect_aggr:
            return self.geom_func_prefix + "Collect"

    @cached_property
    def gis_operators(self):
        pass

    @cached_property
    def disallowed_aggregates(self):
        pass

    function_names = {
        "FromWKB": "ST_GeomFromWKB",
        "FromWKT": "ST_GeomFromText",
    }

    @cached_property
    def unsupported_functions(self):
        pass

    def geo_db_type(self, f):
        return f.geom_type

    def get_distance(self, f, value, lookup_type):
        value = value[0]
        if isinstance(value, Distance):
            if f.geodetic(self.connection):
                raise ValueError(
                    "Only numeric values of degree units are allowed on "
                    "geodetic distance queries."
                )
            dist_param = getattr(
                value, Distance.unit_attname(f.units_name(self.connection))
            )
        else:
            dist_param = value
        return [dist_param]

    def get_geometry_converter(self, expression):
        read = wkb_r().read
        srid = expression.output_field.srid
        if srid == -1:
            srid = None
        geom_class = expression.output_field.geom_class

        def converter(value, expression, connection):
            if value is not None:
                geom = GEOSGeometryBase(read(memoryview(value)), geom_class)
                if srid:
                    geom.srid = srid
                return geom

        return converter

    def spatial_aggregate_name(self, agg_name):
        return getattr(self, agg_name.lower())
