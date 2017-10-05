import numpy as np
from engine.models import *
from .utils import reset_database
from engine.engines import initialize_learner, get_engine


class EngineSimulator(object):
    """
    Base engine simulator that assumes that database models have already been populated
    Explicitly calls engine subfunctions to simulate the submit and recommmend operations
    """
    def __init__(self, initializer=None, **kwargs):
        # initialize database
        if initializer:
            initializer(**kwargs)

    def submit_score(self, learner=None, activity=None, score=None):
        """
        Arguments:
            learner (int): learner id
            activity (int): activity id
            score (float): score value
        """
        activity = Activity.objects.get(pk=activity)
        learner, created = Learner.objects.get_or_create(pk=learner)
        if created:
            initialize_learner(learner)
        engine = get_engine(learner)
        score = Score(learner=learner, activity=activity, score=score)
        engine.update(score)

    def recommend(self, learner=None, collection=None):
        """
        Arguments:
            learner (int): learner id
            collection (int): collection id
        """
        collection_obj = Collection.objects.get(pk=collection)
        learner_obj, created = Learner.objects.get_or_create(pk=learner)
        if created:
            initialize_learner(learner_obj)
        engine = get_engine(learner_obj)
        activity_recommendation = engine.recommend(learner_obj, collection_obj)
        return activity_recommendation.pk if activity_recommendation else None
