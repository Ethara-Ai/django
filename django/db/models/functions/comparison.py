"""Database functions that do comparisons or type conversions."""

from django.db.models.expressions import Func, Value
from django.utils.regex_helper import _lazy_re_compile


class Cast(Func):
    """Coerce an expression to a new field type."""

    function = "CAST"
    template = "%(function)s(%(expressions)s AS %(db_type)s)"

    def __init__(self, expression, output_field):
        super().__init__(expression, output_field=output_field)

    def as_sql(self, compiler, connection, **extra_context):
        extra_context["db_type"] = self.output_field.cast_db_type(connection)
        return super().as_sql(compiler, connection, **extra_context)

    def as_sqlite(self, compiler, connection, **extra_context):
        pass

    def as_mysql(self, compiler, connection, **extra_context):
        pass

    def as_postgresql(self, compiler, connection, **extra_context):
        # CAST would be valid too, but the :: shortcut syntax is more readable.
        # 'expressions' is wrapped in parentheses in case it's a complex
        # expression.
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class Coalesce(Func):
    """Return, from left to right, the first non-null expression."""

    function = "COALESCE"

    def __init__(self, *expressions, **extra):
        if len(expressions) < 2:
            raise ValueError("Coalesce must take at least two expressions")
        super().__init__(*expressions, **extra)

    @property
    def empty_result_set_value(self):
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        # Oracle prohibits mixing TextField, JSONField (NCLOB) and CharField
        # (NVARCHAR2), so convert all fields to NCLOB when that type is
        # expected.
        pass


class Collate(Func):
    function = "COLLATE"
    template = "%(expressions)s %(function)s %(collation)s"
    allowed_default = False
    # Inspired from
    # https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS
    collation_re = _lazy_re_compile(r"^[\w-]+$")

    def __init__(self, expression, collation):
        if not (collation and self.collation_re.match(collation)):
            raise ValueError("Invalid collation name: %r." % collation)
        self.collation = collation
        super().__init__(expression)

    def as_sql(self, compiler, connection, **extra_context):
        extra_context.setdefault("collation", connection.ops.quote_name(self.collation))
        return super().as_sql(compiler, connection, **extra_context)


class Greatest(Func):
    """
    Return the maximum expression.

    If any expression is null the return value is database-specific:
    On PostgreSQL, the maximum not-null expression is returned.
    On MySQL, Oracle, and SQLite, if any expression is null, null is returned.
    """

    function = "GREATEST"

    def __init__(self, *expressions, **extra):
        if len(expressions) < 2:
            raise ValueError("Greatest must take at least two expressions")
        super().__init__(*expressions, **extra)

    def as_sqlite(self, compiler, connection, **extra_context):
        """Use the MAX function on SQLite."""
        pass


class Least(Func):
    """
    Return the minimum expression.

    If any expression is null the return value is database-specific:
    On PostgreSQL, return the minimum not-null expression.
    On MySQL, Oracle, and SQLite, if any expression is null, return null.
    """

    function = "LEAST"

    def __init__(self, *expressions, **extra):
        if len(expressions) < 2:
            raise ValueError("Least must take at least two expressions")
        super().__init__(*expressions, **extra)

    def as_sqlite(self, compiler, connection, **extra_context):
        """Use the MIN function on SQLite."""
        pass


class NullIf(Func):
    function = "NULLIF"
    arity = 2

    def as_oracle(self, compiler, connection, **extra_context):
        pass
