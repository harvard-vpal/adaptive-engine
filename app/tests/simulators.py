import numpy as np
from engine.models import *
from django.apps import apps
from engine import engines, utils
from .utils import reset_database

class EngineSimulator():
    """
    Base engine simulator that assumes that database models have already been populated
    Explicitly calls engine subfunctions to simulate the submit and recommmend operations
    """
    def __init__(self, initializer=None, **kwargs):
        # initialize database
        if initializer:
            initializer(**kwargs)

    def submit_score(self, learner_id, activity_id, score_value):
        activity = Activity.objects.get(pk=activity_id)
        learner, created = Learner.objects.get_or_create(pk=learner_id)
        
        if created or not learner.experimental_group:
            engine = engines.get_engine(learner)
            engine.initialize_learner(learner)
        else:
            engine = engines.get_engine(learner)
        score = Score(learner=learner, activity_id=activity_id, score=score_value)
        # do bayes update
        engine.update(score)
        score.save()

    def recommend(self, learner_id, collection_id):
        collection = Collection.objects.get(pk=collection_id)
        learner, created = Learner.objects.get_or_create(pk=learner_id)
        if created or not learner.experimental_group:
            engine = engines.get_engine(learner)
            engine.initialize_learner(learner)
        else:
            engine = engines.get_engine(learner)
        # make recommendation
        recommended_activity = engine.recommend(learner, collection)
        return recommended_activity


class EngineApiInterface(object):
    def __init__(self, host="http://localhost:8000", token=None):
        self.base_url = host+'/engine/api'
        self.headers = {'Authorization': 'Token {}'.format(token)} if token else {}
    def create_activity(self, activity_data):
        r = requests.post(self.base_url+'/activity',headers=self.headers)
    def recommend_activity(self, activity_id, collection_id):
        r = requests.get(self.base_url+'/activity',params=dict(activity=activity_id, collection=collection_id),headers=self.headers)
    def submit_score(self, score_data):
        r = requests.post(self.base_url+'/activity', json=activity)


class EngineApiSimulator(EngineSimulator):
    def __init__(self, engine_api, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.engine_api = engine_api
        
    def initialize_activities(self):
        for i in range(self.num_activities):
            pk = i+1
            self.engine_api.create_activity(dict(
                pk=pk,
                name="Activity {}".format(pk),
                # how to initialize knowledge component?
                tags="tag1,tag2"
            ))


class BridgeSimulator(object):
    def __init__(self, num_learners):
        self.num_learners = num_learners
        self.learners = [LearnerSimulator() for i in range(num_learners)]


    def simulate(self, engine, num_trials=100):
        for i in range(num_trials):
            learner_id = np.random.randint(0,len(self.learners))+1
            learner = self.learners[learner_id-1]
            recommendation = engine.recommend(learner_id, collection_id=1)
            if recommendation:
                score = learner.attempt_activity(recommendation)
                engine.submit_score(learner_id,recommendation.pk,score)


class LearnerSimulator(object):
    def __init__(self):
        pass
    def attempt_activity(self, activity):
        return np.random.uniform()
