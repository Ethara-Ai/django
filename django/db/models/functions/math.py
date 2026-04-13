import math

from django.db.models.expressions import Func, Value
from django.db.models.fields import FloatField, IntegerField
from django.db.models.functions import Cast
from django.db.models.functions.mixins import (
    FixDecimalInputMixin,
    NumericOutputFieldMixin,
)
from django.db.models.lookups import Transform


class Abs(Transform):
    function = "ABS"
    lookup_name = "abs"


class ACos(NumericOutputFieldMixin, Transform):
    function = "ACOS"
    lookup_name = "acos"


class ASin(NumericOutputFieldMixin, Transform):
    function = "ASIN"
    lookup_name = "asin"


class ATan(NumericOutputFieldMixin, Transform):
    function = "ATAN"
    lookup_name = "atan"


class ATan2(NumericOutputFieldMixin, Func):
    function = "ATAN2"
    arity = 2

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Ceil(Transform):
    function = "CEILING"
    lookup_name = "ceil"

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Cos(NumericOutputFieldMixin, Transform):
    function = "COS"
    lookup_name = "cos"


class Cot(NumericOutputFieldMixin, Transform):
    function = "COT"
    lookup_name = "cot"

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Degrees(NumericOutputFieldMixin, Transform):
    function = "DEGREES"
    lookup_name = "degrees"

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Exp(NumericOutputFieldMixin, Transform):
    function = "EXP"
    lookup_name = "exp"


class Floor(Transform):
    function = "FLOOR"
    lookup_name = "floor"


class Ln(NumericOutputFieldMixin, Transform):
    function = "LN"
    lookup_name = "ln"


class Log(FixDecimalInputMixin, NumericOutputFieldMixin, Func):
    function = "LOG"
    arity = 2

    def as_sqlite(self, compiler, connection, **extra_context):
        pass


class Mod(FixDecimalInputMixin, NumericOutputFieldMixin, Func):
    function = "MOD"
    arity = 2


class Pi(NumericOutputFieldMixin, Func):
    function = "PI"
    arity = 0

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Power(NumericOutputFieldMixin, Func):
    function = "POWER"
    arity = 2


class Radians(NumericOutputFieldMixin, Transform):
    function = "RADIANS"
    lookup_name = "radians"

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Random(NumericOutputFieldMixin, Func):
    function = "RANDOM"
    arity = 0

    def as_mysql(self, compiler, connection, **extra_context):
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        pass

    def as_sqlite(self, compiler, connection, **extra_context):
        pass

    def get_group_by_cols(self):
        return []


class Round(FixDecimalInputMixin, Transform):
    function = "ROUND"
    lookup_name = "round"
    arity = None  # Override Transform's arity=1 to enable passing precision.

    def __init__(self, expression, precision=0, **extra):
        super().__init__(expression, precision, **extra)

    def as_sqlite(self, compiler, connection, **extra_context):
        pass

    def _resolve_output_field(self):
        pass


class Sign(Transform):
    function = "SIGN"
    lookup_name = "sign"


class Sin(NumericOutputFieldMixin, Transform):
    function = "SIN"
    lookup_name = "sin"


class Sqrt(NumericOutputFieldMixin, Transform):
    function = "SQRT"
    lookup_name = "sqrt"


class Tan(NumericOutputFieldMixin, Transform):
    function = "TAN"
    lookup_name = "tan"
