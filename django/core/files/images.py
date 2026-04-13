"""
Utility functions for handling images.

Requires Pillow as you might imagine.
"""

import struct
import zlib

from django.core.files import File


class ImageFile(File):
    """
    A mixin for use alongside django.core.files.base.File, which provides
    additional features for dealing with images.
    """

    @property
    def width(self):
        pass

    @property
    def height(self):
        pass

    def _get_image_dimensions(self):
        pass


def get_image_dimensions(file_or_path, close=False):
    """
    Return the (width, height) of an image, given an open file or a path. Set
    'close' to True to close the file at the end if it is initially in an open
    state.
    """
    pass
