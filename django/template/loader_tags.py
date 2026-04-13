import posixpath
from collections import defaultdict

from django.utils.safestring import mark_safe

from .base import Node, Template, TemplateSyntaxError, TextNode, Variable, token_kwargs
from .library import Library

register = Library()

BLOCK_CONTEXT_KEY = "block_context"


class BlockContext:
    def __init__(self):
        # Dictionary of FIFO queues.
        self.blocks = defaultdict(list)

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: blocks={self.blocks!r}>"

    def add_blocks(self, blocks):
        for name, block in blocks.items():
            self.blocks[name].insert(0, block)

    def pop(self, name):
        try:
            return self.blocks[name].pop()
        except IndexError:
            return None

    def push(self, name, block):
        self.blocks[name].append(block)

    def get_block(self, name):
        pass


class BlockNode(Node):
    def __init__(self, name, nodelist, parent=None):
        self.name = name
        self.nodelist = nodelist
        self.parent = parent

    def __repr__(self):
        return "<Block Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        block_context = context.render_context.get(BLOCK_CONTEXT_KEY)
        with context.push():
            if block_context is None:
                context["block"] = self
                result = self.nodelist.render(context)
            else:
                push = block = block_context.pop(self.name)
                if block is None:
                    block = self
                # Create new block so we can store context without
                # thread-safety issues.
                block = type(self)(block.name, block.nodelist)
                block.context = context
                context["block"] = block
                result = block.nodelist.render(context)
                if push is not None:
                    block_context.push(self.name, push)
        return result

    def super(self):
        pass


class ExtendsNode(Node):
    must_be_first = True
    context_key = "extends_context"

    def __init__(self, nodelist, parent_name, template_dirs=None):
        self.nodelist = nodelist
        self.parent_name = parent_name
        self.template_dirs = template_dirs
        self.blocks = {n.name: n for n in nodelist.get_nodes_by_type(BlockNode)}

    def __repr__(self):
        return "<%s: extends %s>" % (self.__class__.__name__, self.parent_name.token)

    def find_template(self, template_name, context):
        """
        This is a wrapper around engine.find_template(). A history is kept in
        the render_context attribute between successive extends calls and
        passed as the skip argument. This enables extends to work recursively
        without extending the same template twice.
        """
        history = context.render_context.setdefault(
            self.context_key,
            [self.origin],
        )
        template, origin = context.template.engine.find_template(
            template_name,
            skip=history,
        )
        history.append(origin)
        return template

    def get_parent(self, context):
        parent = self.parent_name.resolve(context)
        if not parent:
            error_msg = "Invalid template name in 'extends' tag: %r." % parent
            if self.parent_name.filters or isinstance(self.parent_name.var, Variable):
                error_msg += (
                    " Got this from the '%s' variable." % self.parent_name.token
                )
            raise TemplateSyntaxError(error_msg)
        if isinstance(parent, Template):
            # parent is a django.template.Template
            return parent
        if isinstance(getattr(parent, "template", None), Template):
            # parent is a django.template.backends.django.Template
            return parent.template
        return self.find_template(parent, context)

    def render(self, context):
        compiled_parent = self.get_parent(context)

        if BLOCK_CONTEXT_KEY not in context.render_context:
            context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
        block_context = context.render_context[BLOCK_CONTEXT_KEY]

        # Add the block nodes from this node to the block context
        block_context.add_blocks(self.blocks)

        # If this block's parent doesn't have an extends node it is the root,
        # and its block nodes also need to be added to the block context.
        for node in compiled_parent.nodelist:
            # The ExtendsNode has to be the first non-text node.
            if not isinstance(node, TextNode):
                if not isinstance(node, ExtendsNode):
                    blocks = {
                        n.name: n
                        for n in compiled_parent.nodelist.get_nodes_by_type(BlockNode)
                    }
                    block_context.add_blocks(blocks)
                break

        # Call Template._render explicitly so the parser context stays
        # the same.
        with context.render_context.push_state(compiled_parent, isolated_context=False):
            return compiled_parent._render(context)


class IncludeNode(Node):
    context_key = "__include_context"

    def __init__(
        self, template, *args, extra_context=None, isolated_context=False, **kwargs
    ):
        self.template = template
        self.extra_context = extra_context or {}
        self.isolated_context = isolated_context
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: template={self.template!r}>"

    def render(self, context):
        """
        Render the specified template and context. Cache the template object
        in render_context to avoid reparsing and loading when used in a for
        loop.
        """
        template = self.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, "render", None)):
            # If not, try the cache and select_template().
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,
                        template_name,
                    ),
                )
            else:
                template_name = tuple(template_name)
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.select_template(template_name)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, "template"):
            template = template.template
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }
        if self.isolated_context:
            return template.render(context.new(values))
        with context.push(**values):
            return template.render(context)


@register.tag("block")
def do_block(parser, token):
    """
    Define a block that can be overridden by child templates.
    """
    pass


def construct_relative_path(
    current_template_name,
    relative_name,
    allow_recursion=False,
):
    """
    Convert a relative path (starting with './' or '../') to the full template
    name based on the current_template_name.
    """
    new_name = relative_name.strip("'\"")
    if not new_name.startswith(("./", "../")):
        # relative_name is a variable or a literal that doesn't contain a
        # relative path.
        return relative_name

    if current_template_name is None:
        # Unknown origin (e.g. Template('...').render(Context({...})).
        raise TemplateSyntaxError(
            f"The relative path {relative_name} cannot be evaluated due to "
            "an unknown template origin."
        )

    new_name = posixpath.normpath(
        posixpath.join(
            posixpath.dirname(current_template_name.lstrip("/")),
            new_name,
        )
    )
    if new_name.startswith("../"):
        raise TemplateSyntaxError(
            "The relative path '%s' points outside the file hierarchy that "
            "template '%s' is in." % (relative_name, current_template_name)
        )
    if not allow_recursion and current_template_name.lstrip("/") == new_name:
        raise TemplateSyntaxError(
            "The relative path '%s' was translated to template name '%s', the "
            "same template in which the tag appears."
            % (relative_name, current_template_name)
        )
    has_quotes = (
        relative_name.startswith(('"', "'")) and relative_name[0] == relative_name[-1]
    )
    return f'"{new_name}"' if has_quotes else new_name


@register.tag("extends")
def do_extends(parser, token):
    """
    Signal that this template extends a parent template.

    This tag may be used in two ways: ``{% extends "base" %}`` (with quotes)
    uses the literal value "base" as the name of the parent template to extend,
    or ``{% extends variable %}`` uses the value of ``variable`` as either the
    name of the parent template to extend (if it evaluates to a string) or as
    the parent template itself (if it evaluates to a Template object).
    """
    pass


@register.tag("include")
def do_include(parser, token):
    """
    Load a template and render it with the current context. You can pass
    additional context using keyword arguments.

    Example::

        {% include "foo/some_include" %}
        {% include "foo/some_include" with bar="BAZZ!" baz="BING!" %}

    Use the ``only`` argument to exclude the current context when rendering
    the included template::

        {% include "foo/some_include" only %}
        {% include "foo/some_include" with bar="1" only %}
    """
    pass
