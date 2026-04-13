from django.core.checks import Error, Tags, register


@register(Tags.commands)
def migrate_and_makemigrations_autodetector(**kwargs):
    pass
