from django.apps import apps
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


def reset_database(app='engine'):
        for model in apps.all_models[app].values():
            model.objects.all().delete()


def create_token(key=None):
    user = User.objects.create()
    return Token.objects.create(user=user,key=key).key
