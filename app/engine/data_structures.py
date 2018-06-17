from django.db.models.query import QuerySet
from django.db.models.base import ModelBase
from django.db.models import Model
import numpy as np
from django.db import transaction
from collections import namedtuple


Axes = namedtuple('Axes', ['row', 'col'])


class Axis(object):
    """
    Represents a row or col "axis" of a matrix or vector
    Contains info about the related model and instances (often a subset of all instances) for the particular matrix
    TODO consider changing qset attribute name... can be either queryset or model instance
    TODO maybe constructor could take (field) instead of (name, model)
    """
    def __init__(self, name, model, qset=None):
        """
        :param name: str, field name of the model foreignkey field
        :param model:
        :param qset: either a queryset, or a object instance (for Vector slice_index)
        """
        self.name = name
        self.model = model
        self.qset = qset

    @property
    def index(self):
        if self.qset is not None:
            return self.qset
        else:
            return self.model.objects.all().order_by('pk')


class Vector(object):
    """
    Vector data structure that wraps a django model
    """
    def __init__(self, model, axis, slice_axis, value_field='value'):
        """
        :param model: model instance
        :param axis: Axis object instance
        :param slice_index: index within secondary collapsed axis (e.g. learner instance for a learner mastery vector)
        :param value_field: (str) name of model field to expect value
        """
        self.model = model
        self.value_field = value_field
        self.axis = axis
        self.slice_axis = slice_axis
        self.qset = self._filtered_qset()

    def _filtered_qset(self):
        """
        Get filtered queryset to set as qset attribute, default to all object instances,
        or if there are index filters specified, apply index filters
        """
        qset = self.model.objects.all()
        if self.axis.qset:
            filters = {
                self.axis.name + "__in": self.axis.qset,
                self.slice_axis.name: self.slice_axis.qset
            }
            qset = qset.filter(**filters)
        return qset

    def values(self):
        """
        Return 1-d numpy array of raw values, using 'value' field 
        (or custom field specified by vector.value_field)
        """
        # mapping from pk to corresponding 0-index in axis
        axis_map = pk_index_map(self.axis.index)

        # placeholder matrix to populate values in
        output_array = np.full((self.length(),), np.nan)

        for pk, value in self.qset.values_list(self.axis.name, self.value_field):
            # convert pk's to index along axes (0-indexed)
            idx = axis_map[pk]
            # set the value in the output matrix
            output_array[idx] = value

        return output_array

    def update(self, new_values):
        """
        Runs multiple update to replace values with elements of given list
        """
        # get or create, some objects may not exist yet
        for i, idx in enumerate(self.axis.index):
            filters = {
                self.axis.name: idx,
                self.slice_axis.name: self.slice_axis.index
            }
            self.model.objects.update_or_create(
                **filters,
                defaults={self.value_field: new_values[i]}
            )

    def length(self):
        return self.axis.index.count()


