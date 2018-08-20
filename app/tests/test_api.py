from alosi.engine_api import EngineApi
import pytest
import logging
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
log = logging.getLogger(__name__)


@pytest.fixture
def engine_api(db, live_server):
    """
    Test client using alosi EngineApi, with DRF RequestsClient
    :return:
    """

    user = User.objects.create_superuser('myuser', 'myemail@test.com', 'password')
    token = Token.objects.create(user=user)
    api = EngineApi(live_server.url, token=None)
    api.client.headers.update({'Authorization': 'Token {}'.format(token.key)})
    return api


def test_recommend(engine_api):
    print("client headers: {}".format(engine_api.client.headers))
    r = engine_api.recommend(
        learner=dict(
            user_id='my_user_id',
            tool_consumer_instance_guid='default'
        ),
        collection='test_collection'
    )
    log.warning("response text: {}".format(r.text))
    assert True
