"""HTML utilities suitable for global use."""

import html
import json
import re
import warnings
from collections import deque
from collections.abc import Mapping
from html.parser import HTMLParser
from itertools import chain
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.core.validators import DomainNameValidator, EmailValidator
from django.utils.deprecation import RemovedInDjango70Warning
from django.utils.functional import Promise, cached_property, keep_lazy, keep_lazy_text
from django.utils.http import MAX_URL_LENGTH, RFC3986_GENDELIMS, RFC3986_SUBDELIMS
from django.utils.regex_helper import _lazy_re_compile
from django.utils.safestring import SafeData, SafeString, mark_safe
from django.utils.text import normalize_newlines

# https://html.spec.whatwg.org/#void-elements
VOID_ELEMENTS = frozenset(
    (
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
        # Deprecated tags.
        "frame",
        "spacer",
    )
)

MAX_STRIP_TAGS_DEPTH = 50

# HTML tag that opens but has no closing ">" after 1k+ chars.
long_open_tag_without_closing_re = _lazy_re_compile(r"<[a-zA-Z][^>]{1000,}")


@keep_lazy(SafeString)
def escape(text):
    """
    Return the given text with ampersands, quotes and angle brackets encoded
    for use in HTML.

    Always escape input, even if it's already escaped and marked as such.
    This may result in double-escaping. If this is a concern, use
    conditional_escape() instead.
    """
    return SafeString(html.escape(str(text)))


_js_escapes = {
    ord("\\"): "\\u005C",
    ord("'"): "\\u0027",
    ord('"'): "\\u0022",
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
    ord("="): "\\u003D",
    ord("-"): "\\u002D",
    ord(";"): "\\u003B",
    ord("`"): "\\u0060",
    ord("\u2028"): "\\u2028",
    ord("\u2029"): "\\u2029",
}

# Escape every ASCII character with a value less than 32 (C0), 127(C0),
# or 128-159(C1).
_js_escapes.update(
    (ord("%c" % z), "\\u%04X" % z) for z in chain(range(32), range(0x7F, 0xA0))
)


@keep_lazy(SafeString)
def escapejs(value):
    """Hex encode characters for use in JavaScript strings."""
    pass


_json_script_escapes = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


def json_script(value, element_id=None, encoder=None):
    """
    Escape all the HTML/XML special characters with their unicode escapes, so
    value is safe to be output anywhere except for inside a tag attribute. Wrap
    the escaped JSON in a script tag.
    """
    pass


def conditional_escape(text):
    """
    Similar to escape(), except that it doesn't operate on pre-escaped strings.

    This function relies on the __html__ convention used both by Django's
    SafeData class and by third-party libraries like markupsafe.
    """
    if isinstance(text, Promise):
        text = str(text)
    if hasattr(text, "__html__"):
        return text.__html__()
    else:
        return escape(text)


def format_html(format_string, *args, **kwargs):
    """
    Similar to str.format, but pass all arguments through conditional_escape(),
    and call mark_safe() on the result. This function should be used instead
    of str.format or % interpolation to build up small HTML fragments.
    """
    if not (args or kwargs):
        raise TypeError("args or kwargs must be provided.")
    args_safe = map(conditional_escape, args)
    kwargs_safe = {k: conditional_escape(v) for (k, v) in kwargs.items()}
    return mark_safe(format_string.format(*args_safe, **kwargs_safe))


def format_html_join(sep, format_string, args_generator):
    """
    A wrapper of format_html, for the common case of a group of arguments that
    need to be formatted using the same format string, and then joined using
    'sep'. 'sep' is also passed through conditional_escape.

    'args_generator' should be an iterator that returns the sequence of 'args'
    that will be passed to format_html.

    Example:

      format_html_join('\n', "<li>{} {}</li>", ((u.first_name, u.last_name)
                                                  for u in users))
    """
    pass


@keep_lazy_text
def linebreaks(value, autoescape=False):
    """Convert newlines into <p> and <br>s."""
    pass


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        pass

    def handle_entityref(self, name):
        pass

    def handle_charref(self, name):
        pass

    def get_data(self):
        pass


def _strip_once(value):
    """
    Internal tag stripping utility used by strip_tags.
    """
    pass


@keep_lazy_text
def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    pass


@keep_lazy_text
def strip_spaces_between_tags(value):
    """Return the given HTML with spaces between tags removed."""
    return re.sub(r">\s+<", "><", str(value))


