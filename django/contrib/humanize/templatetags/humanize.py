import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from django import template
from django.template import defaultfilters
from django.utils.formats import number_format
from django.utils.safestring import mark_safe
from django.utils.timezone import is_aware
from django.utils.translation import gettext as _
from django.utils.translation import (
    gettext_lazy,
    ngettext,
    ngettext_lazy,
    npgettext_lazy,
    pgettext,
    round_away_from_one,
)

register = template.Library()


@register.filter(is_safe=True)
def ordinal(value):
    """
    Convert an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any non-negative integer.
    """
    pass


@register.filter(is_safe=True)
def intcomma(value, use_l10n=True):
    """
    Convert an integer or float (or a string representation of either) to a
    string containing commas every three digits. Format localization is
    respected. For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    pass


# A tuple of standard large number to their converters
intword_converters = (
    (6, lambda number: ngettext("%(value)s million", "%(value)s million", number)),
    (9, lambda number: ngettext("%(value)s billion", "%(value)s billion", number)),
    (12, lambda number: ngettext("%(value)s trillion", "%(value)s trillion", number)),
    (
        15,
        lambda number: ngettext(
            "%(value)s quadrillion", "%(value)s quadrillion", number
        ),
    ),
    (
        18,
        lambda number: ngettext(
            "%(value)s quintillion", "%(value)s quintillion", number
        ),
    ),
    (
        21,
        lambda number: ngettext("%(value)s sextillion", "%(value)s sextillion", number),
    ),
    (
        24,
        lambda number: ngettext("%(value)s septillion", "%(value)s septillion", number),
    ),
    (27, lambda number: ngettext("%(value)s octillion", "%(value)s octillion", number)),
    (30, lambda number: ngettext("%(value)s nonillion", "%(value)s nonillion", number)),
    (33, lambda number: ngettext("%(value)s decillion", "%(value)s decillion", number)),
    (100, lambda number: ngettext("%(value)s googol", "%(value)s googol", number)),
)


@register.filter(is_safe=False)
def intword(value):
    """
    Convert a large integer to a friendly text representation. Works best
    for numbers over 1 million. For example, 1000000 becomes '1.0 million',
    1200000 becomes '1.2 million' and '1200000000' becomes '1.2 billion'.
    """
    pass


@register.filter(is_safe=True)
def apnumber(value):
    """
    For numbers 1-9, return the number spelled out. Otherwise, return the
    number. This follows Associated Press style.
    """
    pass


# Perform the comparison in the default time zone when USE_TZ = True
# (unless a specific time zone has been applied with the |timezone filter).
@register.filter(expects_localtime=True)
def naturalday(value, arg=None):
    """
    For date values that are tomorrow, today or yesterday compared to
    present day return representing string. Otherwise, return a string
    formatted according to settings.DATE_FORMAT.
    """
    pass


# This filter doesn't require expects_localtime=True because it deals properly
# with both naive and aware datetimes. Therefore avoid the cost of conversion.
@register.filter
def naturaltime(value):
    """
    For date and time values show how many seconds, minutes, or hours ago
    compared to current timestamp return representing string.
    """
    pass


class NaturalTimeFormatter:
    time_strings = {
        # Translators: delta will contain a string like '2 months' or
        # '1 month, 2 weeks'
        "past-day": gettext_lazy("%(delta)s ago"),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        "past-hour": ngettext_lazy("an hour ago", "%(count)s hours ago", "count"),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        "past-minute": ngettext_lazy("a minute ago", "%(count)s minutes ago", "count"),
        # Translators: please keep a non-breaking space (U+00A0) between count
        # and time unit.
        "past-second": ngettext_lazy("a second ago", "%(count)s seconds ago", "count"),
        "now": gettext_lazy("now"),
        # fmt: off
        # fmt turned off to avoid black splitting the ngettext_lazy calls to
        # multiple lines, as this results in gettext missing the 'Translators:'
        # comments.
        "future-second": ngettext_lazy(
            # Translators: please keep a non-breaking space (U+00A0) between
            # count and time unit.
            "a second from now", "%(count)s seconds from now", "count"
        ),
        "future-minute": ngettext_lazy(
            # Translators: please keep a non-breaking space (U+00A0) between
            # count and time unit.
            "a minute from now", "%(count)s minutes from now", "count",
        ),
        "future-hour": ngettext_lazy(
            # Translators: please keep a non-breaking space (U+00A0) between
            # count and time unit.
            "an hour from now", "%(count)s hours from now", "count",
        ),
        # fmt: on
        # Translators: delta will contain a string like '2 months' or
        # '1 month, 2 weeks'
        "future-day": gettext_lazy("%(delta)s from now"),
    }
    past_substrings = {
        # fmt: off
        "year": npgettext_lazy(
            # Translators: 'naturaltime-past' strings will be included in
            # '%(delta)s ago'
            "naturaltime-past", "%(num)d year", "%(num)d years", "num",
        ),
        # fmt:on
        "month": npgettext_lazy(
            "naturaltime-past", "%(num)d month", "%(num)d months", "num"
        ),
        "week": npgettext_lazy(
            "naturaltime-past", "%(num)d week", "%(num)d weeks", "num"
        ),
        "day": npgettext_lazy("naturaltime-past", "%(num)d day", "%(num)d days", "num"),
        "hour": npgettext_lazy(
            "naturaltime-past", "%(num)d hour", "%(num)d hours", "num"
        ),
        "minute": npgettext_lazy(
            "naturaltime-past", "%(num)d minute", "%(num)d minutes", "num"
        ),
    }
    future_substrings = {
        # fmt: off
        "year": npgettext_lazy(
            # Translators: 'naturaltime-future' strings will be included in
            # '%(delta)s from now'.
            "naturaltime-future", "%(num)d year", "%(num)d years", "num",
        ),
        # fmt: on
        "month": npgettext_lazy(
            "naturaltime-future", "%(num)d month", "%(num)d months", "num"
        ),
        "week": npgettext_lazy(
            "naturaltime-future", "%(num)d week", "%(num)d weeks", "num"
        ),
        "day": npgettext_lazy(
            "naturaltime-future", "%(num)d day", "%(num)d days", "num"
        ),
        "hour": npgettext_lazy(
            "naturaltime-future", "%(num)d hour", "%(num)d hours", "num"
        ),
        "minute": npgettext_lazy(
            "naturaltime-future", "%(num)d minute", "%(num)d minutes", "num"
        ),
    }

    @classmethod
    def string_for(cls, value):
        pass
