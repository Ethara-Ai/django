from ctypes import byref, c_double, c_int, c_void_p

from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.prototypes import raster as capi
from django.contrib.gis.gdal.raster.base import GDALRasterBase
from django.contrib.gis.shortcuts import numpy
from django.utils.encoding import force_str

from .const import (
    GDAL_COLOR_TYPES,
    GDAL_INTEGER_TYPES,
    GDAL_PIXEL_TYPES,
    GDAL_TO_CTYPES,
)


class GDALBand(GDALRasterBase):
    """
    Wrap a GDAL raster band, needs to be obtained from a GDALRaster object.
    """

    def __init__(self, source, index):
        self.source = source
        self._ptr = capi.get_ds_raster_band(source._ptr, index)

    def _flush(self):
        """
        Call the flush method on the Band's parent raster and force a refresh
        of the statistics attribute when requested the next time.
        """
        self.source._flush()
        self._stats_refresh = True

    @property
    def description(self):
        """
        Return the description string of the band.
        """
        pass

    @property
    def width(self):
        """
        Width (X axis) in pixels of the band.
        """
        pass

    @property
    def height(self):
        """
        Height (Y axis) in pixels of the band.
        """
        pass

    @property
    def pixel_count(self):
        """
        Return the total number of pixels in this band.
        """
        pass

    _stats_refresh = False

    def statistics(self, refresh=False, approximate=False):
        """
        Compute statistics on the pixel values of this band.

        The return value is a tuple with the following structure:
        (minimum, maximum, mean, standard deviation).

        If approximate=True, the statistics may be computed based on overviews
        or a subset of image tiles.

        If refresh=True, the statistics will be computed from the data
        directly, and the cache will be updated where applicable.

        For empty bands (where all pixel values are nodata), all statistics
        values are returned as None.

        For raster formats using Persistent Auxiliary Metadata (PAM) services,
        the statistics might be cached in an auxiliary file.
        """
        pass

    @property
    def min(self):
        """
        Return the minimum pixel value for this band.
        """
        pass

    @property
    def max(self):
        """
        Return the maximum pixel value for this band.
        """
        pass

    @property
    def mean(self):
        """
        Return the mean of all pixel values of this band.
        """
        pass

    @property
    def std(self):
        """
        Return the standard deviation of all pixel values of this band.
        """
        pass

    @property
    def nodata_value(self):
        """
        Return the nodata value for this band, or None if it isn't set.
        """
        pass

    @nodata_value.setter
    def nodata_value(self, value):
        """
        Set the nodata value for this band.
        """
        pass

    def datatype(self, as_string=False):
        """
        Return the GDAL Pixel Datatype for this band.
        """
        dtype = capi.get_band_datatype(self._ptr)
        if as_string:
            dtype = GDAL_PIXEL_TYPES[dtype]
        return dtype

    def color_interp(self, as_string=False):
        """Return the GDAL color interpretation for this band."""
        pass

    def data(self, data=None, offset=None, size=None, shape=None, as_memoryview=False):
        """
        Read or writes pixel values for this band. Blocks of data can
        be accessed by specifying the width, height and offset of the
        desired block. The same specification can be used to update
        parts of a raster by providing an array of values.

        Allowed input data types are bytes, memoryview, list, tuple, and array.
        """
        offset = offset or (0, 0)
        size = size or (self.width - offset[0], self.height - offset[1])
        shape = shape or size
        if any(x <= 0 for x in size):
            raise ValueError("Offset too big for this raster.")

        if size[0] > self.width or size[1] > self.height:
            raise ValueError("Size is larger than raster.")

        # Create ctypes type array generator
        ctypes_array = GDAL_TO_CTYPES[self.datatype()] * (shape[0] * shape[1])

        if data is None:
            # Set read mode
            access_flag = 0
            # Prepare empty ctypes array
            data_array = ctypes_array()
        else:
            # Set write mode
            access_flag = 1

            # Instantiate ctypes array holding the input data
            if isinstance(data, (bytes, memoryview)) or (
                numpy and isinstance(data, numpy.ndarray)
            ):
                data_array = ctypes_array.from_buffer_copy(data)
            else:
                data_array = ctypes_array(*data)

        # Access band
        capi.band_io(
            self._ptr,
            access_flag,
            offset[0],
            offset[1],
            size[0],
            size[1],
            byref(data_array),
            shape[0],
            shape[1],
            self.datatype(),
            0,
            0,
        )

        # Return data as numpy array if possible, otherwise as list
        if data is None:
            if as_memoryview:
                return memoryview(data_array)
            elif numpy:
                # reshape() needs a reshape parameter with the height first.
                return numpy.frombuffer(
                    data_array, dtype=numpy.dtype(data_array)
                ).reshape(tuple(reversed(size)))
            else:
                return list(data_array)
        else:
            self._flush()


class BandList(list):
    def __init__(self, source):
        self.source = source
        super().__init__()

    def __iter__(self):
        for idx in range(1, len(self) + 1):
            yield GDALBand(self.source, idx)

    def __len__(self):
        return capi.get_ds_raster_count(self.source._ptr)

    def __getitem__(self, index):
        try:
            return GDALBand(self.source, index + 1)
        except GDALException:
            raise GDALException("Unable to get band index %d" % index)
