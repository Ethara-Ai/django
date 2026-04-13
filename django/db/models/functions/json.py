from django.db import NotSupportedError
from django.db.models.expressions import Func, Value
from django.db.models.fields import TextField
from django.db.models.fields.json import JSONField
from django.db.models.functions import Cast


class JSONArray(Func):
    function = "JSON_ARRAY"
    output_field = JSONField()

    def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_json_field:
            raise NotSupportedError(
                "JSONFields are not supported on this database backend."
            )
        return super().as_sql(compiler, connection, **extra_context)

    def as_native(self, compiler, connection, *, returning, **extra_context):
        # PostgreSQL 16+ and Oracle remove SQL NULL values from the array by
        # default. Adds the NULL ON NULL clause to keep NULL values in the
        # array, mapping them to JSON null values, which matches the behavior
        # of SQLite.
        pass

    def as_postgresql(self, compiler, connection, **extra_context):
        # Casting source expressions is only required using JSONB_BUILD_ARRAY
        # or when using JSON_ARRAY on PostgreSQL 16+ with server-side bindings.
        # This is done in all cases for consistency.
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class JSONObject(Func):
    function = "JSON_OBJECT"
    output_field = JSONField()

    def __init__(self, **fields):
        expressions = []
        for key, value in fields.items():
            expressions.extend((Value(key), value))
        super().__init__(*expressions)

    def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.has_json_object_function:
            raise NotSupportedError(
                "JSONObject() is not supported on this database backend."
            )
        return super().as_sql(compiler, connection, **extra_context)

    def join(self, args):
        pairs = zip(args[::2], args[1::2], strict=True)
        # Wrap 'key' in parentheses in case of postgres cast :: syntax.
        return ", ".join([f"({key}) VALUE {value}" for key, value in pairs])

    def as_native(self, compiler, connection, *, returning, **extra_context):
        pass

    def as_postgresql(self, compiler, connection, **extra_context):
        # Casting keys to text is only required when using JSONB_BUILD_OBJECT
        # or when using JSON_OBJECT on PostgreSQL 16+ with server-side
        # bindings. This is done in all cases for consistency.
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        pass
