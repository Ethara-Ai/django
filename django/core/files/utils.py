import os
import pathlib

from django.core.exceptions import SuspiciousFileOperation


def validate_file_name(name, allow_relative_path=False):
    # Remove potentially dangerous names
    if os.path.basename(name) in {"", ".", ".."}:
        raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)

    if allow_relative_path:
        # Ensure that name can be treated as a pure posix path, i.e. Unix
        # style (with forward slashes).
        path = pathlib.PurePosixPath(str(name).replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise SuspiciousFileOperation(
                "Detected path traversal attempt in '%s'" % name
            )
    elif name != os.path.basename(name):
        raise SuspiciousFileOperation("File name '%s' includes path elements" % name)

    return name


class FileProxyMixin:
    """
    A mixin class used to forward file methods to an underlying file
    object. The internal file object has to be called "file"::

        class FileProxy(FileProxyMixin):
            def __init__(self, file):
                self.file = file
    """

    encoding = property(lambda self: self.file.encoding)
    fileno = property(lambda self: self.file.fileno)
    flush = property(lambda self: self.file.flush)
    isatty = property(lambda self: self.file.isatty)
    newlines = property(lambda self: self.file.newlines)
    read = property(lambda self: self.file.read)
    readinto = property(lambda self: self.file.readinto)
    readline = property(lambda self: self.file.readline)
    readlines = property(lambda self: self.file.readlines)
    seek = property(lambda self: self.file.seek)
    tell = property(lambda self: self.file.tell)
    truncate = property(lambda self: self.file.truncate)
    write = property(lambda self: self.file.write)
    writelines = property(lambda self: self.file.writelines)

    @property
    def closed(self):
        pass

    def readable(self):
        pass

    def writable(self):
        pass

    def seekable(self):
        pass

    def __iter__(self):
        return iter(self.file)
