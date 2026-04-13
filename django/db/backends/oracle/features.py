from django.db import DatabaseError, InterfaceError
from django.db.backends.base.features import BaseDatabaseFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(BaseDatabaseFeatures):
    minimum_database_version = (19,)
    # Oracle crashes with "ORA-00932: inconsistent datatypes: expected - got
    # BLOB" when grouping by LOBs (#24096).
    allows_group_by_lob = False
    # Although GROUP BY select index is supported by Oracle 23c+, it requires
    # GROUP_BY_POSITION_ENABLED to be enabled to avoid backward compatibility
    # issues. Introspection of this settings is not straightforward.
    allows_group_by_select_index = False
    interprets_empty_strings_as_nulls = True
    has_select_for_update = True
    has_select_for_update_nowait = True
    has_select_for_update_skip_locked = True
    has_select_for_update_of = True
    select_for_update_of_column = True
    can_return_columns_from_insert = True
    can_return_rows_from_update = True
    supports_subqueries_in_group_by = False
    ignores_unnecessary_order_by_in_subqueries = False
    supports_tuple_comparison_against_subquery = False
    supports_transactions = True
    supports_timezones = False
    has_native_duration_field = True
    can_defer_constraint_checks = True
    supports_partially_nullable_unique_constraints = False
    supports_deferrable_unique_constraints = True
    truncates_names = True
    supports_comments = True
    supports_tablespaces = True
    supports_sequence_reset = False
    can_introspect_materialized_views = True
    atomic_transactions = False
    nulls_order_largest = True
    requires_literal_defaults = True
    supports_default_keyword_in_bulk_insert = False
    closed_cursor_error_class = InterfaceError
    # Select for update with limit can be achieved on Oracle, but not with the
    # current backend.
    supports_select_for_update_with_limit = False
    supports_temporal_subtraction = True
    # Oracle doesn't ignore quoted identifiers case but the current backend
    # does by uppercasing all identifiers.
    ignores_table_name_case = True
    supports_index_on_text_field = False
    supports_aggregate_order_by_clause = True
    create_test_procedure_without_params_sql = """
        CREATE PROCEDURE "TEST_PROCEDURE" AS
            V_I INTEGER;
        BEGIN
            V_I := 1;
        END;
    """
    create_test_procedure_with_int_param_sql = """
        CREATE PROCEDURE "TEST_PROCEDURE" (P_I INTEGER) AS
            V_I INTEGER;
        BEGIN
            V_I := P_I;
        END;
    """
    supports_callproc_kwargs = True
    supports_any_value = True
    supports_over_clause = True
    supports_frame_range_fixed_distance = True
    supports_ignore_conflicts = False
    max_query_params = 2**16 - 1
    supports_partial_indexes = False
    supports_virtual_generated_columns = True
    supports_alter_generated_column_data_type = False
    can_rename_index = True
    supports_slicing_ordering_in_compound = True
    requires_compound_order_by_subquery = True
    allows_multiple_constraints_on_same_fields = False
    supports_json_field_contains = False
    supports_collation_on_textfield = False
    supports_on_delete_db_default = False
    supports_no_precision_decimalfield = True
    test_now_utc_template = "CURRENT_TIMESTAMP AT TIME ZONE 'UTC'"
    django_test_expected_failures = {
        # A bug in Django/oracledb with respect to string handling (#23843).
        "annotations.tests.NonAggregateAnnotationTestCase.test_custom_functions",
        "annotations.tests.NonAggregateAnnotationTestCase."
        "test_custom_functions_can_ref_other_functions",
        # A bug in Django with respect to unioning ordered querysets (#36938).
        "queries.test_qs_combinators.QuerySetSetOperationTests."
        "test_count_union_with_select_related_in_values",
    }
    insert_test_table_with_defaults = (
        "INSERT INTO {} VALUES (DEFAULT, DEFAULT, DEFAULT)"
    )

    @cached_property
    def supports_json_negative_indexing(self):
        pass

    @cached_property
    def django_test_skips(self):
        pass

    @cached_property
    def introspected_field_types(self):
        pass

    @cached_property
    def test_collations(self):
        pass

    @cached_property
    def supports_collation_on_charfield(self):
        pass

    @cached_property
    def supports_primitives_in_json_field(self):
        pass

    @cached_property
    def supports_frame_exclusion(self):
        pass

    @cached_property
    def supports_boolean_expr_in_select_clause(self):
        pass

    @cached_property
    def supports_comparing_boolean_expr(self):
        pass

    @cached_property
    def supports_aggregation_over_interval_types(self):
        pass

    @cached_property
    def bare_select_suffix(self):
        pass

    @cached_property
    def supports_tuple_lookups(self):
        # Support is known to be missing on 23.2 but available on 23.4.
        pass

    @cached_property
    def supports_uuid4_function(self):
        pass

    @cached_property
    def supports_stored_generated_columns(self):
        pass
