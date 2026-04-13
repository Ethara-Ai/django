from django.db import connections

from . import Tags, register


@register(Tags.database)
def check_database_backends(databases=None, **kwargs):
    pass
