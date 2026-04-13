from ctypes import byref, c_double

from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.envelope import Envelope, OGREnvelope
from django.contrib.gis.gdal.error import GDALException, SRSException
from django.contrib.gis.gdal.feature import Feature
from django.contrib.gis.gdal.field import OGRFieldTypes
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.gdal.geomtype import OGRGeomType
from django.contrib.gis.gdal.prototypes import ds as capi
from django.contrib.gis.gdal.prototypes import geom as geom_api
from django.contrib.gis.gdal.prototypes import srs as srs_api
from django.contrib.gis.gdal.srs import SpatialReference
from django.utils.encoding import force_bytes, force_str


# For more information, see the OGR C API source code:
#  https://gdal.org/api/vector_c_api.html
#
# The OGR_L_* routines are relevant here.
class Layer(GDALBase):
    """
    A class that wraps an OGR Layer, needs to be instantiated from a DataSource
    object.
    """

    def __init__(self, layer_ptr, ds):
        """
        Initialize on an OGR C pointer to the Layer and the `DataSource` object
        that owns this layer. The `DataSource` object is required so that a
        reference to it is kept with this Layer. This prevents garbage
        collection of the `DataSource` while this Layer is still active.
        """
        if not layer_ptr:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = layer_ptr
        self._ds = ds
        self._ldefn = capi.get_layer_defn(self._ptr)
        # Does the Layer support random reading?
        self._random_read = self.test_capability(b"RandomRead")

    def __getitem__(self, index):
        "Get the Feature at the specified index."
        if isinstance(index, int):
            # An integer index was given -- we cannot do a check based on the
            # number of features because the beginning and ending feature IDs
            # are not guaranteed to be 0 and len(layer)-1, respectively.
            if index < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self._make_feature(index)
        elif isinstance(index, slice):
            # A slice was given
            start, stop, stride = index.indices(self.num_feat)
            return [self._make_feature(fid) for fid in range(start, stop, stride)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )

    def __iter__(self):
        "Iterate over each Feature in the Layer."
        # ResetReading() must be called before iteration is to begin.
        capi.reset_reading(self._ptr)
        for i in range(self.num_feat):
            yield Feature(capi.get_next_feature(self._ptr), self)

    def __len__(self):
        "The length is the number of features."
        return self.num_feat

    def __str__(self):
        "The string name of the layer."
        return self.name

    def _make_feature(self, feat_id):
        """
        Helper routine for __getitem__ that constructs a Feature from the given
        Feature ID. If the OGR Layer does not support random-access reading,
        then each feature of the layer will be incremented through until the
        a Feature is found matching the given feature ID.
        """
        if self._random_read:
            # If the Layer supports random reading, return.
            try:
                return Feature(capi.get_feature(self.ptr, feat_id), self)
            except GDALException:
                pass
        else:
            # Random access isn't supported, have to increment through
            # each feature until the given feature ID is encountered.
            for feat in self:
                if feat.fid == feat_id:
                    return feat
        # Should have returned a Feature, raise an IndexError.
        raise IndexError("Invalid feature id: %s." % feat_id)

    # #### Layer properties ####
    @property
    def extent(self):
        "Return the extent (an Envelope) of this layer."
        pass

    @property
    def name(self):
        "Return the name of this layer in the Data Source."
        pass

    @property
    def num_feat(self, force=1):
        "Return the number of features in the Layer."
        pass

    @property
    def num_fields(self):
        "Return the number of fields in the Layer."
        pass

    @property
    def geom_type(self):
        "Return the geometry type (OGRGeomType) of the Layer."
        pass

    @property
    def srs(self):
        "Return the Spatial Reference used in this Layer."
        pass

    @property
    def fields(self):
        """
        Return a list of string names corresponding to each of the Fields
        available in this Layer.
        """
        pass

    @property
    def field_types(self):
        """
        Return a list of the types of fields in this Layer. For example,
        return the list [OFTInteger, OFTReal, OFTString] for an OGR layer that
        has an integer, a floating-point, and string fields.
        """
        pass

    @property
    def field_widths(self):
        "Return a list of the maximum field widths for the features."
        pass

    @property
    def field_precisions(self):
        "Return the field precisions for the features."
        pass

    def _get_spatial_filter(self):
        pass

    def _set_spatial_filter(self, filter):
        pass

    spatial_filter = property(_get_spatial_filter, _set_spatial_filter)

    # #### Layer Methods ####
    def get_fields(self, field_name):
        """
        Return a list containing the given field name for every Feature
        in the Layer.
        """
        if field_name not in self.fields:
            raise GDALException("invalid field name: %s" % field_name)
        return [feat.get(field_name) for feat in self]

    def get_geoms(self, geos=False):
        """
        Return a list containing the OGRGeometry for every Feature in
        the Layer.
        """
        pass

    def test_capability(self, capability):
        """
        Return a bool indicating whether the this Layer supports the given
        capability (a string). Valid capability strings include:
          'RandomRead', 'SequentialWrite', 'RandomWrite', 'FastSpatialFilter',
          'FastFeatureCount', 'FastGetExtent', 'CreateField', 'Transactions',
          'DeleteFeature', and 'FastSetNextByIndex'.
        """
        return bool(capi.test_capability(self.ptr, force_bytes(capability)))