def smart_urlquote(url):
    """Quote a URL if it isn't already quoted."""

    def unquote_quote(segment):
        segment = unquote(segment)
        # Tilde is part of RFC 3986 Section 2.3 Unreserved Characters,
        # see also https://bugs.python.org/issue16285
        return quote(segment, safe=RFC3986_SUBDELIMS + RFC3986_GENDELIMS + "~")

    try:
        scheme, netloc, path, query, fragment = urlsplit(url)
    except ValueError:
        # invalid IPv6 URL (normally square brackets in hostname part).
        return unquote_quote(url)

    # Handle IDN as percent-encoded UTF-8 octets, per WHATWG URL Specification
    # section 3.5 and RFC 3986 section 3.2.2. Defer any IDNA to the user agent.
    # See #36013.
    netloc = unquote_quote(netloc)

    if query:
        # Separately unquoting key/value, so as to not mix querystring
        # separators included in query values. See #22267.
        query_parts = [
            (unquote(q[0]), unquote(q[1]))
            for q in parse_qsl(query, keep_blank_values=True)
        ]
        # urlencode will take care of quoting
        query = urlencode(query_parts)

    path = unquote_quote(path)
    fragment = unquote_quote(fragment)

    return urlunsplit((scheme, netloc, path, query, fragment))


class CountsDict(dict):
    def __init__(self, *args, word, **kwargs):
        super().__init__(*args, *kwargs)
        self.word = word

    def __missing__(self, key):
        self[key] = self.word.count(key)
        return self[key]


