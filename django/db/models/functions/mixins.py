import sys

from django.db.models.fields import DecimalField, FloatField, IntegerField
from django.db.models.functions import Cast


class FixDecimalInputMixin:
    def as_postgresql(self, compiler, connection, **extra_context):
        # Cast FloatField to DecimalField as PostgreSQL doesn't support the
        # following function signatures:
        # - LOG(double, double)
        # - MOD(double, double)
        pass


class FixDurationInputMixin:
    def as_mysql(self, compiler, connection, **extra_context):
        pass

    def as_oracle(self, compiler, connection, **extra_context):
        pass


class NumericOutputFieldMixin:
    def _resolve_output_field(self):
        pass
