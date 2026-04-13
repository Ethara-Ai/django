import json

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.text import get_text_list
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

ADDITION = 1
CHANGE = 2
DELETION = 3

ACTION_FLAG_CHOICES = [
    (ADDITION, _("Addition")),
    (CHANGE, _("Change")),
    (DELETION, _("Deletion")),
]


class LogEntryManager(models.Manager):
    use_in_migrations = True

    def log_actions(
        self, user_id, queryset, action_flag, change_message="", *, single_object=False
    ):
        if isinstance(change_message, list):
            change_message = json.dumps(change_message)

        log_entry_list = [
            self.model(
                user_id=user_id,
                content_type_id=ContentType.objects.get_for_model(
                    obj, for_concrete_model=False
                ).id,
                object_id=obj.pk,
                object_repr=str(obj)[:200],
                action_flag=action_flag,
                change_message=change_message,
            )
            for obj in queryset
        ]

        if len(log_entry_list) == 1:
            instance = log_entry_list[0]
            instance.save()
            if single_object:
                return instance
            return [instance]

        return self.model.objects.bulk_create(log_entry_list)


class LogEntry(models.Model):
    action_time = models.DateTimeField(
        _("action time"),
        default=timezone.now,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("user"),
    )
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name=_("content type"),
        blank=True,
        null=True,
    )
    object_id = models.TextField(_("object id"), blank=True, null=True)
    # Translators: 'repr' means representation
    # (https://docs.python.org/library/functions.html#repr)
    object_repr = models.CharField(_("object repr"), max_length=200)
    action_flag = models.PositiveSmallIntegerField(
        _("action flag"), choices=ACTION_FLAG_CHOICES
    )
    # change_message is either a string or a JSON structure
    change_message = models.TextField(_("change message"), blank=True)

    objects = LogEntryManager()

    class Meta:
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")
        db_table = "django_admin_log"
        ordering = ["-action_time"]

    def __repr__(self):
        return str(self.action_time)

    def __str__(self):
        if self.is_addition():
            return gettext("Added “%(object)s”.") % {"object": self.object_repr}
        elif self.is_change():
            return gettext("Changed “%(object)s” — %(changes)s") % {
                "object": self.object_repr,
                "changes": self.get_change_message(),
            }
        elif self.is_deletion():
            return gettext("Deleted “%(object)s.”") % {"object": self.object_repr}

        return gettext("LogEntry Object")

    def is_addition(self):
        pass

    def is_change(self):
        pass

    def is_deletion(self):
        pass

    def get_change_message(self):
        """
        If self.change_message is a JSON structure, interpret it as a change
        string, properly translated.
        """
        pass

    def get_edited_object(self):
        """Return the edited object represented by this log entry."""
        pass

    def get_admin_url(self):
        """
        Return the admin URL to edit the object represented by this log entry.
        """
        pass
