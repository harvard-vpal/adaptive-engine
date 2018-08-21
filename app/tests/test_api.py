import logging
import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alosi.engine_api import EngineApi
from engine.models import Collection


log = logging.getLogger(__name__)


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


@pytest.fixture
def test_collection(db):
    """
    Create empty test collection
    :param db: https://pytest-django.readthedocs.io/en/latest/helpers.html#db
    :return: Collection model instance
    """
    collection = Collection.objects.create(collection_id='test_collection',name='foo')
    return collection


def test_recommend(engine_api, test_collection):
    """
    Test recommendation api endpoint
    :param engine_api: alosi.EngineApi instance
    :param test_collection: Collection model instance
    """
    r = engine_api.recommend(
        learner=dict(
            user_id='my_user_id',
            tool_consumer_instance_guid='default'
        ),
        collection=test_collection.collection_id,
        sequence=[]
    )
    log.warning("response text: {}".format(r.text))
    assert r.status_code == 200
