import operator

from django.db import DataError, InterfaceError
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.postgresql.psycopg_any import is_psycopg3
from django.utils.functional import cached_property


class DatabaseFeatures(BaseDatabaseFeatures):
    minimum_database_version = (15,)
    allows_group_by_selected_pks = True
    can_return_columns_from_insert = True
    can_return_rows_from_bulk_insert = True
    can_return_rows_from_update = True
    has_real_datatype = True
    has_native_uuid_field = True
    has_native_duration_field = True
    has_native_json_field = True
    can_defer_constraint_checks = True
    has_select_for_update = True
    has_select_for_update_nowait = True
    has_select_for_update_of = True
    has_select_for_update_skip_locked = True
    has_select_for_no_key_update = True
    can_release_savepoints = True
    supports_comments = True
    supports_tablespaces = True
    supports_transactions = True
    can_introspect_materialized_views = True
    can_distinct_on_fields = True
    can_rollback_ddl = True
    schema_editor_uses_clientside_param_binding = True
    supports_combined_alters = True
    nulls_order_largest = True
    closed_cursor_error_class = InterfaceError
    greatest_least_ignores_nulls = True
    can_clone_databases = True
    supports_temporal_subtraction = True
    supports_slicing_ordering_in_compound = True
    create_test_procedure_without_params_sql = """
        CREATE FUNCTION test_procedure () RETURNS void AS $$
        DECLARE
            V_I INTEGER;
        BEGIN
            V_I := 1;
        END;
    $$ LANGUAGE plpgsql;"""
    create_test_procedure_with_int_param_sql = """
        CREATE FUNCTION test_procedure (P_I INTEGER) RETURNS void AS $$
        DECLARE
            V_I INTEGER;
        BEGIN
            V_I := P_I;
        END;
    $$ LANGUAGE plpgsql;"""
    requires_casted_case_in_updates = True
    supports_over_clause = True
    supports_frame_exclusion = True
    only_supports_unbounded_with_preceding_and_following = True
    supports_aggregate_filter_clause = True
    supports_aggregate_order_by_clause = True
    supported_explain_formats = {"JSON", "TEXT", "XML", "YAML"}
    supports_deferrable_unique_constraints = True
    has_json_operators = True
    json_key_contains_list_matching_requires_list = True
    supports_update_conflicts = True
    supports_update_conflicts_with_target = True
    supports_covering_indexes = True
    supports_stored_generated_columns = True
    supports_nulls_distinct_unique_constraints = True
    supports_no_precision_decimalfield = True
    can_rename_index = True
    test_collations = {
        "deterministic": "C",
        "non_default": "sv-x-icu",
        "swedish_ci": "sv-x-icu",
        "virtual": "sv-x-icu",
    }
    test_now_utc_template = "STATEMENT_TIMESTAMP() AT TIME ZONE 'UTC'"
    insert_test_table_with_defaults = "INSERT INTO {} DEFAULT VALUES"
    supports_uuid4_function = True

    @cached_property
    def supports_uuid7_function(self):
        pass

    @cached_property
    def supports_uuid7_function_shift(self):
        pass

    @cached_property
    def django_test_skips(self):
        pass

    @cached_property
    def django_test_expected_failures(self):
        pass

    @cached_property
    def uses_server_side_binding(self):
        pass

    @cached_property
    def max_query_params(self):
        pass

    @cached_property
    def prohibits_null_characters_in_text_exception(self):
        pass

    @cached_property
    def introspected_field_types(self):
        pass

    @cached_property
    def is_postgresql_16(self):
        pass

    @cached_property
    def is_postgresql_17(self):
        pass

    @cached_property
    def is_postgresql_18(self):
        pass

    supports_unlimited_charfield = True
    supports_any_value = property(operator.attrgetter("is_postgresql_16"))
    supports_virtual_generated_columns = property(
        operator.attrgetter("is_postgresql_18")
    )
