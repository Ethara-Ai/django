from decimal import Decimal

from django.contrib.gis.db.models.fields import BaseSpatialField, GeometryField
from django.contrib.gis.db.models.sql import AreaField, DistanceField
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.point import Point
from django.core.exceptions import FieldError
from django.db import NotSupportedError
from django.db.models import (
    BinaryField,
    BooleanField,
    CharField,
    FloatField,
    Func,
    IntegerField,
    TextField,
    Transform,
    Value,
)
from django.db.models.functions import Cast
from django.utils.functional import cached_property

NUMERIC_TYPES = (int, float, Decimal)


class GeoFuncMixin:
    function = None
    geom_param_pos = (0,)

    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, **extra)

        # Ensure that value expressions are geometric.
        for pos in self.geom_param_pos:
            expr = self.source_expressions[pos]
            if not isinstance(expr, Value):
                continue
            try:
                output_field = expr.output_field
            except FieldError:
                output_field = None
            geom = expr.value
            if (
                not isinstance(geom, GEOSGeometry)
                or output_field
                and not isinstance(output_field, GeometryField)
            ):
                raise TypeError(
                    "%s function requires a geometric argument in position %d."
                    % (self.name, pos + 1)
                )
            if not geom.srid and not output_field:
                raise ValueError("SRID is required for all geometries.")
            if not output_field:
                self.source_expressions[pos] = Value(
                    geom, output_field=GeometryField(srid=geom.srid)
                )

    @property
    def name(self):
        pass

    @cached_property
    def geo_field(self):
        pass

    def as_sql(self, compiler, connection, function=None, **extra_context):
        if self.function is None and function is None:
            function = connection.ops.spatial_function_name(self.name)
        return super().as_sql(compiler, connection, function=function, **extra_context)

    def resolve_expression(self, *args, **kwargs):
        res = super().resolve_expression(*args, **kwargs)
        if not self.geom_param_pos:
            return res

        # Ensure that expressions are geometric.
        source_fields = res.get_source_fields()
        for pos in self.geom_param_pos:
            field = source_fields[pos]
            if not isinstance(field, GeometryField):
                raise TypeError(
                    "%s function requires a GeometryField in position %s, got %s."
                    % (
                        self.name,
                        pos + 1,
                        type(field).__name__,
                    )
                )

        base_srid = res.geo_field.srid
        for pos in self.geom_param_pos[1:]:
            expr = res.source_expressions[pos]
            expr_srid = expr.output_field.srid
            if expr_srid != base_srid:
                # Automatic SRID conversion so objects are comparable.
                res.source_expressions[pos] = Transform(
                    expr, base_srid
                ).resolve_expression(*args, **kwargs)
        return res

    def _handle_param(self, value, param_name="", check_types=None):
        if not hasattr(value, "resolve_expression"):
            if check_types and not isinstance(value, check_types):
                raise TypeError(
                    "The %s parameter has the wrong type: should be %s."
                    % (param_name, check_types)
                )
        return value


class GeoFunc(GeoFuncMixin, Func):
    pass


class GeomOutputGeoFunc(GeoFunc):
    @cached_property
    def output_field(self):
        pass


