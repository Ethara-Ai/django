"""
Sphinx plugins for Django documentation.
"""

import json
import os
import re

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx import addnodes
from sphinx import version_info as sphinx_version
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.directives.code import CodeBlock
from sphinx.domains.std import Cmdoption
from sphinx.errors import ExtensionError
from sphinx.util import logging
from sphinx.util.console import bold
from sphinx.writers.html import HTMLTranslator

logger = logging.getLogger(__name__)
# RE for option descriptions without a '--' prefix
simple_option_desc_re = re.compile(r"([-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)")


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="templatetag",
        rolename="ttag",
        indextemplate="pair: %s; template tag",
    )
    app.add_crossref_type(
        directivename="templatefilter",
        rolename="tfilter",
        indextemplate="pair: %s; template filter",
    )
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )
    app.add_object_type(
        directivename="django-admin",
        rolename="djadmin",
        indextemplate="pair: %s; django-admin command",
        parse_node=parse_django_admin_node,
    )
    app.add_directive("django-admin-option", Cmdoption)
    app.add_config_value("django_next_version", "0.0", True)
    app.add_directive("versionadded", VersionDirective)
    app.add_directive("versionchanged", VersionDirective)
    app.add_builder(DjangoStandaloneHTMLBuilder)
    app.set_translator("djangohtml", DjangoHTMLTranslator)
    app.set_translator("json", DjangoHTMLTranslator)
    app.add_node(
        ConsoleNode,
        html=(visit_console_html, None),
        latex=(visit_console_dummy, depart_console_dummy),
        man=(visit_console_dummy, depart_console_dummy),
        text=(visit_console_dummy, depart_console_dummy),
        texinfo=(visit_console_dummy, depart_console_dummy),
    )
    app.add_directive("console", ConsoleDirective)
    app.connect("html-page-context", html_page_context_hook)
    app.add_role("default-role-error", default_role_error)
    return {"parallel_read_safe": True}


class VersionDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        if len(self.arguments) > 1:
            msg = """Only one argument accepted for directive '{directive_name}::'.
            Comments should be provided as content,
            not as an extra argument.""".format(directive_name=self.name)
            raise self.error(msg)

        env = self.state.document.settings.env
        ret = []
        node = addnodes.versionmodified()
        ret.append(node)

        if self.arguments[0] == env.config.django_next_version:
            node["version"] = "Development version"
        else:
            node["version"] = self.arguments[0]

        node["type"] = self.name
        if self.content:
            self.state.nested_parse(self.content, self.content_offset, node)
        try:
            env.get_domain("changeset").note_changeset(node)
        except ExtensionError:
            # Sphinx < 1.8: Domain 'changeset' is not registered
            env.note_versionchange(node["type"], node["version"], node, self.lineno)
        return ret


class DjangoHTMLTranslator(HTMLTranslator):
    """
    Django-specific reST to HTML tweaks.
    """

    # Don't use border=1, which docutils does by default.
    def visit_table(self, node):
        pass

    def depart_table(self, node):
        pass

    def visit_desc_parameterlist(self, node):
        pass

    def depart_desc_parameterlist(self, node):
        pass

    #
    # Turn the "new in version" stuff (versionadded/versionchanged) into a
    # better callout -- the Sphinx default is just a little span,
    # which is a bit less obvious that I'd like.
    #
    # FIXME: these messages are all hardcoded in English. We need to change
    # that to accommodate other language docs, but I can't work out how to make
    # that work.
    #
    version_text = {
        "versionchanged": "Changed in Django %s",
        "versionadded": "New in Django %s",
    }

    def visit_versionmodified(self, node):
        pass

    def depart_versionmodified(self, node):
        pass

    # Give each section a unique ID -- nice for custom CSS hooks
    def visit_section(self, node):
        pass


def parse_django_admin_node(env, sig, signode):
    pass


class DjangoStandaloneHTMLBuilder(StandaloneHTMLBuilder):
    """
    Subclass to add some extra things we need.
    """

    name = "djangohtml"

    def finish(self):
        pass


