import re

from django.core.exceptions import ValidationError
from django.forms.utils import RenderableFieldMixin, pretty_name
from django.forms.widgets import MultiWidget, Textarea, TextInput
from django.utils.functional import cached_property
from django.utils.html import format_html, html_safe
from django.utils.translation import gettext_lazy as _

__all__ = ("BoundField",)


class BoundField(RenderableFieldMixin):
    "A Field plus data"

    def __init__(self, form, field, name):
        self.form = form
        self.field = field
        self.name = name
        self.html_name = form.add_prefix(name)
        self.html_initial_name = form.add_initial_prefix(name)
        self.html_initial_id = form.add_initial_prefix(self.auto_id)
        if self.field.label is None:
            self.label = pretty_name(name)
        else:
            self.label = self.field.label
        self.help_text = field.help_text or ""
        self.renderer = form.renderer

    @cached_property
    def subwidgets(self):
        """
        Most widgets yield a single subwidget, but others like RadioSelect and
        CheckboxSelectMultiple produce one subwidget for each choice.

        This property is cached so that only one database query occurs when
        rendering ModelChoiceFields.
        """
        pass

    def __bool__(self):
        # BoundField evaluates to True even if it doesn't have subwidgets.
        return True

    def __iter__(self):
        return iter(self.subwidgets)

    def __len__(self):
        return len(self.subwidgets)

    def __getitem__(self, idx):
        # Prevent unnecessary reevaluation when accessing BoundField's attrs
        # from templates.
        if not isinstance(idx, (int, slice)):
            raise TypeError(
                "BoundField indices must be integers or slices, not %s."
                % type(idx).__name__
            )
        return self.subwidgets[idx]

    @property
    def errors(self):
        """
        Return an ErrorList (empty if there are no errors) for this field.
        """
        pass

    @property
    def template_name(self):
        pass

    def get_context(self):
        return {"field": self}

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Render the field by rendering the passed widget, adding any HTML
        attributes passed as attrs. If a widget isn't specified, use the
        field's default widget.
        """
        pass

    def as_text(self, attrs=None, **kwargs):
        """
        Return a string of HTML for representing this as an
        <input type="text">.
        """
        pass

    def as_textarea(self, attrs=None, **kwargs):
        """Return a string of HTML for representing this as a <textarea>."""
        pass

    def as_hidden(self, attrs=None, **kwargs):
        """
        Return a string of HTML for representing this as an
        <input type="hidden">.
        """
        pass

    @property
    def data(self):
        """
        Return the data for this BoundField, or None if it wasn't given.
        """
        return self.form._widget_data_value(self.field.widget, self.html_name)

    def value(self):
        """
        Return the value for this BoundField, using the initial value if
        the form is not bound or the data otherwise.
        """
        data = self.initial
        if self.form.is_bound:
            data = self.field.bound_data(self.data, data)
        return self.field.prepare_value(data)

    def _has_changed(self):
        pass

    def label_tag(self, contents=None, attrs=None, label_suffix=None, tag=None):
        """
        Wrap the given contents in a <label>, if the field has an ID attribute.
        contents should be mark_safe'd to avoid HTML escaping. If contents
        aren't given, use the field's HTML-escaped label.

        If attrs are given, use them as HTML attributes on the <label> tag.

        label_suffix overrides the form's label_suffix.
        """
        pass

    def legend_tag(self, contents=None, attrs=None, label_suffix=None):
        """
        Wrap the given contents in a <legend>, if the field has an ID
        attribute. Contents should be mark_safe'd to avoid HTML escaping. If
        contents aren't given, use the field's HTML-escaped label.

        If attrs are given, use them as HTML attributes on the <legend> tag.

        label_suffix overrides the form's label_suffix.
        """
        pass

    def css_classes(self, extra_classes=None):
        """
        Return a string of space-separated CSS classes for this field.
        """
        pass

    @property
    def is_hidden(self):
        """Return True if this BoundField's widget is hidden."""
        pass

    @property
    def auto_id(self):
        """
        Calculate and return the ID attribute for this BoundField, if the
        associated Form has specified auto_id. Return an empty string
        otherwise.
        """
        pass

    @property
    def id_for_label(self):
        """
        Wrapper around the field widget's `id_for_label` method.
        Useful, for example, for focusing on this field regardless of whether
        it has a single widget or a MultiWidget.
        """
        widget = self.field.widget
        id_ = widget.attrs.get("id") or self.auto_id
        return widget.id_for_label(id_)

    @cached_property
    def initial(self):
        return self.form.get_initial_for_field(self.field, self.name)

    def build_widget_attrs(self, attrs, widget=None):
        pass

    @property
    def aria_describedby(self):
        # Preserve aria-describedby set on the widget.
        pass

    @property
    def widget_type(self):
        pass

    @property
    def use_fieldset(self):
        """
        Return the value of this BoundField widget's use_fieldset attribute.
        """
        pass


@html_safe
class BoundWidget:
    """
    A container class used for iterating over widgets. This is useful for
    widgets that have choices. For example, the following can be used in a
    template:

    {% for radio in myform.beatles %}
      <label for="{{ radio.id_for_label }}">
        {{ radio.choice_label }}
        <span class="radio">{{ radio.tag }}</span>
      </label>
    {% endfor %}
    """

    def __init__(self, parent_widget, data, renderer):
        self.parent_widget = parent_widget
        self.data = data
        self.renderer = renderer

    def __str__(self):
        return self.tag(wrap_label=True)

    def tag(self, wrap_label=False):
        context = {"widget": {**self.data, "wrap_label": wrap_label}}
        return self.parent_widget._render(self.template_name, context, self.renderer)

    @property
    def template_name(self):
        pass

    @property
    def id_for_label(self):
        return self.data["attrs"].get("id")

    @property
    def choice_label(self):
        pass
