from django.db.models.query import QuerySet
from django.db.models import Model


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

        # sorts matrix elements so that they are in linear indexing order
        # https://www.mathworks.com/help/matlab/math/matrix-indexing.html
        self.qset = model.objects.order_by(self.row_field, self.col_field)


        # TODO some validation to see if expected number of elements are present
    
    def shape(self):
        row_model = _meta.get_field(self.row_field).remote_field.model
        col_model = _meta.get_field(self.col_field).remote_field.model
        return (row_model.objects.count(), col_model.objects.count())

    # TODO values() method to get 2d nparray
    def values(self):
        """
        Returns 2d np array
        """
        return np.array(self.qset.values_list('values',flat=True)).reshape(self.shape())

    def __getitem__(self,indices):
        """
        indices is a tuple (of length 2) of model instances or Nones
        Returns a queryset corresponding to a row (if one selector present) or element

        Cases:
            specify single row or column index -> Vector (single row or column)
            specify queryset for either row or column index -> Matrix (subset of rows or columns)
        """
        if len(indices)!=2:
            raise Exception("Need to specify 2 indices")
        
        row_idx = indices[0]
        col_idx = indices[1]
        
        # XOR: either row/col specified, but not both
        if not bool(row_idx) ^ bool(col_idx): 
            raise NotImplementedError 


        idx = row_idx if row_idx else col_idx

        qset_args = {}
        # check type - single element or queryset
        if isinstance(idx, Model):

            # select single row or col -> Vector
            if row_idx: qset_args[self.row_field] = row_idx
            if col_idx: qset_args[self.col_field] = col_idx
            # TODO: maybe want to sort here?
            return Vector(self.model.objects.filter(*qset_args))

        elif isinstance(idx, QuerySet):
            # accept queryset as index selector -> output matrix
            if row_idx: qset_args[self.row_field+"__in"] = row_idx
            if col_idx: qset_args[self.col_field+"__in"] = col_idx

            return Matrix(self.model.objects.filter(*qset_args))