class ConsoleNode(nodes.literal_block):
    """
    Custom node to override the visit/depart event handlers at registration
    time. Wrap a literal_block object and defer to it.
    """

    tagname = "ConsoleNode"

    def __init__(self, litblk_obj):
        self.wrapped = litblk_obj

    def __getattr__(self, attr):
        if attr == "wrapped":
            return self.__dict__.wrapped
        return getattr(self.wrapped, attr)


def visit_console_dummy(self, node):
    """Defer to the corresponding parent's handler."""
    pass


def depart_console_dummy(self, node):
    """Defer to the corresponding parent's handler."""
    pass


def visit_console_html(self, node):
    """Generate HTML for the console directive."""
    pass


class ConsoleDirective(CodeBlock):
    """
    A reStructuredText directive which renders a two-tab code block in which
    the second tab shows a Windows command line equivalent of the usual
    Unix-oriented examples.
    """

    required_arguments = 0
    # The 'doscon' Pygments formatter needs a prompt like this. '>' alone
    # won't do it because then it simply paints the whole command line as a
    # gray comment with no highlighting at all.
    WIN_PROMPT = r"...\> "

    def run(self):
        def args_to_win(cmdline):
            changed = False
            out = []
            for token in cmdline.split():
                if token[:2] == "./":
                    token = token[2:]
                    changed = True
                elif token[:2] == "~/":
                    token = "%HOMEPATH%\\" + token[2:]
                    changed = True
                elif token == "make":
                    token = "make.bat"
                    changed = True
                if "://" not in token and "git" not in cmdline:
                    out.append(token.replace("/", "\\"))
                    changed = True
                else:
                    out.append(token)
            if changed:
                return " ".join(out)
            return cmdline

        def cmdline_to_win(line):
            if line.startswith("# "):
                return "REM " + args_to_win(line[2:])
            if line.startswith("$ # "):
                return "REM " + args_to_win(line[4:])
            if line.startswith("$ ./manage.py"):
                return "manage.py " + args_to_win(line[13:])
            if line.startswith("$ manage.py"):
                return "manage.py " + args_to_win(line[11:])
            if line.startswith("$ ./runtests.py"):
                return "runtests.py " + args_to_win(line[15:])
            if line.startswith("$ ./"):
                return args_to_win(line[4:])
            if line.startswith("$ python3"):
                return "py " + args_to_win(line[9:])
            if line.startswith("$ python"):
                return "py " + args_to_win(line[8:])
            if line.startswith("$ "):
                return args_to_win(line[2:])
            return None

        def code_block_to_win(content):
            bchanged = False
            lines = []
            for line in content:
                modline = cmdline_to_win(line)
                if modline is None:
                    lines.append(line)
                else:
                    lines.append(self.WIN_PROMPT + modline)
                    bchanged = True
            if bchanged:
                return ViewList(lines)
            return None

        env = self.state.document.settings.env
        self.arguments = ["console"]
        lit_blk_obj = super().run()[0]

        # Only do work when the djangohtml HTML Sphinx builder is being used,
        # invoke the default behavior for the rest.
        if env.app.builder.name not in ("djangohtml", "json"):
            return [lit_blk_obj]

        lit_blk_obj["uid"] = str(env.new_serialno("console"))
        # Only add the tabbed UI if there is actually a Windows-specific
        # version of the CLI example.
        win_content = code_block_to_win(self.content)
        if win_content is None:
            lit_blk_obj["win_console_text"] = None
        else:
            self.content = win_content
            lit_blk_obj["win_console_text"] = super().run()[0].rawsource

        # Replace the literal_node object returned by Sphinx's CodeBlock with
        # the ConsoleNode wrapper.
        return [ConsoleNode(lit_blk_obj)]


def html_page_context_hook(app, pagename, templatename, context, doctree):
    # Put a bool on the context used to render the template. It's used to
    # control inclusion of console-tabs.css and activation of the JavaScript.
    # This way it's include only from HTML files rendered from reST files where
    # the ConsoleDirective is used.
    pass


def default_role_error(
    name, rawtext, text, lineno, inliner, options=None, content=None
):
    pass
