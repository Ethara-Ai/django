from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.prototypes import raster as capi


class GDALRasterBase(GDALBase):
    """
    Attributes that exist on both GDALRaster and GDALBand.
    """

    @property
    def metadata(self):
        """
        Return the metadata for this raster or band. The return value is a
        nested dictionary, where the first-level key is the metadata domain and
        the second-level is the metadata item names and values for that domain.
        """
        pass

    @metadata.setter
    def metadata(self, value):
        """
        Set the metadata. Update only the domains that are contained in the
        value dictionary.
        """
        pass
