import logging
import pytest
from engine.models import Collection, KnowledgeComponent, Mastery, Learner, Activity, PrerequisiteRelation
from .fixtures import engine_api
from time import sleep
import random

log = logging.getLogger(__name__)


@pytest.fixture
def hpl_test_resources(db):
    """
    Create resources to simulate hpl use case:
        - KCs
        - collection containing two activities
    :param db:
    :return:
    """
    #create collection
    collection = Collection.objects.create(collection_id='hpl')

    # create activities and associate with collection
    problems = []
    activities = [
        Activity(
            url='http://example.com/3_Lawrence',
            name='3_Lawrence',
            type='html'
        ),
        Activity(
            url='http://example.com/4_SNHU',
            name='4_SNHU',
            type='html'
        )
    ]
    for activity in activities:
        activity.save()
        activity.collections.add(collection)

    # create knowledge components and relations
    kc_ids_1 = ['sect_academic','sect_consult','sect_policy','sect_prek12','role_admin','role_consult',
                'role_counsel','role_curricdev','role_coach','role_orgspec','role_policy','role_profdev',
                'role_research','role_teaching','prox_instruct','prox_leader','prox_system'
                ]
    kc_ids_2 = ['sect_academic','sect_consult','sect_corp','sect_highered','sect_mediatech','sect_nonprof',
                'role_admin','role_advoc','role_consult','role_counsel','role_curricdev','role_coach',
                'role_mediatech','role_orgspec','role_policy','role_profdev','role_teaching',
                'prox_instruct','prox_leader','prox_system']
    kc_ids = sorted(list(set(kc_ids_1 + kc_ids_2)))
    kcs = [KnowledgeComponent(kc_id=kc_id, name=kc_id, mastery_prior=0.5) for kc_id in kc_ids]
    for kc in kcs:
        kc.save()

    # tag activites with knowledge components
    activities[0].knowledge_components.set(KnowledgeComponent.objects.filter(kc_id__in=kc_ids_1))
    activities[1].knowledge_components.set(KnowledgeComponent.objects.filter(kc_id__in=kc_ids_2))

    return dict(collection=collection, kcs=kcs)

@pytest.fixture
def hpl_test_learner_lawrence(db):
    """
    Create learner with masteries
    :param db:
    :return:
    """
    # case:
    learner = Learner(user_id='hpl_test_learner_lawrence',tool_consumer_instance_guid='default')
    learner.save()
    Mastery.objects.bulk_create([
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_highered'), value=0.9),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_mediatech'), value=0.9),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_prek12'), value=0.1),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_policy'), value=0.1),
    ])
    return learner

@pytest.fixture
def hpl_test_learner_snhu(db):
    """
    Create learner with masteries
    :param db:
    :return:
    """
    # case:
    learner = Learner(user_id='hpl_test_learner_snhu', tool_consumer_instance_guid='default')
    learner.save()
    Mastery.objects.bulk_create([
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_highered'), value=0.2),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_mediatech'), value=0.2),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_prek12'), value=0.8),
        Mastery(learner=learner, knowledge_component=KnowledgeComponent.objects.get(kc_id='sect_policy'), value=0.8),
    ])
    return learner

def test_hpl_recommend_lawrence(engine_api, hpl_test_resources, hpl_test_learner_lawrence):
    """
    Test recommendation behavior, given collection and prepopulated masteries for learner that should be
    expected to receive lawrence as recommendation
    """
    collection = hpl_test_resources['collection']
    learner = hpl_test_learner_lawrence
    r = engine_api.recommend(
        learner=dict(
            user_id=learner.user_id,
            tool_consumer_instance_guid=learner.tool_consumer_instance_guid
        ),
        collection=collection.collection_id,
        sequence=[]
    )
    assert r.json()['source_launch_url'] == 'http://example.com/3_Lawrence'


def test_hpl_recommend_snhu(engine_api, hpl_test_resources, hpl_test_learner_snhu):
    """
    Test recommendation behavior, given collection and prepopulated masteries for learner that should be
    expected to receive snhu as recommendation
    """
    collection = hpl_test_resources['collection']
    learner = hpl_test_learner_snhu
    r = engine_api.recommend(
        learner=dict(
            user_id=learner.user_id,
            tool_consumer_instance_guid=learner.tool_consumer_instance_guid
        ),
        collection=collection.collection_id,
        sequence=[]
    )
    log.warning([kc.kc_id for kc in hpl_test_resources['kcs']])
    assert r.json()['source_launch_url'] == 'http://example.com/4_SNHU'
