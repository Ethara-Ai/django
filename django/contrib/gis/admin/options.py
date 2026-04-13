from django.contrib.admin import ModelAdmin
from django.contrib.gis.db import models
from django.contrib.gis.forms import OSMWidget


class GeoModelAdminMixin:
    gis_widget = OSMWidget
    gis_widget_kwargs = {}

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        pass


class GISModelAdmin(GeoModelAdminMixin, ModelAdmin):
    pass