class Matrix(object):
    """
    Matrix data structure that wraps a django model
    """

    def __init__(self, model, indices=None, value_field='value'):
        """
        :param model: model class
        :param indices: tuple/list of queryset or object instances
        :param value_field: str, the model field corresponding to the value (default is 'value')
        """
        # arg validation
        self._validate_args(model, indices)

        self.model = model

        # construct axes attribute
        axes = []
        for i in range(2):
            # assumption:
            # first field defined in model definition is row field, col field is defined second
            # model._meta.get_fields()[1] is row field, [2] is col index
            field = self.model._meta.get_fields()[i+1]
            model = field.remote_field.model
            qset = indices[i] if indices is not None else None
            axes.append(Axis(name=field.name, model=model, qset=qset))
        self.axes = Axes._make(axes)

        # filter qset by any provided indices
        self.qset = self._filtered_qset()

        self.value_field = value_field
        # TODO some validation to see if expected number of elements are present

    def _validate_args(self, model, indices):
        """
        Validate constructor args
        :param model:
        :return:
        """
        # validate model arg
        if not isinstance(model, ModelBase):
            raise ValueError
        # validate indices arg
        if indices:
            # expect list/tuple
            if not isinstance(indices, (list, tuple)):
                raise ValueError
            # expect size 2
            if len(indices) != 2:
                raise ValueError
            # both indices should be QuerySets or None
            if not all([isinstance(idx, QuerySet) for idx in indices if idx]):
                raise ValueError

    def shape(self):
        """
        Returns the "shape" of the matrix. Shape of an axis is the length of the axis queryset if it
        exists, otherwise it is the number of all objects that exist for that axis model type
        :return: 2-tuple of dimensions
        """
        return tuple([a.index.count() for a in self.axes])

    def values(self):
        """
        Get matrix values as an np.array
        :return: 2d np.array
        """
        row_axis_map = pk_index_map(self.axes.row.index)
        col_axis_map = pk_index_map(self.axes.col.index)

        # placeholder matrix to populate values in
        output_matrix = np.full(self.shape(), np.nan)

        for row_pk, col_pk, value in self.qset.values_list(self.axes.row.name, self.axes.col.name, self.value_field):
            # convert pk's to index along axes (0-indexed)
            row_idx = row_axis_map[row_pk]
            col_idx = col_axis_map[col_pk]
            # set the value in the output matrix
            output_matrix[row_idx, col_idx] = value

        return output_matrix

    def _filtered_qset(self):
        """
        Get filtered queryset to set as qset attribute, default to all object instances,
        or if there are index filters specified, apply index filters
        """
        qset = self.model.objects.all()
        filters = {}
        for axis in self.axes:
            if axis.qset:
                filters[axis.name+"__in"] = axis.qset
        if filters:
            qset = qset.filter(**filters)

        # sorts matrix elements so that they are in C-like indexing order
        qset = qset.order_by(self.axes.row.name, self.axes.col.name)

        return qset

    def update(self, new_values):
        """
        Runs multiple update to replace values with elements of given list
        Flattens new_values to 1-D array
        Arguments:
            new_values (np.ndarray)
        """
        # get or create, some objects may not exist yet
        for i, row_idx in enumerate(self.axes.row.index):
            for j, col_idx in enumerate(self.axes.col.index):
                filters = {
                    self.axes.row.name: row_idx,
                    self.axes.col.name: col_idx
                }
                self.model.objects.update_or_create(
                    **filters,
                    defaults={self.value_field: new_values[i, j]}
                )

        multiple_update(self.qset, self.value_field, new_values.flatten())

    def __getitem__(self, indices):
        """
        Examples:
            matrix = Matrix(..)
            matrix[:,model_instance]
            matrix[queryset,:]
            matrix[model_instance,]
        TODO could validate provided indices belong to correct model class
        :param indices: is a tuple (len 1 or 2) of model instances or Nones.
        :return: queryset corresponding to a row (if one selector present) or element
        """
        # Convert indices so that it is length 2
        # Valid case: Matrix[idx,] -> row vector
        if len(indices) == 1:
            indices = (indices[0], slice(None))

        # validate indices length
        if len(indices) != 2:
            raise ValueError

        # replace slice objects (:) with Nones
        indices = [idx if not isinstance(idx, slice) else None for idx in indices]

        # Case: Matrix[:,:]
        if not any(indices):
            return self

        # indicator for whether each index is a single model instance (as opposed to queryset)
        single_row = isinstance(indices[0], Model)
        single_col = isinstance(indices[1], Model)

        # Case - both indices are querysets or None: result should be a Matrix
        # pass along indices to matrix constructor
        if not (single_row or single_col):
            return Matrix(self.model, indices=indices)

        # Case - only one index is a model instance: result should be a Vector
        elif single_row ^ single_col:
            # create filters to apply to queryset
            filters = {}
            for a, idx in zip(self.axes, indices):
                if isinstance(idx, Model):
                    filters[a.name] = idx
                elif isinstance(idx, QuerySet):
                    filters[a.name+"__in"] = idx
            # construct axis objects for new Vector
            if single_row:
                axis = self.axes.col
                axis.qset = indices[1]
                slice_axis = self.axes.row
                slice_axis.qset = indices[0]
            elif single_col:
                axis = self.axes.row
                axis.qset = indices[0]
                slice_axis = self.axes.col
                slice_axis.qset = indices[1]
            # construct and return Vector object
            return Vector(self.model, axis=axis, slice_axis=slice_axis)

        # reduce to single value
        elif single_row and single_col:
            # create filters to apply to queryset
            filters = {
                self.axes.row.name: indices[0],
                self.axes.col.name: indices[1]
            }
            try:
                instance = self.model.objects.get(**filters)
            except self.model.DoesNotExist:
                return None
            return getattr(instance, self.value_field)

        else:
            return ValueError('Invalid array indexing attempted')


def value_index_map(array):
    """
    Given input array, returns dict with key/values k,i,
    where i is the 0-index where value k appeared in the input array
    Assumes array elements are unique
    Used to get a mapping from pk's of an query set axis to the 0-index
    :param array:
    :return: dict
    """
    output_map = {v: i for i, v in enumerate(array)}
    return output_map


def pk_index_map(qset):
    """
    Given queryset, return dict with key/values k,i,
    where i is the 0-index where instance with pk k appeared in the input array
    :param qset: queryset
    :return: dict
    """
    return value_index_map(qset.values_list('pk', flat=True))


def convert_pk_to_index(pk_tuples, indices):
    """
    For a list of tuples with elements referring to pk's of indices,
    convert pks to 0-index values corresponding to order of queryset
    :param pk_tuples: list of tuples [(row_pk, col_pk), ... ]
    :param indices: list of querysets
    :return: list of tuples [(row_idx, col_idx), ... ]
    """
    output_tuples = []
    maps = [pk_index_map(idx) for idx in indices]
    for pk_tuple in pk_tuples:
        try:
            idxs = tuple(maps[axis][pk] for axis, pk in enumerate(pk_tuple))
            output_tuples.append(idxs)
        except KeyError:
            # pk may not be in index scope which is fine
            pass

    return output_tuples
