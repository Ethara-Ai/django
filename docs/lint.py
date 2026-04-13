import re
import sys
from collections import Counter
from os.path import abspath, dirname, splitext
from unittest import mock

from sphinxlint.checkers import (
    _ROLE_BODY,
    _is_long_interpreted_text,
    _is_very_long_string_literal,
    _starts_with_anonymous_hyperlink,
    _starts_with_directive_or_hyperlink,
)
from sphinxlint.checkers import checker as sphinxlint_checker
from sphinxlint.rst import SIMPLENAME
from sphinxlint.sphinxlint import check_text
from sphinxlint.utils import PER_FILE_CACHES, hide_non_rst_blocks, paragraphs


def django_check_file(filename, checkers, options=None):
    pass


_TOCTREE_DIRECTIVE_RE = re.compile(r"^ *.. toctree::")
_PARSED_LITERAL_DIRECTIVE_RE = re.compile(r"^ *.. parsed-literal::")
_IS_METHOD_RE = re.compile(r"^ *([\w.]+)\([\w ,*]*\)\s*$")
# https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
# Use two trailing underscores when embedding the URL. Technically, a single
# underscore works as well, but that would create a named reference instead of
# an anonymous one. Named references typically do not have a benefit when the
# URL is embedded. Moreover, they have the disadvantage that you must make sure
# that you do not use the same “Link text” for another link in your document.
_HYPERLINK_DANGLING_RE = re.compile(r"^\s*<https?://[^>]+>`__?[\.,;]?$")


@sphinxlint_checker(".rst", enabled=False, rst_only=True)
def check_line_too_long_django(file, lines, options=None):
    """A modified version of Sphinx-lint's line-too-long check.

    Original:
    https://github.com/sphinx-contrib/sphinx-lint/blob/main/sphinxlint/checkers.py
    """
    pass


_PYTHON_DOMAIN = re.compile(f":py:{SIMPLENAME}:`{_ROLE_BODY}`")


@sphinxlint_checker(".rst", enabled=False, rst_only=True)
def check_python_domain_in_roles(file, lines, options=None):
    """
    :py: indicates the Python language domain. This means code writen in
    Python, not Python built-ins in particular.

    Bad:    :py:class:`email.message.EmailMessage`
    Good:   :class:`email.message.EmailMessage`
    """
    pass


_DOC_CAPTURE_TARGET_RE = re.compile(r":doc:`(?:[^<`]+<)?([^>`]+)>?`")


@sphinxlint_checker(".rst", rst_only=True)
def check_absolute_targets_doc_role(file, lines, options=None):
    pass


import sphinxlint  # noqa: E402

sphinxlint.check_file = django_check_file

from sphinxlint.cli import main  # noqa: E402

if __name__ == "__main__":
    directory = dirname(abspath(__file__))
    params = sys.argv[1:] if len(sys.argv) > 1 else []

    print(f"Running sphinxlint for: {directory} {params=}")

    sys.exit(
        main(
            [
                directory,
                "--jobs",
                "0",
                "--ignore",
                "_build",
                "--ignore",
                "_theme",
                "--ignore",
                "_ext",
                "--enable",
                "all",
                "--disable",
                "line-too-long",  # Disable sphinx-lint version
                "--max-line-length",
                "79",
                *params,
            ]
        )
    )
