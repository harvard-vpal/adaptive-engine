import logging
import pytest
from engine.models import Collection, KnowledgeComponent, Mastery, Learner, Activity, PrerequisiteRelation
from .fixtures import engine_api
from time import sleep
import random

log = logging.getLogger(__name__)


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
            mastery_prior = 0.2,
        )
        kc.save()
        kcs.append(kc)

    PrerequisiteRelation.objects.create(
        prerequisite = kcs[0],
        knowledge_component = kcs[1],
        value=0.9
    )

    # tag activities with knowledge components
    for i in range(8):
        activities[i].knowledge_components.add(kcs[0])
    for i in range(4, 12):
        activities[i].knowledge_components.add(kcs[1])

    return collection


def test_sequence(engine_api, sequence_test_collection):
    """
    Simulates a student doing questions in the collection returned by sequence_test_collection fixture
    :param engine_api: fixture returning api client
    :param sequence_test_collection: fixture returning collection
    :return:
    """
    collection = sequence_test_collection
    activities = collection.activity_set.all()
    collection_id = collection.collection_id
    LEARNER = dict(
        user_id='my_user_id',
        tool_consumer_instance_guid='default'
    )

    random.seed(1)
    sequence = []
    for i in range(len(activities)):
        # recommend activity to learner
        r = engine_api.recommend(
            learner=LEARNER,
            collection=collection_id,
            sequence=sequence,
        )
        assert r.ok
        sleep(0.1)  # pytest-django local live server doesn't like requests too close to each other
        print("Engine recommendation response: {}".format(r.json()))
        recommended_activity = r.json()['source_launch_url']

        activity = Activity.objects.get(url=recommended_activity)

        # simulate student response
        sequence_item = {
            'activity': recommended_activity,
            'score': random.betavariate(i+1, len(activities)-i+1),
            'is_problem': True if activity.type == 'problem' else False,
        }
        sequence.append(sequence_item)
        if sequence_item['is_problem']:
            # submit score to api
            r = engine_api.submit_score(
                learner=LEARNER,
                activity=sequence_item['activity'],
                score=sequence_item['score']
            )
            assert r.ok
            sleep(0.1)
