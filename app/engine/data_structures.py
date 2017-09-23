from django.db.models.query import QuerySet
from django.db.models.base import ModelBase
from django.db.models import Model
import numpy as np
from django.db import transaction
from collections import namedtuple


@transaction.atomic
def multiple_update(qset, field, values):
    if qset.count()!=len(values):
        raise Exception('dimension mismatch')
    for item, value in zip(qset, values):
        setattr(item, field, value)
        item.save()


class Vector(object):
    """
    Vector data structure that wraps a django model
    """
    def __init__(self, qset, value_field='value'):
        """
        Arguments:
            qset (QuerySet): should already be sorted
            value_field (str): name of model field to expect value
        """
        self.qset = qset
        self.value_field = value_field

    def values(self):
        """
        Return 1-d numpy array of raw values, using 'value' field 
        (or custom field specified by vector.value_field)
        """
        return np.array(self.qset.values_list(self.value_field,flat=True))

    def filter(self, **kwargs):
        """
        Apply filter to queryset and return new Vector
        """
        return Vector(self.qset.filter(**kwargs))

    def update(self, new_values):
        """
        Runs multiple update to replace values with elements of given list
        """
        multiple_update(self.qset,self.value_field,new_values)

    def length(self):
        return self.qset.count()


class Matrix(object):
    """
    Matrix data structure that wraps a django model
    """

    Axes = namedtuple('Axes',['row','col'])
    Axis = namedtuple('axis',['name','model','index'])

    def __init__(self,model,indices=None, value_field='value'):
        if isinstance(model, ModelBase):
            self.model = model
        else:
            raise ValueError

        # assumption: first field definied in model definition is row field, 
        # col field is defined second
        self.axes = Matrix.Axes._make([
            Matrix.Axis(
                name=field.name,
                model=field.remote_field.model,
                index=index,
            ) for field, index in zip(
                self.model._meta.get_fields()[1:3],
                self._validate_indices(indices)
            )
        ])

        # filter qset by any provided indices
        self.qset = self._filtered_qset()
        # sorts matrix elements so that they are in C-like indexing order
        self.qset.order_by(self.axes.row.name, self.axes.col.name)
        self.value_field = value_field
        # TODO some validation to see if expected number of elements are present
    
    def shape(self):
        """
        Return 2-tuple of dimensions
        """
        return tuple([a.index.count() if a.index else a.model.objects.count() for a in self.axes])

    # TODO values() method to get 2d nparray
    def values(self):
        """
        Returns 2d np array
        """
        return np.array(self.qset.values_list(self.value_field,flat=True)).reshape(self.shape())

    def _validate_indices(self, indices):
        """
        Validate and prepare indices input argument to Matrix constructor
        """
        if indices:
            # expect list/tuple
            if not isinstance(indices, (list, tuple)):
                raise ValueError
            # expect size 2
            if len(indices)!=2:
                raise ValueError
            # both indices should be QuerySets or None
            if not all([isinstance(idx, QuerySet) for idx in indices if idx]):
                raise ValueError
        else:
            indices = [None, None]
        return indices

    def _filtered_qset(self):
        """
        Set qset attribute, default to all object instances, 
        or if there are index filters specified, apply index filters
        """
        qset = self.model.objects.all()
        filters = {}
        for axis in self.axes:
            if axis.index:
                filters[axis.name+"__in"]=axis.index
        if filters:
            qset = qset.filter(**filters)
        return qset

    def update(self, new_values):
        """
        Runs multiple update to replace values with elements of given list
        Flattens new_values to 1-D array
        Arguments:
            new_values (np.ndarray)
        """
        multiple_update(self.qset,self.value_field,new_values.flatten())

    def __getitem__(self,indices):
        """
        Arguments:
            indices: is a tuple (of length 2) of model instances or Nones
        Returns a queryset corresponding to a row (if one selector present) or element
        Examples:
            matrix = Matrix(..)
            matrix[:,model_instance]
            matrix[queryset,:]
            matrix[model_instance,]
        """
        if not isinstance(indices, tuple):
            raise ValueError

        # Case: Matrix[idx,] -> row vector
        if len(indices)==1:
            indices = (indices[0],None)

        if len(indices)==2:
            # replace slice objects (:) in indices with Nones
            indices = [idx if not isinstance(idx,slice) else None for idx in indices]
        else:
            raise ValueError

        # Case: Matrix[:,:]
        if not any(indices): 
            return self
        
        if any([isinstance(idx,QuerySet) for idx in indices]):
            return Matrix(self.model, indices=indices)
        else:
            filters = {}
            for a,idx in zip(self.axes,indices):
                if isinstance(idx,Model):
                    filters[a.name] = idx
                elif isinstance(idx,QuerySet):
                    filters[a.name+"__in"] = idx
                elif idx:
                    raise NotImplementedError
            return Vector(self.model.objects.filter(**filters))