class SQLiteDecimalToFloatMixin:
    """
    By default, Decimal values are converted to str by the SQLite backend,
    which is not acceptable by the GIS functions expecting numeric values.
    """

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class OracleToleranceMixin:
    tolerance = 0.05

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Area(OracleToleranceMixin, GeoFunc):
    arity = 1

    @cached_property
    def output_field(self):
        pass

    def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_area_geodetic and self.geo_field.geodetic(
            connection
        ):
            raise NotSupportedError(
                "Area on geodetic coordinate systems not supported."
            )
        return super().as_sql(compiler, connection, **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Azimuth(GeoFunc):
    output_field = FloatField()
    arity = 2
    geom_param_pos = (0, 1)


class AsGeoJSON(GeoFunc):
    output_field = TextField()

    def __init__(self, expression, bbox=False, crs=False, precision=8, **extra):
        expressions = [expression]
        if precision is not None:
            expressions.append(self._handle_param(precision, "precision", int))
        options = 0
        if crs and bbox:
            options = 3
        elif bbox:
            options = 1
        elif crs:
            options = 2
        expressions.append(options)
        super().__init__(*expressions, **extra)

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class AsGML(GeoFunc):
    geom_param_pos = (1,)
    output_field = TextField()

    def __init__(self, expression, version=2, precision=8, **extra):
        expressions = [version, expression]
        if precision is not None:
            expressions.append(self._handle_param(precision, "precision", int))
        super().__init__(*expressions, **extra)

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class AsKML(GeoFunc):
    output_field = TextField()

    def __init__(self, expression, precision=8, **extra):
        expressions = [expression]
        if precision is not None:
            expressions.append(self._handle_param(precision, "precision", int))
        super().__init__(*expressions, **extra)


class AsSVG(GeoFunc):
    output_field = TextField()

    def __init__(self, expression, relative=False, precision=8, **extra):
        relative = (
            relative if hasattr(relative, "resolve_expression") else int(relative)
        )
        expressions = [
            expression,
            relative,
            self._handle_param(precision, "precision", int),
        ]
        super().__init__(*expressions, **extra)


class AsWKB(GeoFunc):
    output_field = BinaryField()
    arity = 1


class AsWKT(GeoFunc):
    output_field = TextField()
    arity = 1


class BoundingCircle(OracleToleranceMixin, GeomOutputGeoFunc):
    def __init__(self, expression, num_seg=48, **extra):
        super().__init__(expression, num_seg, **extra)

    def as_oracle(self, compiler, connection, **extra_context):
        pass

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Centroid(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 1


class ClosestPoint(GeomOutputGeoFunc):
    arity = 2
    geom_param_pos = (0, 1)


class Difference(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 2
    geom_param_pos = (0, 1)


class DistanceResultMixin:
    @cached_property
    def output_field(self):
        pass

    def source_is_geography(self):
        pass


class Distance(DistanceResultMixin, OracleToleranceMixin, GeoFunc):
    geom_param_pos = (0, 1)
    spheroid = None

    def __init__(self, expr1, expr2, spheroid=None, **extra):
        expressions = [expr1, expr2]
        if spheroid is not None:
            self.spheroid = self._handle_param(spheroid, "spheroid", bool)
        super().__init__(*expressions, **extra)

    def as_postgresql(self, compiler, connection, **extra_context):
        pass

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Envelope(GeomOutputGeoFunc):
    arity = 1


class ForcePolygonCW(GeomOutputGeoFunc):
    arity = 1


class FromWKB(GeoFunc):
    arity = 2
    geom_param_pos = ()

    def __init__(self, expression, srid=0, **extra):
        expressions = [
            expression,
            self._handle_param(srid, "srid", int),
        ]
        if "output_field" not in extra:
            extra["output_field"] = GeometryField(srid=srid)
        super().__init__(*expressions, **extra)

    def as_oracle(self, compiler, connection, **extra_context):
        # Oracle doesn't support the srid parameter.
        pass


class FromWKT(FromWKB):
    pass


class GeoHash(GeoFunc):
    output_field = TextField()

    def __init__(self, expression, precision=None, **extra):
        expressions = [expression]
        if precision is not None:
            expressions.append(self._handle_param(precision, "precision", int))
        super().__init__(*expressions, **extra)

    def as_mysql(self, compiler, connection, **extra_context):
        pass


class GeometryDistance(GeoFunc):
    output_field = FloatField()
    arity = 2
    function = ""
    arg_joiner = " <-> "
    geom_param_pos = (0, 1)


class Intersection(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 2
    geom_param_pos = (0, 1)


@BaseSpatialField.register_lookup
class GeometryType(GeoFuncMixin, Transform):
    output_field = CharField()
    lookup_name = "geom_type"

    def as_oracle(self, compiler, connection, **extra_context):
        pass


@BaseSpatialField.register_lookup
class IsEmpty(GeoFuncMixin, Transform):
    lookup_name = "isempty"
    output_field = BooleanField()

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


@BaseSpatialField.register_lookup
class IsValid(OracleToleranceMixin, GeoFuncMixin, Transform):
    lookup_name = "isvalid"
    output_field = BooleanField()

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Length(DistanceResultMixin, OracleToleranceMixin, GeoFunc):
    def __init__(self, expr1, spheroid=True, **extra):
        self.spheroid = spheroid
        super().__init__(expr1, **extra)

    def as_sql(self, compiler, connection, **extra_context):
        if (
            self.geo_field.geodetic(connection)
            and not connection.features.supports_length_geodetic
        ):
            raise NotSupportedError(
                "This backend doesn't support Length on geodetic fields"
            )
        return super().as_sql(compiler, connection, **extra_context)

    def as_postgresql(self, compiler, connection, **extra_context):
        pass

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class LineLocatePoint(GeoFunc):
    output_field = FloatField()
    arity = 2
    geom_param_pos = (0, 1)


class MakeValid(GeomOutputGeoFunc):
    pass


class MemSize(GeoFunc):
    output_field = IntegerField()
    arity = 1


@BaseSpatialField.register_lookup
class NumDimensions(GeoFuncMixin, Transform):
    lookup_name = "num_dimensions"
    output_field = IntegerField()
    arity = 1


class NumGeometries(GeoFunc):
    output_field = IntegerField()
    arity = 1


class NumPoints(GeoFunc):
    output_field = IntegerField()
    arity = 1


class Perimeter(DistanceResultMixin, OracleToleranceMixin, GeoFunc):
    arity = 1

    def as_postgresql(self, compiler, connection, **extra_context):
        pass

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class PointOnSurface(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 1


class Reverse(GeoFunc):
    arity = 1


class Rotate(GeomOutputGeoFunc):
    def __init__(self, expression, angle, origin=None, **extra):
        expressions = [
            expression,
            self._handle_param(angle, "angle", NUMERIC_TYPES),
        ]
        if origin is not None:
            if not isinstance(origin, Point):
                raise TypeError("origin argument must be a Point")
            expressions.append(Value(origin.wkt, output_field=GeometryField()))
        super().__init__(*expressions, **extra)


class Scale(SQLiteDecimalToFloatMixin, GeomOutputGeoFunc):
    def __init__(self, expression, x, y, z=0.0, **extra):
        expressions = [
            expression,
            self._handle_param(x, "x", NUMERIC_TYPES),
            self._handle_param(y, "y", NUMERIC_TYPES),
        ]
        if z != 0.0:
            expressions.append(self._handle_param(z, "z", NUMERIC_TYPES))
        super().__init__(*expressions, **extra)


class SnapToGrid(SQLiteDecimalToFloatMixin, GeomOutputGeoFunc):
    def __init__(self, expression, *args, **extra):
        nargs = len(args)
        expressions = [expression]
        if nargs in (1, 2):
            expressions.extend(
                [self._handle_param(arg, "", NUMERIC_TYPES) for arg in args]
            )
        elif nargs == 4:
            # Reverse origin and size param ordering
            expressions += [
                *(self._handle_param(arg, "", NUMERIC_TYPES) for arg in args[2:]),
                *(self._handle_param(arg, "", NUMERIC_TYPES) for arg in args[0:2]),
            ]
        else:
            raise ValueError("Must provide 1, 2, or 4 arguments to `SnapToGrid`.")
        super().__init__(*expressions, **extra)


class SymDifference(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 2
    geom_param_pos = (0, 1)


class Transform(GeomOutputGeoFunc):
    def __init__(self, expression, srid, **extra):
        expressions = [
            expression,
            self._handle_param(srid, "srid", int),
        ]
        if "output_field" not in extra:
            extra["output_field"] = GeometryField(srid=srid)
        super().__init__(*expressions, **extra)


class Translate(Scale):
    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Union(OracleToleranceMixin, GeomOutputGeoFunc):
    arity = 2
    geom_param_pos = (0, 1)
