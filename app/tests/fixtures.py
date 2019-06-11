import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alosi.engine_api import EngineApi
from engine.models import Collection, KnowledgeComponent, Activity, PrerequisiteRelation


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
def sequence_test_collection(db):
    """
    Collection with realistic data structure for testing sequence
    Creates collection, 12 activities, 2 KCs,
    :param db:
    :return: Collection model instance
    """
    collection = Collection.objects.create(collection_id='test')
    # create activities and associate with collection
    problems = []
    for i in range(10):
        activity = Activity(
            url='http://example.com/problem/{}'.format(i),
            name='activity {}'.format(i),
            type='problem'
        )
        activity.save()
        activity.collections.add(collection)
        problems.append(activity)

    # create some non-problem activities
    readings = []
    for i in range(2):
        activity = Activity(
            url='http://example.com/reading/{}'.format(i),
            name='reading {}'.format(i),
            type='html'
        )
        activity.save()
        activity.collections.add(collection)
        readings.append(activity)

    activities = problems + readings

    # create activity dependencies
    activity_prerequisites = {
        problems[8]: [readings[0]],  # problem 8 requires reading 0
        problems[9]: [readings[0],readings[1]],   # problem 9 requires reading 0 and 1
    }
    for dependent, prerequisites in activity_prerequisites.items():
        dependent.prerequisite_activities.set(prerequisites)

    # create knowledge components and relations
    kcs = []
    for i in range(2):
        kc = KnowledgeComponent(
            kc_id=i,
            name='kc {}'.format(i),
            mastery_prior=0.2,
        )
        kc.save()
        kcs.append(kc)

    PrerequisiteRelation.objects.create(
        prerequisite=kcs[0],
        knowledge_component=kcs[1],
        value=0.9
    )

    # tag activities with knowledge components
    for i in range(8):
        activities[i].knowledge_components.add(kcs[0])
    for i in range(4, 12):
        activities[i].knowledge_components.add(kcs[1])

    return collection
