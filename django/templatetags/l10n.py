from django.template import Library, Node, TemplateSyntaxError
from django.utils import formats

register = Library()


@register.filter(is_safe=False)
def localize(value):
    """
    Force a value to be rendered as a localized value.
    """
    return str(formats.localize(value, use_l10n=True))


@register.filter(is_safe=False)
def unlocalize(value):
    """
    Force a value to be rendered as a non-localized value.
    """
    pass


class LocalizeNode(Node):
    def __init__(self, nodelist, use_l10n):
        self.nodelist = nodelist
        self.use_l10n = use_l10n

    def __repr__(self):
        return "<%s>" % self.__class__.__name__

    def render(self, context):
        old_setting = context.use_l10n
        context.use_l10n = self.use_l10n
        output = self.nodelist.render(context)
        context.use_l10n = old_setting
        return output


@register.tag("localize")
def localize_tag(parser, token):
    """
    Force or prevents localization of values.

    Sample usage::

        {% localize off %}
            var pi = {{ 3.1415 }};
        {% endlocalize %}
    """
    pass
