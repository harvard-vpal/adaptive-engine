import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alosi.engine_api import EngineApi


@pytest.fixture
def engine_api(db, live_server):
    """
    Set up an engine test server and api user, and return an alosi api client to the engine
    :param db: https://pytest-django.readthedocs.io/en/latest/helpers.html#db
    :return: alosi.EngineApi instance
    """
    user = User.objects.create_superuser('myuser', 'myemail@test.com', 'password')
    token = Token.objects.create(user=user)
    api = EngineApi(live_server.url, token=None)
    api.client.headers.update({'Authorization': 'Token {}'.format(token.key)})
    return api
