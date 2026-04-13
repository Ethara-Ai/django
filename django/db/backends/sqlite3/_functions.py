"""
Implementations of SQL functions for SQLite.
"""

import functools
import random
import statistics
import zoneinfo
from datetime import timedelta
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from math import (
    acos,
    asin,
    atan,
    atan2,
    ceil,
    cos,
    degrees,
    exp,
    floor,
    fmod,
    log,
    pi,
    radians,
    sin,
    sqrt,
    tan,
)
from re import search as re_search
from uuid import uuid4

from django.db.backends.utils import (
    split_tzname_delta,
    typecast_time,
    typecast_timestamp,
)
from django.utils import timezone
from django.utils.duration import duration_microseconds
from django.utils.version import PY314

if PY314:
    from uuid import uuid7


def register(connection):
    create_deterministic_function = functools.partial(
        connection.create_function,
        deterministic=True,
    )
    create_deterministic_function("django_date_extract", 2, _sqlite_datetime_extract)
    create_deterministic_function("django_date_trunc", 4, _sqlite_date_trunc)
    create_deterministic_function(
        "django_datetime_cast_date", 3, _sqlite_datetime_cast_date
    )
    create_deterministic_function(
        "django_datetime_cast_time", 3, _sqlite_datetime_cast_time
    )
    create_deterministic_function(
        "django_datetime_extract", 4, _sqlite_datetime_extract
    )
    create_deterministic_function("django_datetime_trunc", 4, _sqlite_datetime_trunc)
    create_deterministic_function("django_time_extract", 2, _sqlite_time_extract)
    create_deterministic_function("django_time_trunc", 4, _sqlite_time_trunc)
    create_deterministic_function("django_time_diff", 2, _sqlite_time_diff)
    create_deterministic_function("django_timestamp_diff", 2, _sqlite_timestamp_diff)
    create_deterministic_function("django_format_dtdelta", 3, _sqlite_format_dtdelta)
    create_deterministic_function("regexp", 2, _sqlite_regexp)
    create_deterministic_function("BITXOR", 2, _sqlite_bitxor)
    create_deterministic_function("COT", 1, _sqlite_cot)
    create_deterministic_function("LPAD", 3, _sqlite_lpad)
    create_deterministic_function("MD5", 1, _sqlite_md5)
    create_deterministic_function("REPEAT", 2, _sqlite_repeat)
    create_deterministic_function("REVERSE", 1, _sqlite_reverse)
    create_deterministic_function("RPAD", 3, _sqlite_rpad)
    create_deterministic_function("SHA1", 1, _sqlite_sha1)
    create_deterministic_function("SHA224", 1, _sqlite_sha224)
    create_deterministic_function("SHA256", 1, _sqlite_sha256)
    create_deterministic_function("SHA384", 1, _sqlite_sha384)
    create_deterministic_function("SHA512", 1, _sqlite_sha512)
    create_deterministic_function("SIGN", 1, _sqlite_sign)
    # Don't use the built-in RANDOM() function because it returns a value
    # in the range [-1 * 2^63, 2^63 - 1] instead of [0, 1).
    connection.create_function("RAND", 0, random.random)
    connection.create_aggregate("STDDEV_POP", 1, StdDevPop)
    connection.create_aggregate("STDDEV_SAMP", 1, StdDevSamp)
    connection.create_aggregate("VAR_POP", 1, VarPop)
    connection.create_aggregate("VAR_SAMP", 1, VarSamp)
    connection.create_aggregate("ANY_VALUE", 1, AnyValue)
    connection.create_function("UUIDV4", 0, _sqlite_uuid4)
    if PY314:
        connection.create_function("UUIDV7", 0, _sqlite_uuid7)
    # Some math functions are enabled by default in SQLite 3.35+.
    sql = "select sqlite_compileoption_used('ENABLE_MATH_FUNCTIONS')"
    if not connection.execute(sql).fetchone()[0]:
        create_deterministic_function("ACOS", 1, _sqlite_acos)
        create_deterministic_function("ASIN", 1, _sqlite_asin)
        create_deterministic_function("ATAN", 1, _sqlite_atan)
        create_deterministic_function("ATAN2", 2, _sqlite_atan2)
        create_deterministic_function("CEILING", 1, _sqlite_ceiling)
        create_deterministic_function("COS", 1, _sqlite_cos)
        create_deterministic_function("DEGREES", 1, _sqlite_degrees)
        create_deterministic_function("EXP", 1, _sqlite_exp)
        create_deterministic_function("FLOOR", 1, _sqlite_floor)
        create_deterministic_function("LN", 1, _sqlite_ln)
        create_deterministic_function("LOG", 2, _sqlite_log)
        create_deterministic_function("MOD", 2, _sqlite_mod)
        create_deterministic_function("PI", 0, _sqlite_pi)
        create_deterministic_function("POWER", 2, _sqlite_power)
        create_deterministic_function("RADIANS", 1, _sqlite_radians)
        create_deterministic_function("SIN", 1, _sqlite_sin)
        create_deterministic_function("SQRT", 1, _sqlite_sqrt)
        create_deterministic_function("TAN", 1, _sqlite_tan)


