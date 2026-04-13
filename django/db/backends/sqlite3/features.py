import operator
import sqlite3

from django.db import transaction
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.utils import OperationalError
from django.utils.functional import cached_property
from django.utils.version import PY314

from .base import Database


class DatabaseFeatures(BaseDatabaseFeatures):
    minimum_database_version = (3, 37)
    test_db_allows_multiple_connections = False
    supports_unspecified_pk = True
    supports_timezones = False
    supports_transactions = True
    atomic_transactions = False
    can_rollback_ddl = True
    can_create_inline_fk = False
    requires_literal_defaults = True
    can_clone_databases = True
    supports_temporal_subtraction = True
    ignores_table_name_case = True
    supports_cast_with_precision = False
    time_cast_precision = 3
    can_release_savepoints = True
    has_case_insensitive_like = True
    supports_parentheses_in_compound = False
    can_defer_constraint_checks = True
    supports_over_clause = True
    supports_frame_range_fixed_distance = True
    supports_frame_exclusion = True
    supports_aggregate_filter_clause = True
    supports_aggregate_order_by_clause = Database.sqlite_version_info >= (3, 44, 0)
    supports_aggregate_distinct_multiple_argument = False
    supports_any_value = True
    order_by_nulls_first = True
    supports_json_field_contains = False
    supports_update_conflicts = True
    supports_update_conflicts_with_target = True
    supports_stored_generated_columns = True
    supports_virtual_generated_columns = True
    test_collations = {
        "ci": "nocase",
        "cs": "binary",
        "non_default": "nocase",
        "virtual": "nocase",
    }
    django_test_expected_failures = {
        # The django_format_dtdelta() function doesn't properly handle mixed
        # Date/DateTime fields and timedeltas.
        "expressions.tests.FTimeDeltaTests.test_mixed_comparisons1",
    }
    insert_test_table_with_defaults = 'INSERT INTO {} ("null") VALUES (1)'
    supports_default_keyword_in_insert = False
    supports_unlimited_charfield = True
    supports_no_precision_decimalfield = True
    can_return_columns_from_insert = True
    can_return_rows_from_bulk_insert = True
    can_return_rows_from_update = True
    supports_uuid4_function = True

    @cached_property
    def supports_uuid7_function(self):
        pass

    @cached_property
    def django_test_skips(self):
        pass

    @cached_property
    def introspected_field_types(self):
        pass

    @property
    def max_query_params(self):
        """
        SQLite has a variable limit per query. The limit can be changed using
        the SQLITE_MAX_VARIABLE_NUMBER compile-time option (which defaults to
        32766) or lowered per connection at run-time with
        setlimit(SQLITE_LIMIT_VARIABLE_NUMBER, N).
        """
        pass

    @cached_property
    def supports_json_field(self):
        pass

    can_introspect_json_field = property(operator.attrgetter("supports_json_field"))
    has_json_object_function = property(operator.attrgetter("supports_json_field"))
