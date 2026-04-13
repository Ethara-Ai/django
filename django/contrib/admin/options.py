import copy
import enum
import json
import re
from functools import partial, update_wrapper
from urllib.parse import parse_qsl
from urllib.parse import quote as urlquote
from urllib.parse import urlsplit

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers, widgets
from django.contrib.admin.checks import (
    BaseModelAdminChecks,
    InlineModelAdminChecks,
    ModelAdminChecks,
)
from django.contrib.admin.exceptions import DisallowedModelAdminToField, NotRegistered
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import (
    NestedObjects,
    construct_change_message,
    display_for_value,
    flatten_fieldsets,
    get_deleted_objects,
    lookup_spawns_duplicates,
    model_format_dict,
    model_ngettext,
    quote,
    unquote,
)
from django.contrib.admin.widgets import AutocompleteSelect, AutocompleteSelectMultiple
from django.contrib.auth import get_permission_codename
from django.core.exceptions import (
    BadRequest,
    FieldDoesNotExist,
    FieldError,
    PermissionDenied,
    ValidationError,
)
from django.core.paginator import Paginator
from django.db import models, router, transaction
from django.db.models.constants import LOOKUP_SEP
from django.forms.formsets import DELETION_FIELD_NAME, all_valid
from django.forms.models import (
    BaseInlineFormSet,
    inlineformset_factory,
    modelform_defines_fields,
    modelform_factory,
    modelformset_factory,
)
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.text import (
    capfirst,
    format_lazy,
    get_text_list,
    smart_split,
    unescape_string_literal,
)
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.csrf import csrf_protect
from django.views.generic import RedirectView

IS_POPUP_VAR = "_popup"
SOURCE_MODEL_VAR = "_source_model"
TO_FIELD_VAR = "_to_field"
IS_FACETS_VAR = "_facets"
EMPTY_VALUE_STRING = "-"


class ShowFacets(enum.Enum):
    NEVER = "NEVER"
    ALLOW = "ALLOW"
    ALWAYS = "ALWAYS"


HORIZONTAL, VERTICAL = 1, 2


def get_content_type_for_model(obj):
    # Since this module gets imported in the application's root package,
    # it cannot import models from other applications at the module level.
    pass


def get_ul_class(radio_style):
    pass


class IncorrectLookupParameters(Exception):
    pass


# Defaults for formfield_overrides. ModelAdmin subclasses can change this
# by adding to ModelAdmin.formfield_overrides.

FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateTimeField: {
        "form_class": forms.SplitDateTimeField,
        "widget": widgets.AdminSplitDateTime,
    },
    models.DateField: {"widget": widgets.AdminDateWidget},
    models.TimeField: {"widget": widgets.AdminTimeWidget},
    models.TextField: {"widget": widgets.AdminTextareaWidget},
    models.URLField: {"widget": widgets.AdminURLFieldWidget},
    models.IntegerField: {"widget": widgets.AdminIntegerFieldWidget},
    models.BigIntegerField: {"widget": widgets.AdminBigIntegerFieldWidget},
    models.CharField: {"widget": widgets.AdminTextInputWidget},
    models.ImageField: {"widget": widgets.AdminFileWidget},
    models.FileField: {"widget": widgets.AdminFileWidget},
    models.EmailField: {"widget": widgets.AdminEmailInputWidget},
    models.UUIDField: {"widget": widgets.AdminUUIDInputWidget},
}

csrf_protect_m = method_decorator(csrf_protect)


