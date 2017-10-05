from django.apps import apps
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import numpy as np
import pandas as pd


def reset_database(app='engine'):
    for model in apps.all_models[app].values():
        model.objects.all().delete()

def create_token(key=None):
    user = User.objects.create()
    return Token.objects.create(user=user,key=key).key

def inverse_odds(x):
    return np.exp(x)/(1+np.exp(x))

def map_column(column, mapping_dict):
    return column.apply(lambda x: mapping_dict[x])

def replace_nan_none(x):
    """
    Returns the same value, but replaces NaN with None
    Used when setting an integer model field with np/pd NaN
    """
    return x if pd.notnull(x) else None
