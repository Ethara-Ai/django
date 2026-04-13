"""
This module houses the ctypes initialization procedures, as well
as the notice and error handler function callbacks (get called
when an error occurs in GEOS).

This module also houses GEOS Pointer utilities, including
get_pointer_arr(), and GEOM_PTR.
"""

import logging
import os
from ctypes import CDLL, CFUNCTYPE, POINTER, Structure, c_char_p
from ctypes.util import find_library

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.version import get_version_tuple

logger = logging.getLogger("django.contrib.gis")


def load_geos():
    # Custom library path set?
    pass


# The notice and error handler C function callback definitions.
# Supposed to mimic the GEOS message handler (C below):
#  typedef void (*GEOSMessageHandler)(const char *fmt, ...);
NOTICEFUNC = CFUNCTYPE(None, c_char_p, c_char_p)


def notice_h(fmt, lst):
    pass


notice_h = NOTICEFUNC(notice_h)

ERRORFUNC = CFUNCTYPE(None, c_char_p, c_char_p)


def error_h(fmt, lst):
    pass


error_h = ERRORFUNC(error_h)

# #### GEOS Geometry C data structures, and utility functions. ####


# Opaque GEOS geometry structures, used for GEOM_PTR and CS_PTR
class GEOSGeom_t(Structure):
    pass


class GEOSPrepGeom_t(Structure):
    pass


class GEOSCoordSeq_t(Structure):
    pass


class GEOSContextHandle_t(Structure):
    pass


# Pointers to opaque GEOS geometry structures.
GEOM_PTR = POINTER(GEOSGeom_t)
PREPGEOM_PTR = POINTER(GEOSPrepGeom_t)
CS_PTR = POINTER(GEOSCoordSeq_t)
CONTEXT_PTR = POINTER(GEOSContextHandle_t)


lgeos = SimpleLazyObject(load_geos)


class GEOSFuncFactory:
    """
    Lazy loading of GEOS functions.
    """

    argtypes = None
    restype = None
    errcheck = None

    def __init__(self, func_name, *, restype=None, errcheck=None, argtypes=None):
        self.func_name = func_name
        if restype is not None:
            self.restype = restype
        if errcheck is not None:
            self.errcheck = errcheck
        if argtypes is not None:
            self.argtypes = argtypes

    def __call__(self, *args):
        return self.func(*args)

    @cached_property
    def func(self):
        from django.contrib.gis.geos.prototypes.threadsafe import GEOSFunc

        func = GEOSFunc(self.func_name)
        func.argtypes = self.argtypes or []
        func.restype = self.restype
        if self.errcheck:
            func.errcheck = self.errcheck
        return func


def geos_version():
    """Return the string version of the GEOS library."""
    return lgeos.GEOSversion()


def geos_version_tuple():
    """Return the GEOS version as a tuple (major, minor, subminor)."""
    return get_version_tuple(geos_version().decode())
