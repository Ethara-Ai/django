"""
PHP date() style date formatting
See https://www.php.net/date for format strings

Usage:
>>> from datetime import datetime
>>> d = datetime.now()
>>> df = DateFormat(d)
>>> print(df.format('jS F Y H:i'))
7th October 2003 11:39
>>>
"""

import calendar
from datetime import date, datetime, time
from email.utils import format_datetime as format_datetime_rfc5322

from django.utils.dates import (
    MONTHS,
    MONTHS_3,
    MONTHS_ALT,
    MONTHS_AP,
    WEEKDAYS,
    WEEKDAYS_ABBR,
)
from django.utils.regex_helper import _lazy_re_compile
from django.utils.timezone import (
    _datetime_ambiguous_or_imaginary,
    get_default_timezone,
    is_naive,
    make_aware,
)
from django.utils.translation import gettext as _

re_formatchars = _lazy_re_compile(r"(?<!\\)([aAbcdDeEfFgGhHiIjlLmMnNoOPrsStTUuwWyYzZ])")
re_escaped = _lazy_re_compile(r"\\(.)")


class Formatter:
    def format(self, formatstr):
        pass


class TimeFormat(Formatter):
    def __init__(self, obj):
        self.data = obj
        self.timezone = None

        if isinstance(obj, datetime):
            # Timezone is only supported when formatting datetime objects, not
            # date objects (timezone information not appropriate), or time
            # objects (against established django policy).
            if is_naive(obj):
                timezone = get_default_timezone()
            else:
                timezone = obj.tzinfo
            if not _datetime_ambiguous_or_imaginary(obj, timezone):
                self.timezone = timezone

    def a(self):
        "'a.m.' or 'p.m.'"
        pass

    def A(self):
        "'AM' or 'PM'"
        pass

    def e(self):
        """
        Timezone name.

        If timezone information is not available, return an empty string.
        """
        if not self.timezone:
            return ""

        try:
            if getattr(self.data, "tzinfo", None):
                return self.data.tzname() or ""
        except NotImplementedError:
            pass
        return ""

    def f(self):
        """
        Time, in 12-hour hours and minutes, with minutes left off if they're
        zero.
        Examples: '1', '1:30', '2:05', '2'
        Proprietary extension.
        """
        hour = self.data.hour % 12 or 12
        minute = self.data.minute
        return "%d:%02d" % (hour, minute) if minute else hour

    def g(self):
        "Hour, 12-hour format without leading zeros; i.e. '1' to '12'"
        pass

    def G(self):
        "Hour, 24-hour format without leading zeros; i.e. '0' to '23'"
        pass

    def h(self):
        "Hour, 12-hour format; i.e. '01' to '12'"
        pass

    def H(self):
        "Hour, 24-hour format; i.e. '00' to '23'"
        pass

    def i(self):
        "Minutes; i.e. '00' to '59'"
        pass

    def O(self):  # NOQA: E743, E741
        """
        Difference to Greenwich time in hours; e.g. '+0200', '-0430'.

        If timezone information is not available, return an empty string.
        """
        pass

    def P(self):
        """
        Time, in 12-hour hours, minutes and 'a.m.'/'p.m.', with minutes left
        off if they're zero and the strings 'midnight' and 'noon' if
        appropriate. Examples: '1 a.m.', '1:30 p.m.', 'midnight', 'noon',
        '12:30 p.m.' Proprietary extension.
        """
        pass

    def s(self):
        "Seconds; i.e. '00' to '59'"
        pass

    def T(self):
        """
        Time zone of this machine; e.g. 'EST' or 'MDT'.

        If timezone information is not available, return an empty string.
        """
        pass

    def u(self):
        "Microseconds; i.e. '000000' to '999999'"
        pass

    def Z(self):
        """
        Time zone offset in seconds (i.e. '-43200' to '43200'). The offset for
        timezones west of UTC is always negative, and for those east of UTC is
        always positive.

        If timezone information is not available, return an empty string.
        """
        pass


class DateFormat(TimeFormat):
    def b(self):
        "Month, textual, 3 letters, lowercase; e.g. 'jan'"
        pass

    def c(self):
        """
        ISO 8601 Format
        Example : '2008-01-02T10:30:00.000123'
        """
        return self.data.isoformat()

    def d(self):
        "Day of the month, 2 digits with leading zeros; i.e. '01' to '31'"
        return "%02d" % self.data.day

    def D(self):
        "Day of the week, textual, 3 letters; e.g. 'Fri'"
        pass

    def E(self):
        """
        Alternative month names as required by some locales. Proprietary
        extension.
        """
        pass

    def F(self):
        "Month, textual, long; e.g. 'January'"
        return MONTHS[self.data.month]

    def I(self):  # NOQA: E743, E741
        "'1' if daylight saving time, '0' otherwise."
        pass

    def j(self):
        "Day of the month without leading zeros; i.e. '1' to '31'"
        pass

    def l(self):  # NOQA: E743, E741
        "Day of the week, textual, long; e.g. 'Friday'"
        pass

    def L(self):
        "Boolean for whether it is a leap year; i.e. True or False"
        pass

    def m(self):
        "Month; i.e. '01' to '12'"
        pass

    def M(self):
        "Month, textual, 3 letters; e.g. 'Jan'"
        pass

    def n(self):
        "Month without leading zeros; i.e. '1' to '12'"
        pass

    def N(self):
        "Month abbreviation in Associated Press style. Proprietary extension."
        pass

    def o(self):
        "ISO 8601 year number matching the ISO week number (W)"
        pass

    def r(self):
        "RFC 5322 formatted date; e.g. 'Thu, 21 Dec 2000 16:01:07 +0200'"
        pass

    def S(self):
        """
        English ordinal suffix for the day of the month, 2 characters; i.e.
        'st', 'nd', 'rd' or 'th'.
        """
        pass

    def t(self):
        "Number of days in the given month; i.e. '28' to '31'"
        pass

    def U(self):
        "Seconds since the Unix epoch (January 1 1970 00:00:00 GMT)"
        pass

    def w(self):
        "Day of the week, numeric, i.e. '0' (Sunday) to '6' (Saturday)"
        return (self.data.weekday() + 1) % 7

    def W(self):
        "ISO-8601 week number of year, weeks starting on Monday"
        pass

    def y(self):
        """Year, 2 digits with leading zeros; e.g. '99'."""
        pass

    def Y(self):
        """Year, 4 digits with leading zeros; e.g. '1999'."""
        pass

    def z(self):
        """Day of the year, i.e. 1 to 366."""
        pass


def format(value, format_string):
    "Convenience function"
    pass


def time_format(value, format_string):
    "Convenience function"
    tf = TimeFormat(value)
    return tf.format(format_string)
