from django import template

register = template.Library()


class AdminLogNode(template.Node):
    def __init__(self, limit, varname, user):
        self.limit = limit
        self.varname = varname
        self.user = user

    def __repr__(self):
        return "<GetAdminLog Node>"

    def render(self, context):
        entries = context["log_entries"]
        if self.user is not None:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].pk
            entries = entries.filter(user__pk=user_id)
        context[self.varname] = entries[: int(self.limit)]
        return ""


@register.tag
def get_admin_log(parser, token):
    """
    Populate a template variable with the admin log for the given criteria.

    Usage::

        {% get_admin_log [limit] as [varname] for_user [user_id_or_varname] %}

    Examples::

        {% get_admin_log 10 as admin_log for_user 23 %}
        {% get_admin_log 10 as admin_log for_user user %}
        {% get_admin_log 10 as admin_log %}

    Note that ``user_id_or_varname`` can be a hard-coded integer (user ID)
    or the name of a template context variable containing the user object
    whose ID you want.
    """
    pass
