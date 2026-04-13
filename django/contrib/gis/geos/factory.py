from django.contrib.gis.geos.geometry import GEOSGeometry, hex_regex, wkt_regex


def fromfile(file_h):
    """
    Given a string file name, returns a GEOSGeometry. The file may contain WKB,
    WKT, or HEX.
    """
    pass


def fromstr(string, **kwargs):
    "Given a string value, return a GEOSGeometry object."
    pass