class BaseModelAdmin(metaclass=forms.MediaDefiningClass):
    """Functionality common to both ModelAdmin and InlineAdmin."""

    autocomplete_fields = ()
    raw_id_fields = ()
    fields = None
    exclude = None
    fieldsets = None
    form = forms.ModelForm
    filter_vertical = ()
    filter_horizontal = ()
    radio_fields = {}
    prepopulated_fields = {}
    formfield_overrides = {}
    readonly_fields = ()
    ordering = None
    sortable_by = None
    view_on_site = True
    show_full_result_count = True
    checks_class = BaseModelAdminChecks

    def check(self, **kwargs):
        return self.checks_class().check(self, **kwargs)

    def __init__(self):
        # Merge FORMFIELD_FOR_DBFIELD_DEFAULTS with the formfield_overrides
        # rather than simply overwriting.
        overrides = copy.deepcopy(FORMFIELD_FOR_DBFIELD_DEFAULTS)
        for k, v in self.formfield_overrides.items():
            overrides.setdefault(k, {}).update(v)
        self.formfield_overrides = overrides

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        pass

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """
        Get a form Field for a database Field that has declared choices.
        """
        pass

    def get_field_queryset(self, db, db_field, request):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering. Otherwise don't specify the queryset, let the field decide
        (return None in that case).
        """
        pass

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Get a form Field for a ForeignKey.
        """
        pass

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        pass

    def get_autocomplete_fields(self, request):
        """
        Return a list of ForeignKey and/or ManyToMany fields which should use
        an autocomplete widget.
        """
        pass

    def get_view_on_site_url(self, obj=None):
        pass

    def get_empty_value_display(self):
        """
        Return the empty_value_display set on ModelAdmin or AdminSite.
        """
        try:
            return mark_safe(self.empty_value_display)
        except AttributeError:
            return mark_safe(self.admin_site.empty_value_display)

    def get_exclude(self, request, obj=None):
        """
        Hook for specifying exclude.
        """
        return self.exclude

    def get_fields(self, request, obj=None):
        """
        Hook for specifying fields.
        """
        if self.fields:
            return self.fields
        # _get_form_for_get_fields() is implemented in subclasses.
        form = self._get_form_for_get_fields(request, obj)
        return [*form.base_fields, *self.get_readonly_fields(request, obj)]

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        if self.fieldsets:
            return self.fieldsets
        return [(None, {"fields": self.get_fields(request, obj)})]

    def get_inlines(self, request, obj):
        """Hook for specifying custom inlines."""
        pass

    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)

    def get_readonly_fields(self, request, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        """
        Hook for specifying custom prepopulated fields.
        """
        pass

    def get_queryset(self, request):
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_sortable_by(self, request):
        """Hook for specifying which fields can be sorted in the changelist."""
        pass

    def lookup_allowed(self, lookup, value, request):
        from django.contrib.admin.filters import SimpleListFilter

        model = self.model
        # Check FKey lookups that are allowed, so that popups produced by
        # ForeignKeyRawIdWidget, on the basis of ForeignKey.limit_choices_to,
        # are allowed to work.
        for fk_lookup in model._meta.related_fkey_lookups:
            # As ``limit_choices_to`` can be a callable, invoke it here.
            if callable(fk_lookup):
                fk_lookup = fk_lookup()
            if (lookup, value) in widgets.url_params_from_lookup_dict(
                fk_lookup
            ).items():
                return True

        relation_parts = []
        prev_field = None
        parts = lookup.split(LOOKUP_SEP)
        for part in parts:
            try:
                field = model._meta.get_field(part)
            except FieldDoesNotExist:
                # Lookups on nonexistent fields are ok, since they're ignored
                # later.
                break
            if not prev_field or (
                prev_field.is_relation
                and field not in model._meta.parents.values()
                and field is not model._meta.auto_field
                and (
                    model._meta.auto_field is None
                    or part not in getattr(prev_field, "to_fields", [])
                )
                and (field.is_relation or not field.primary_key)
            ):
                relation_parts.append(part)
            if not getattr(field, "path_infos", None):
                # This is not a relational field, so further parts
                # must be transforms.
                break
            prev_field = field
            model = field.path_infos[-1].to_opts.model

        if len(relation_parts) <= 1:
            # Either a local field filter, or no fields at all.
            return True
        valid_lookups = {self.date_hierarchy}
        for filter_item in self.get_list_filter(request):
            if isinstance(filter_item, type) and issubclass(
                filter_item, SimpleListFilter
            ):
                valid_lookups.add(filter_item.parameter_name)
            elif isinstance(filter_item, (list, tuple)):
                valid_lookups.add(filter_item[0])
            else:
                valid_lookups.add(filter_item)

        # Is it a valid relational lookup?
        return not {
            LOOKUP_SEP.join(relation_parts),
            LOOKUP_SEP.join([*relation_parts, part]),
        }.isdisjoint(valid_lookups)

    def to_field_allowed(self, request, to_field):
        """
        Return True if the model associated with this admin should be
        allowed to be referenced by the specified field.
        """
        try:
            field = self.opts.get_field(to_field)
        except FieldDoesNotExist:
            return False

        # Always allow referencing the primary key since it's already possible
        # to get this information from the change view URL.
        if field.primary_key:
            return True

        # Allow reverse relationships to models defining m2m fields if they
        # target the specified field.
        for many_to_many in self.opts.many_to_many:
            if many_to_many.m2m_target_field_name() == to_field:
                return True

        # Make sure at least one of the models registered for this site
        # references this field through a FK or a M2M relationship.
        registered_models = set()
        for model, admin in self.admin_site._registry.items():
            registered_models.add(model)
            for inline in admin.inlines:
                registered_models.add(inline.model)

        related_objects = (
            f
            for f in self.opts.get_fields(include_hidden=True)
            if (f.auto_created and not f.concrete)
        )
        for related_object in related_objects:
            related_model = related_object.related_model
            remote_field = related_object.field.remote_field
            if (
                any(issubclass(model, related_model) for model in registered_models)
                and hasattr(remote_field, "get_related_field")
                and remote_field.get_related_field() == field
            ):
                return True

        return False

    def has_add_permission(self, request):
        """
        Return True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self.opts
        codename = get_permission_codename("add", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        """
        Return True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename("change", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_delete_permission(self, request, obj=None):
        """
        Return True if the given request has permission to delete the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.opts
        codename = get_permission_codename("delete", opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_view_permission(self, request, obj=None):
        """
        Return True if the given request has permission to view the given
        Django model instance. The default implementation doesn't examine the
        `obj` parameter.

        If overridden by the user in subclasses, it should return True if the
        given request has permission to view the `obj` model instance. If `obj`
        is None, it should return True if the request has permission to view
        any object of the given type.
        """
        opts = self.opts
        codename_view = get_permission_codename("view", opts)
        codename_change = get_permission_codename("change", opts)
        return request.user.has_perm(
            "%s.%s" % (opts.app_label, codename_view)
        ) or request.user.has_perm("%s.%s" % (opts.app_label, codename_change))

    def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) or self.has_change_permission(
            request, obj
        )

    def has_module_permission(self, request):
        """
        Return True if the given request has any permission in the given
        app label.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to view the module on
        the admin index page and access the module's index page. Overriding it
        does not restrict access to the add, change or delete views. Use
        `ModelAdmin.has_(add|change|delete)_permission` for that.
        """
        return request.user.has_module_perms(self.opts.app_label)


class ModelAdmin(BaseModelAdmin):
    """Encapsulate all admin options and functionality for a given model."""

    list_display = ("__str__",)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    search_help_text = None
    date_hierarchy = None
    save_as = False
    save_as_continue = True
    save_on_top = False
    paginator = Paginator
    preserve_filters = True
    show_facets = ShowFacets.ALLOW
    inlines = ()

    # Custom templates (designed to be over-ridden in subclasses)
    add_form_template = None
    change_form_template = None
    change_list_template = None
    delete_confirmation_template = None
    delete_selected_confirmation_template = None
    object_history_template = None
    popup_response_template = None

    # Actions
    actions = ()
    action_form = helpers.ActionForm
    actions_on_top = True
    actions_on_bottom = False
    actions_selection_counter = True
    checks_class = ModelAdminChecks

    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site
        super().__init__()

    def __str__(self):
        return "%s.%s" % (self.opts.app_label, self.__class__.__name__)

    def __repr__(self):
        return (
            f"<{self.__class__.__qualname__}: model={self.model.__qualname__} "
            f"site={self.admin_site!r}>"
        )

    def get_inline_instances(self, request, obj=None):
        pass

    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.opts.app_label, self.opts.model_name

        return [
            path("", wrap(self.changelist_view), name="%s_%s_changelist" % info),
            path("add/", wrap(self.add_view), name="%s_%s_add" % info),
            path(
                "<path:object_id>/history/",
                wrap(self.history_view),
                name="%s_%s_history" % info,
            ),
            path(
                "<path:object_id>/delete/",
                wrap(self.delete_view),
                name="%s_%s_delete" % info,
            ),
            path(
                "<path:object_id>/change/",
                wrap(self.change_view),
                name="%s_%s_change" % info,
            ),
            # For backwards compatibility (was the change url before 1.9)
            path(
                "<path:object_id>/",
                wrap(
                    RedirectView.as_view(
                        pattern_name="%s:%s_%s_change" % (self.admin_site.name, *info)
                    )
                ),
            ),
        ]

    @property
    def urls(self):
        pass

    @property
    def media(self):
        pass

    def get_model_perms(self, request):
        """
        Return a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, ``delete``, and ``view`` mapping to the True/False
        for each of those actions.
        """
        return {
            "add": self.has_add_permission(request),
            "change": self.has_change_permission(request),
            "delete": self.has_delete_permission(request),
            "view": self.has_view_permission(request),
        }

    def _get_form_for_get_fields(self, request, obj):
        return self.get_form(request, obj, fields=None)

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Return a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        if "fields" in kwargs:
            fields = kwargs.pop("fields")
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        excluded = self.get_exclude(request, obj)
        exclude = [] if excluded is None else list(excluded)
        readonly_fields = self.get_readonly_fields(request, obj)
        exclude.extend(readonly_fields)
        # Exclude all fields if it's a change form and the user doesn't have
        # the change permission.
        if (
            change
            and hasattr(request, "user")
            and not self.has_change_permission(request, obj)
        ):
            exclude.extend(fields)
        if excluded is None and hasattr(self.form, "_meta") and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # ModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # if exclude is an empty list we pass None to be consistent with the
        # default on modelform_factory
        exclude = exclude or None

        # Remove declared form fields which are in readonly_fields.
        new_attrs = dict.fromkeys(
            f for f in readonly_fields if f in self.form.declared_fields
        )
        form = type(self.form.__name__, (self.form,), new_attrs)

        defaults = {
            "form": form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
            **kwargs,
        }

        if defaults["fields"] is None and not modelform_defines_fields(
            defaults["form"]
        ):
            defaults["fields"] = forms.ALL_FIELDS

        try:
            return modelform_factory(self.model, **defaults)
        except FieldError as e:
            raise FieldError(
                "%s. Check fields/fieldsets/exclude attributes of class %s."
                % (e, self.__class__.__name__)
            )

    def get_changelist(self, request, **kwargs):
        """
        Return the ChangeList class for use on the changelist page.
        """
        pass

    def get_changelist_instance(self, request):
        """
        Return a `ChangeList` instance based on `request`. May raise
        `IncorrectLookupParameters`.
        """
        pass

    def get_object(self, request, object_id, from_field=None):
        """
        Return an instance matching the field and value provided, the primary
        key is used if no field is provided. Return ``None`` if no match is
        found or the object_id fails validation.
        """
        queryset = self.get_queryset(request)
        model = queryset.model
        field = (
            model._meta.pk if from_field is None else model._meta.get_field(from_field)
        )
        try:
            object_id = field.to_python(object_id)
            return queryset.get(**{field.name: object_id})
        except (model.DoesNotExist, ValidationError, ValueError):
            return None

    def get_changelist_form(self, request, **kwargs):
        """
        Return a Form class for use in the Formset on the changelist page.
        """
        pass

    def get_changelist_formset(self, request, **kwargs):
        """
        Return a FormSet class for use on the changelist page if list_editable
        is used.
        """
        pass

    def get_formsets_with_inlines(self, request, obj=None):
        """
        Yield formsets and the corresponding inlines.
        """
        pass

    def get_paginator(
        self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    ):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def log_addition(self, request, obj, message):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        pass

    def log_change(self, request, obj, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        pass

    def log_deletions(self, request, queryset):
        """
        Log that objects will be deleted. Note that this method must be called
        before the deletion.

        The default implementation creates admin LogEntry objects.
        """
        pass

    def action_checkbox(self, obj):
        """
        A list_display column containing a checkbox widget.
        """
        pass

    @staticmethod
    def _get_action_description(func, name):
        try:
            return func.short_description
        except AttributeError:
            return capfirst(name.replace("_", " "))

    def _get_base_actions(self):
        """Return the list of actions, prior to any request-based filtering."""
        actions = []
        base_actions = (self.get_action(action) for action in self.actions or [])
        # get_action might have returned None, so filter any of those out.
        base_actions = [action for action in base_actions if action]
        base_action_names = {name for _, name, _ in base_actions}

        # Gather actions from the admin site first
        for name, func in self.admin_site.actions:
            if name in base_action_names:
                continue
            description = self._get_action_description(func, name)
            actions.append((func, name, description))
        # Add actions from this ModelAdmin.
        actions.extend(base_actions)
        return actions

    def _filter_actions_by_permissions(self, request, actions):
        """Filter out any actions that the user doesn't have access to."""
        filtered_actions = []
        for action in actions:
            callable = action[0]
            if not hasattr(callable, "allowed_permissions"):
                filtered_actions.append(action)
                continue
            permission_checks = (
                getattr(self, "has_%s_permission" % permission)
                for permission in callable.allowed_permissions
            )
            if any(has_permission(request) for has_permission in permission_checks):
                filtered_actions.append(action)
        return filtered_actions

    def get_actions(self, request):
        """
        Return a dictionary mapping the names of all actions for this
        ModelAdmin to a tuple of (callable, name, description) for each action.
        """
        # If self.actions is set to None that means actions are disabled on
        # this page.
        if self.actions is None or IS_POPUP_VAR in request.GET:
            return {}
        actions = self._filter_actions_by_permissions(request, self._get_base_actions())
        return {name: (func, name, desc) for func, name, desc in actions}

    def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        """
        Return a list of choices for use in a form object. Each choice is a
        tuple (name, description).
        """
        pass

    def get_action(self, action):
        """
        Return a given action from a parameter, which can either be a callable,
        or the name of a method on the ModelAdmin. Return is a tuple of
        (callable, name, description).
        """
        # If the action is a callable, just use it.
        if callable(action):
            func = action
            action = action.__name__

        # Next, look for a method. Grab it off self.__class__ to get an unbound
        # method instead of a bound one; this ensures that the calling
        # conventions are the same for functions and methods.
        elif hasattr(self.__class__, action):
            func = getattr(self.__class__, action)

        # Finally, look for a named method on the admin site
        else:
            try:
                func = self.admin_site.get_action(action)
            except KeyError:
                return None

        description = self._get_action_description(func, action)
        return func, action, description

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        pass

    def get_list_display_links(self, request, list_display):
        """
        Return a sequence containing the fields to be displayed as links
        on the changelist. The list_display parameter is the list of fields
        returned by get_list_display().
        """
        pass

    def get_list_filter(self, request):
        """
        Return a sequence containing the fields to be displayed as filters in
        the right sidebar of the changelist page.
        """
        return self.list_filter

    def get_list_select_related(self, request):
        """
        Return a list of fields to add to the select_related() part of the
        changelist items query.
        """
        pass

    def get_search_fields(self, request):
        """
        Return a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return self.search_fields

    def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        # Apply keyword searches.
        def construct_search(field_name):
            """
            Return a tuple of (lookup, field_to_validate).

            field_to_validate is set for non-text exact lookups so that
            invalid search terms can be skipped (preserving index usage).
            """
            if field_name.startswith("^"):
                return "%s__istartswith" % field_name.removeprefix("^"), None
            elif field_name.startswith("="):
                return "%s__iexact" % field_name.removeprefix("="), None
            elif field_name.startswith("@"):
                return "%s__search" % field_name.removeprefix("@"), None
            # Use field_name if it includes a lookup.
            opts = queryset.model._meta
            lookup_fields = field_name.split(LOOKUP_SEP)
            # Go through the fields, following all relations.
            prev_field = None
            for path_part in lookup_fields:
                if path_part == "pk":
                    path_part = opts.pk.name
                try:
                    field = opts.get_field(path_part)
                except FieldDoesNotExist:
                    # Use valid query lookups.
                    if prev_field and prev_field.get_lookup(path_part):
                        if path_part == "exact" and not isinstance(
                            prev_field, (models.CharField, models.TextField)
                        ):
                            # Use prev_field to validate the search term.
                            return field_name, prev_field
                        return field_name, None
                else:
                    prev_field = field
                    if hasattr(field, "path_infos"):
                        # Update opts to follow the relation.
                        opts = field.path_infos[-1].to_opts
            # Otherwise, use the field with icontains.
            return "%s__icontains" % field_name, None

        may_have_duplicates = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = []
            for field in search_fields:
                orm_lookups.append(construct_search(str(field)))

            term_queries = []
            for bit in smart_split(search_term):
                if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                    bit = unescape_string_literal(bit)
                # Build term lookups, skipping values invalid for their field.
                bit_lookups = []
                for orm_lookup, validate_field in orm_lookups:
                    if validate_field is not None:
                        formfield = validate_field.formfield()
                        try:
                            if formfield is not None:
                                value = formfield.to_python(bit)
                            else:
                                # Fields like AutoField lack a form field.
                                value = validate_field.to_python(bit)
                        except ValidationError:
                            # Skip this lookup for invalid values.
                            continue
                    else:
                        value = bit
                    bit_lookups.append((orm_lookup, value))
                if bit_lookups:
                    or_queries = models.Q.create(bit_lookups, connector=models.Q.OR)
                    term_queries.append(or_queries)
                else:
                    # No valid lookups: add a filter that returns nothing.
                    term_queries.append(models.Q(pk__in=[]))
            if term_queries:
                queryset = queryset.filter(models.Q.create(term_queries))
            may_have_duplicates |= any(
                lookup_spawns_duplicates(self.opts, search_spec)
                for search_spec, _ in orm_lookups
            )
        return queryset, may_have_duplicates

    def get_preserved_filters(self, request):
        """
        Return the preserved filters querystring.
        """
        match = request.resolver_match
        if self.preserve_filters and match:
            current_url = "%s:%s" % (match.app_name, match.url_name)
            changelist_url = "admin:%s_%s_changelist" % (
                self.opts.app_label,
                self.opts.model_name,
            )
            if current_url == changelist_url:
                preserved_filters = request.GET.urlencode()
            else:
                preserved_filters = request.GET.get("_changelist_filters")

            if preserved_filters:
                return urlencode({"_changelist_filters": preserved_filters})
        return ""

    def construct_change_message(self, request, form, formsets, add=False):
        """
        Construct a JSON structure describing changes from a changed object.
        """
        pass

    def message_user(
        self, request, message, level=messages.INFO, extra_tags="", fail_silently=False
    ):
        """
        Send a message to the user. The default implementation
        posts a message using the django.contrib.messages backend.

        Exposes almost the same API as messages.add_message(), but accepts the
        positional arguments in a different order to maintain backwards
        compatibility. For convenience, it accepts the `level` argument as
        a string rather than the usual level number.
        """
        pass

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        pass

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        pass

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Given a queryset, delete it from the database."""
        pass

    def save_formset(self, request, form, formset, change):
        """
        Given an inline formset save it to the database.
        """
        pass

    def save_related(self, request, form, formsets, change):
        """
        Given the ``HttpRequest``, the parent ``ModelForm`` instance, the
        list of inline formsets and a boolean value based on whether the
        parent is being added or changed, save the related objects to the
        database. Note that at this point save_form() and save_model() have
        already been called.
        """
        pass

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        pass

    def _get_preserved_qsl(self, request, preserved_filters):
        pass

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage.
        """
        pass

    def response_change(self, request, obj):
        """
        Determine the HttpResponse for the change_view stage.
        """
        pass

    def _response_post_save(self, request, obj):
        pass

    def response_post_save_add(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        pass

    def response_post_save_change(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when editing an existing object.
        """
        pass

    def response_action(self, request, queryset):
        """
        Handle an admin action. This is called if a request is POSTed to the
        changelist; it returns an HttpResponse if the action was handled, and
        None otherwise.
        """
        pass

    def response_delete(self, request, obj_display, obj_id):
        """
        Determine the HttpResponse for the delete_view stage.
        """
        pass

    def render_delete_form(self, request, context):
        pass

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        # Edit permissions on parent model are required for editable inlines.
        pass

    def get_changeform_initial_data(self, request):
        """
        Get the initial form data from the request's GET params.
        """
        pass

    def _get_obj_does_not_exist_redirect(self, request, opts, object_id):
        """
        Create a message informing the user that the object doesn't exist
        and return a redirect to the admin index page.
        """
        pass

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        pass

    def _changeform_view(self, request, object_id, form_url, extra_context):
        pass

    def add_view(self, request, form_url="", extra_context=None):
        pass

    def change_view(self, request, object_id, form_url="", extra_context=None):
        pass

    def _get_edited_object_pks(self, request, prefix):
        """Return POST data values of list_editable primary keys."""
        pass

    def _get_list_editable_queryset(self, request, prefix):
        """
        Based on POST data, return a queryset of the objects that were edited
        via list_editable.
        """
        pass

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        """
        The 'change list' admin view for this model.
        """
        pass

    def get_deleted_objects(self, objs, request):
        """
        Hook for customizing the delete process for the delete view and the
        "delete selected" action.
        """
        pass

    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        pass

    def _delete_view(self, request, object_id, extra_context):
        "The 'delete' admin view for this model."
        pass

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        pass

    def get_formset_kwargs(self, request, obj, inline, prefix):
        pass

    def _create_formsets(self, request, obj, change):
        "Helper function to generate formsets for add/change_view."
        pass


class InlineModelAdmin(BaseModelAdmin):
    """
    Options for inline editing of ``model`` instances.

    Provide ``fk_name`` to specify the attribute name of the ``ForeignKey``
    from ``model`` to its parent. This is required if ``model`` has more than
    one ``ForeignKey`` to its parent.
    """

    model = None
    fk_name = None
    formset = BaseInlineFormSet
    extra = 3
    min_num = None
    max_num = None
    template = None
    verbose_name = None
    verbose_name_plural = None
    can_delete = True
    show_change_link = False
    checks_class = InlineModelAdminChecks
    classes = None

    def __init__(self, parent_model, admin_site):
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)
        super().__init__()
        if self.verbose_name_plural is None:
            if self.verbose_name is None:
                self.verbose_name_plural = self.opts.verbose_name_plural
            else:
                self.verbose_name_plural = format_lazy("{}s", self.verbose_name)
        if self.verbose_name is None:
            self.verbose_name = self.opts.verbose_name

    @property
    def media(self):
        pass

    def get_extra(self, request, obj=None, **kwargs):
        """Hook for customizing the number of extra inline forms."""
        return self.extra

    def get_min_num(self, request, obj=None, **kwargs):
        """Hook for customizing the min number of inline forms."""
        return self.min_num

    def get_max_num(self, request, obj=None, **kwargs):
        """Hook for customizing the max number of extra inline forms."""
        return self.max_num

    def get_formset(self, request, obj=None, **kwargs):
        """Return a BaseInlineFormSet class for use in add/change views."""
        if "fields" in kwargs:
            fields = kwargs.pop("fields")
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        excluded = self.get_exclude(request, obj)
        exclude = [] if excluded is None else list(excluded)
        exclude.extend(self.get_readonly_fields(request, obj))
        if excluded is None and hasattr(self.form, "_meta") and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # InlineModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # If exclude is an empty list we use None, since that's the actual
        # default.
        exclude = exclude or None
        can_delete = self.can_delete and self.has_delete_permission(request, obj)
        defaults = {
            "form": self.form,
            "formset": self.formset,
            "fk_name": self.fk_name,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
            "extra": self.get_extra(request, obj, **kwargs),
            "min_num": self.get_min_num(request, obj, **kwargs),
            "max_num": self.get_max_num(request, obj, **kwargs),
            "can_delete": can_delete,
            **kwargs,
        }

        base_model_form = defaults["form"]
        can_change = self.has_change_permission(request, obj) if request else True
        can_add = self.has_add_permission(request, obj) if request else True

        class DeleteProtectedModelForm(base_model_form):
            def hand_clean_DELETE(self):
                """
                We don't validate the 'DELETE' field itself because on
                templates it's not rendered using the field information, but
                just using a generic "deletion_field" of the InlineModelAdmin.
                """
                if self.cleaned_data.get(DELETION_FIELD_NAME, False):
                    using = router.db_for_write(self._meta.model)
                    collector = NestedObjects(using=using)
                    if self.instance._state.adding:
                        return
                    collector.collect([self.instance])
                    if collector.protected:
                        objs = []
                        for p in collector.protected:
                            objs.append(
                                # Translators: Model verbose name and instance
                                # representation, suitable to be an item in a
                                # list.
                                _("%(class_name)s %(instance)s")
                                % {"class_name": p._meta.verbose_name, "instance": p}
                            )
                        params = {
                            "class_name": self._meta.model._meta.verbose_name,
                            "instance": self.instance,
                            "related_objects": get_text_list(objs, _("and")),
                        }
                        msg = _(
                            "Deleting %(class_name)s %(instance)s would require "
                            "deleting the following protected related objects: "
                            "%(related_objects)s"
                        )
                        raise ValidationError(
                            msg, code="deleting_protected", params=params
                        )

            def is_valid(self):
                result = super().is_valid()
                self.hand_clean_DELETE()
                return result

            def has_changed(self):
                # Protect against unauthorized edits.
                if not can_change and not self.instance._state.adding:
                    return False
                if not can_add and self.instance._state.adding:
                    return False
                return super().has_changed()

        defaults["form"] = DeleteProtectedModelForm

        if defaults["fields"] is None and not modelform_defines_fields(
            defaults["form"]
        ):
            defaults["fields"] = forms.ALL_FIELDS

        return inlineformset_factory(self.parent_model, self.model, **defaults)

    def _get_form_for_get_fields(self, request, obj=None):
        return self.get_formset(request, obj, fields=None).form

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not self.has_view_or_change_permission(request):
            queryset = queryset.none()
        return queryset

    def _has_any_perms_for_target_model(self, request, perms):
        """
        This method is called only when the ModelAdmin's model is for an
        ManyToManyField's implicit through model (if self.opts.auto_created).
        Return True if the user has any of the given permissions ('add',
        'change', etc.) for the model that points to the through model.
        """
        opts = self.opts
        # Find the target model of an auto-created many-to-many relationship.
        for field in opts.fields:
            if field.remote_field and field.remote_field.model != self.parent_model:
                opts = field.remote_field.model._meta
                break
        return any(
            request.user.has_perm(
                "%s.%s" % (opts.app_label, get_permission_codename(perm, opts))
            )
            for perm in perms
        )

    def has_add_permission(self, request, obj):
        if self.opts.auto_created:
            # Auto-created intermediate models don't have their own
            # permissions. The user needs to have the change permission for the
            # related model in order to be able to do anything with the
            # intermediate model.
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission().
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission().
            return self._has_any_perms_for_target_model(request, ["change"])
        return super().has_delete_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if self.opts.auto_created:
            # Same comment as has_add_permission(). The 'change' permission
            # also implies the 'view' permission.
            return self._has_any_perms_for_target_model(request, ["view", "change"])
        return super().has_view_permission(request)


class StackedInline(InlineModelAdmin):
    template = "admin/edit_inline/stacked.html"


class TabularInline(InlineModelAdmin):
    template = "admin/edit_inline/tabular.html"
