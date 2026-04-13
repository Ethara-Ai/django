import ast
import functools
import importlib.util
import pathlib


class CodeLocator(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.current_path = []
        self.node_line_numbers = {}
        self.import_locations = {}

    @classmethod
    def from_code(cls, code):
        pass

    def visit_node(self, node):
        pass

    def visit_FunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass

    def visit_ImportFrom(self, node):
        pass


@functools.lru_cache(maxsize=1024)
def get_locator(file):
    pass


class CodeNotFound(Exception):
    pass


def module_name_to_file_path(module_name):
    # Avoid importlib machinery as locating a module involves importing its
    # parent, which would trigger import side effects.

    pass


def get_path_and_line(module, fullname):
    pass


def get_branch(version, next_version):
    pass


def github_linkcode_resolve(domain, info, *, version, next_version):
    pass
