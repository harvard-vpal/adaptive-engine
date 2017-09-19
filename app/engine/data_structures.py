from django.db.models.query import QuerySet
from django.db.models import Model
import numpy as np

def multiple_update(qset, field, values):
    new_qset = qset.filter().count()
    if qset.count()!=len(values):
        raise Exception('dimension mismatch')
    with transaction.atomic():
        for item, value in zip(qset, values):
            item.update(*{field:value})


class Vector(object):
    def __init__(self, qset):
        self.qset = qset
        # self.len = qset.count()
        # self.values = np.array(qset.values_list('value',flat=True))

    def values(self):
        """
        Return numpy array of raw values, using 'value' field
        """
        return np.array(self.qset.values_list('value',flat=True))

    def filter(self, **kwargs):
        """
        Apply filter to queryset and return new Vector
        """
        return Vector(self.qset.filter(**kwargs))

    def update(self, list):
        """
        Runs multiple update to replace values with elements of given list
        """
        multiple_update(self.qset,'value',new_values)

    # def add(self, obj, update=False):
    #     if isinstance(obj,list):
    #         self.add_list(obj, update)
    #     if isinstance(obj,Vector):
    #         self.add_vector(obj, update)

    # def add_vector(self, vector, update):
    #     """
    #     element-wise vector addition
    #     """
    #     values = vector.qset.values_list('value')
    #     self.add_list(values, update)

    # def add_list(self, list_to_add, update):
    #     """
    #     element-wise vector addition, that takes as input list
    #     """
    #     new_values = [i+j for i,j in zip(self.values+list_to_add)]
    #     if update:
    #         multiple_update(self.qset,'value',new_values)
    #     else:
    #         return new_values
            
    # def add_scalar(self, vector, update):
    #     values = vector.qset.values_list('value')


class Matrix(object):
    def __init__(self,model):
        self.model = model
        fields = [f.name for f in model._meta.get_fields()][1:]
        # assumption: row field is defined first, col field is defined second
        self.row_field = fields[0]
        self.col_field = fields[1]

        # sorts matrix elements so that they are in C-like indexing order
        self.qset = model.objects.order_by(self.row_field, self.col_field)


        # TODO some validation to see if expected number of elements are present
    
    def shape(self):
        row_model = self.model._meta.get_field(self.row_field).remote_field.model
        col_model = self.model._meta.get_field(self.col_field).remote_field.model
        return (row_model.objects.count(), col_model.objects.count())

    # TODO values() method to get 2d nparray
    def values(self):
        """
        Returns 2d np array
        """
        return np.array(self.qset.values_list('value',flat=True)).reshape(self.shape())

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
            row_idx = indices[0]
            col_idx = None

        elif len(indices)==2:
            # replace slice objects (:) in indices with Nones
            row_idx = indices[0] if not isinstance(indices[0],slice) else None
            col_idx = indices[1] if not isinstance(indices[1],slice) else None

        else:
            raise ValueError

        # Case: Matrix[:,:]
        if not row_idx or col_idx: 
            return self

        filters = {}

        for field,idx in {self.row_field:row_idx, self.col_field:col_idx}.items():
            print field,idx
            if isinstance(idx,Model):
                filters[field] = idx
            elif isinstance(idx,QuerySet):
                filters[field+"__in"] = idx
            elif idx:
                raise NotImplementedError

        if any([isinstance(idx,QuerySet) for idx in [row_idx,col_idx]]):
            return Matrix(self.model.objects.filter(**filters))
        else:
            return Vector(self.model.objects.filter(**filters))