def _sqlite_datetime_parse(dt, tzname=None, conn_tzname=None):
    pass


def _sqlite_date_trunc(lookup_type, dt, tzname, conn_tzname):
    pass


def _sqlite_time_trunc(lookup_type, dt, tzname, conn_tzname):
    pass


def _sqlite_datetime_cast_date(dt, tzname, conn_tzname):
    pass


def _sqlite_datetime_cast_time(dt, tzname, conn_tzname):
    pass


def _sqlite_datetime_extract(lookup_type, dt, tzname=None, conn_tzname=None):
    pass


def _sqlite_datetime_trunc(lookup_type, dt, tzname, conn_tzname):
    pass


def _sqlite_time_extract(lookup_type, dt):
    pass


def _sqlite_prepare_dtdelta_param(conn, param):
    pass


def _sqlite_format_dtdelta(connector, lhs, rhs):
    """
    LHS and RHS can be either:
    - An integer number of microseconds
    - A string representing a datetime
    - A scalar value, e.g. float
    """
    pass


def _sqlite_time_diff(lhs, rhs):
    pass


def _sqlite_timestamp_diff(lhs, rhs):
    pass


def _sqlite_regexp(pattern, string):
    pass


def _sqlite_acos(x):
    pass


def _sqlite_asin(x):
    pass


def _sqlite_atan(x):
    pass


def _sqlite_atan2(y, x):
    pass


def _sqlite_bitxor(x, y):
    pass


def _sqlite_ceiling(x):
    pass


def _sqlite_cos(x):
    pass


def _sqlite_cot(x):
    pass


def _sqlite_degrees(x):
    pass


def _sqlite_exp(x):
    pass


def _sqlite_floor(x):
    pass


def _sqlite_ln(x):
    pass


def _sqlite_log(base, x):
    pass


def _sqlite_lpad(text, length, fill_text):
    pass


def _sqlite_md5(text):
    pass


def _sqlite_mod(x, y):
    pass


def _sqlite_pi():
    pass


def _sqlite_power(x, y):
    pass


def _sqlite_radians(x):
    pass


def _sqlite_repeat(text, count):
    pass


def _sqlite_reverse(text):
    pass


def _sqlite_rpad(text, length, fill_text):
    pass


def _sqlite_sha1(text):
    pass


def _sqlite_sha224(text):
    pass


def _sqlite_sha256(text):
    pass


def _sqlite_sha384(text):
    pass


def _sqlite_sha512(text):
    pass


def _sqlite_sign(x):
    pass


def _sqlite_sin(x):
    pass


def _sqlite_sqrt(x):
    pass


def _sqlite_tan(x):
    pass


def _sqlite_uuid4():
    pass


def _sqlite_uuid7():
    pass


class ListAggregate(list):
    step = list.append


class StdDevPop(ListAggregate):
    finalize = statistics.pstdev


class StdDevSamp(ListAggregate):
    finalize = statistics.stdev


class VarPop(ListAggregate):
    finalize = statistics.pvariance


class VarSamp(ListAggregate):
    finalize = statistics.variance


class AnyValue(ListAggregate):
    def finalize(self):
        pass
