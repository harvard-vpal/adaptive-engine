import logging
import random
from time import sleep
import pytest
from engine.models import Collection, KnowledgeComponent, Mastery, Learner, Activity, PrerequisiteRelation
from .fixtures import engine_api, sequence_test_collection
from alosi.engine import EPSILON
log = logging.getLogger(__name__)


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

            learner = Learner.objects.get(**LEARNER)
            mastery = Mastery.objects.filter(learner=learner).values_list('value', flat=True)
            # test that learner mastery values are between epsilon and (1-epsilon)
            assert all([EPSILON <= x <= (1-EPSILON) for x in mastery])
    print("Final sequence:")
    for a in sequence:
        print(a)

    # test grade after sequence
    data = {
        'learner': LEARNER
    }
    r = engine_api.request('POST', f'collection/{sequence_test_collection.collection_id}/grade', json=data)
    print(f'grade after sequence: {r.json()}')
    assert r.ok