class Urlizer:
    """
    Convert any URLs in text into clickable links.

    Work on http://, https://, www. links, and also on links ending in one of
    the original seven gTLDs (.com, .edu, .gov, .int, .mil, .net, and .org).
    Links can have trailing punctuation (periods, commas, close-parens) and
    leading punctuation (opening parens) and it'll still do the right thing.
    """

    trailing_punctuation_chars = ".,:;!"
    wrapping_punctuation = [("(", ")"), ("[", "]")]

    simple_url_re = _lazy_re_compile(r"^https?://\[?\w", re.IGNORECASE)
    simple_url_2_re = _lazy_re_compile(
        rf"^www\.|^(?!http)(?:{DomainNameValidator.hostname_re})"
        rf"(?:{DomainNameValidator.domain_re})"
        r"\.(com|edu|gov|int|mil|net|org)($|/.*)$",
        re.IGNORECASE,
    )
    word_split_re = _lazy_re_compile(r"""([\s<>"']+)""")

    mailto_template = "mailto:{local}@{domain}"
    url_template = '<a href="{href}"{attrs}>{url}</a>'

    def __call__(self, text, trim_url_limit=None, nofollow=False, autoescape=False):
        """
        If trim_url_limit is not None, truncate the URLs in the link text
        longer than this limit to trim_url_limit - 1 characters and append an
        ellipsis.

        If nofollow is True, give the links a rel="nofollow" attribute.

        If autoescape is True, autoescape the link text and URLs.
        """
        safe_input = isinstance(text, SafeData)

        words = self.word_split_re.split(str(text))
        local_cache = {}
        urlized_words = []
        for word in words:
            if (urlized_word := local_cache.get(word)) is None:
                urlized_word = self.handle_word(
                    word,
                    safe_input=safe_input,
                    trim_url_limit=trim_url_limit,
                    nofollow=nofollow,
                    autoescape=autoescape,
                )
                local_cache[word] = urlized_word
            urlized_words.append(urlized_word)
        return "".join(urlized_words)

    def handle_word(
        self,
        word,
        *,
        safe_input,
        trim_url_limit=None,
        nofollow=False,
        autoescape=False,
    ):
        if "." in word or "@" in word or ":" in word:
            # lead: Punctuation trimmed from the beginning of the word.
            # middle: State of the word.
            # trail: Punctuation trimmed from the end of the word.
            lead, middle, trail = self.trim_punctuation(word)
            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ""
            if len(middle) <= MAX_URL_LENGTH and self.simple_url_re.match(middle):
                url = smart_urlquote(html.unescape(middle))
            elif len(middle) <= MAX_URL_LENGTH and self.simple_url_2_re.match(middle):
                unescaped_middle = html.unescape(middle)
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # url = smart_urlquote(f"https://{unescaped_middle}")
                protocol = (
                    "https"
                    if getattr(settings, "URLIZE_ASSUME_HTTPS", False)
                    else "http"
                )
                if not settings.URLIZE_ASSUME_HTTPS:
                    warnings.warn(
                        "The default protocol will be changed from HTTP to "
                        "HTTPS in Django 7.0. Set the URLIZE_ASSUME_HTTPS "
                        "transitional setting to True to opt into using HTTPS as the "
                        "new default protocol.",
                        RemovedInDjango70Warning,
                        stacklevel=2,
                    )
                url = smart_urlquote(f"{protocol}://{unescaped_middle}")
            elif ":" not in middle and self.is_email_simple(middle):
                local, domain = middle.rsplit("@", 1)
                # Encode per RFC 6068 Section 2 (items 1, 4, 5). Defer any IDNA
                # to the user agent. See #36013.
                local = quote(local, safe="")
                domain = quote(domain, safe="")
                url = self.mailto_template.format(local=local, domain=domain)
                nofollow_attr = ""
            # Make link.
            if url:
                trimmed = self.trim_url(middle, limit=trim_url_limit)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    trimmed = escape(trimmed)
                middle = self.url_template.format(
                    href=escape(url),
                    attrs=nofollow_attr,
                    url=trimmed,
                )
                return SafeString(f"{lead}{middle}{trail}")
            else:
                if safe_input:
                    return mark_safe(word)
                elif autoescape:
                    return escape(word)
        elif safe_input:
            return mark_safe(word)
        elif autoescape:
            return escape(word)
        return word

    def trim_url(self, x, *, limit):
        if limit is None or len(x) <= limit:
            return x
        return "%s…" % x[: max(0, limit - 1)]

    @cached_property
    def wrapping_punctuation_openings(self):
        pass

    @cached_property
    def trailing_punctuation_chars_no_semicolon(self):
        pass

    @cached_property
    def trailing_punctuation_chars_has_semicolon(self):
        pass

    def trim_punctuation(self, word):
        """
        Trim trailing and wrapping punctuation from `word`. Return the items of
        the new state.
        """
        # Strip all opening wrapping punctuation.
        middle = word.lstrip(self.wrapping_punctuation_openings)
        lead = word[: len(word) - len(middle)]
        trail = deque()

        # Continue trimming until middle remains unchanged.
        trimmed_something = True
        counts = CountsDict(word=middle)
        while trimmed_something and middle:
            trimmed_something = False
            # Trim wrapping punctuation.
            for opening, closing in self.wrapping_punctuation:
                if counts[opening] < counts[closing]:
                    rstripped = middle.rstrip(closing)
                    if rstripped != middle:
                        strip = counts[closing] - counts[opening]
                        trail.appendleft(middle[-strip:])
                        middle = middle[:-strip]
                        trimmed_something = True
                        counts[closing] -= strip

            amp = middle.rfind("&")
            if amp == -1:
                rstripped = middle.rstrip(self.trailing_punctuation_chars)
            else:
                rstripped = middle.rstrip(self.trailing_punctuation_chars_no_semicolon)
            if rstripped != middle:
                trail.appendleft(middle[len(rstripped) :])
                middle = rstripped
                trimmed_something = True

            if self.trailing_punctuation_chars_has_semicolon and middle.endswith(";"):
                # Only strip if not part of an HTML entity.
                potential_entity = middle[amp:]
                escaped = html.unescape(potential_entity)
                if escaped == potential_entity or escaped.endswith(";"):
                    rstripped = middle.rstrip(self.trailing_punctuation_chars)
                    trail_start = len(rstripped)
                    amount_trailing_semicolons = len(middle) - len(middle.rstrip(";"))
                    if amp > -1 and amount_trailing_semicolons > 1:
                        # Leave up to most recent semicolon as might be an
                        # entity.
                        recent_semicolon = middle[trail_start:].index(";")
                        middle_semicolon_index = recent_semicolon + trail_start + 1
                        trail.appendleft(middle[middle_semicolon_index:])
                        middle = rstripped + middle[trail_start:middle_semicolon_index]
                    else:
                        trail.appendleft(middle[trail_start:])
                        middle = rstripped
                    trimmed_something = True

        trail = "".join(trail)
        return lead, middle, trail

    @staticmethod
    def is_email_simple(value):
        """Return True if value looks like an email address."""
        try:
            EmailValidator(allowlist=[])(value)
        except ValidationError:
            return False
        return True


urlizer = Urlizer()


@keep_lazy_text
def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    pass


def avoid_wrapping(value):
    """
    Avoid text wrapping in the middle of a phrase by adding non-breaking
    spaces where there previously were normal spaces.
    """
    pass


def html_safe(klass):
    """
    A decorator that defines the __html__ method. This helps non-Django
    templates to detect classes whose __str__ methods return SafeString.
    """
    pass
