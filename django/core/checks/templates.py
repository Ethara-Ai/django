from . import Tags, register


@register(Tags.templates)
def check_templates(app_configs, **kwargs):
    """Check all registered template engines."""
    pass
