import logging
import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alosi.engine_api import EngineApi
from engine.models import Collection, KnowledgeComponent, Mastery, Learner, Activity


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


@pytest.fixture
def knowledge_component(db):
    """
    Create knowledge component
    :param db:
    :return: knowledge component model instance
    """
    return KnowledgeComponent.objects.create(kc_id='kc_id',name='kc name',mastery_prior=0.5)


@pytest.fixture
def activities(db):
    """
    Create two activities
    :param db:
    :return: queryset of knowledge components
    """
    kcs = [
        Activity(
            url='http://example.com/1',
            name='activity 1',
        ),
        Activity(
            url='http://example.com/2',
            name='activity 2',
        ),
    ]
    Activity.objects.bulk_create(kcs)
    return Activity.objects.filter(url__in=['http://example.com/1','http://example.com/2'])


def test_recommend(engine_api, test_collection):
    """
    Recommend activity via api
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
    assert r.ok


def test_create_knowledge_component(engine_api, test_collection):
    """
    Creates KC via api
    :param engine_api:
    :param test_collection:
    :return:
    """
    KC_ID = 'kc_id'
    KC_NAME = 'kc name'
    KC_MASTERY_PRIOR = 0.5
    r = engine_api.create_knowledge_component(
        kc_id = KC_ID,
        name = KC_NAME,
        mastery_prior = KC_MASTERY_PRIOR
    )
    assert r.ok


def test_knowledge_component_id_field(engine_api, knowledge_component):
    """
    Tests that 'id' field is available in knowledge component list endpoint data
    :param engine_api:
    :param knowledge_component:
    :return:
    """
    r = engine_api.request('GET', 'knowledge_component')  # kc list endpoint
    assert 'id' in r.json()[0]


@pytest.mark.django_db
def test_bulk_update_mastery(engine_api, knowledge_component):
    """
    Update mastery for a new learner via api
    Tests that learner is created, mastery object is created, and mastery value is updated (checks db)
    :param engine_api:
    :param knowledge_component:
    :return:
    """
    NEW_VALUE = 0.6
    LEARNER = {
        'user_id': 'user_id',
        'tool_consumer_instance_guid': 'tool_consumer_instance_guid'
    }
    data = [
        {
            'learner': LEARNER,
            'knowledge_component': {
                'kc_id': knowledge_component.kc_id
            },
            'value': NEW_VALUE
        }
    ]
    r = engine_api.bulk_update_mastery(data)
    assert r.ok

    learner = Learner.objects.get(
        user_id=LEARNER['user_id'],
        tool_consumer_instance_guid=LEARNER['tool_consumer_instance_guid']
    )

    mastery = Mastery.objects.get(
        learner=learner,
        knowledge_component=knowledge_component
    )
    assert mastery.value == NEW_VALUE


@pytest.mark.django_db
def test_api_create_prerequisite_activity(engine_api, activities):
    """
    Create prerequisite activity relation via api
    :param engine_api:
    :param knowledge_components:
    :return:
    """
    data = dict(
        from_activity=activities[1].pk,
        to_activity=activities[0].pk
    )
    r = engine_api.request('POST', 'prerequisite_activity', json=data)
    assert r.ok
