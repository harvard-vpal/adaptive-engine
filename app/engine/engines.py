from builtins import super
import numpy as np
from .data_structures import Matrix
from .models import *
from alosi.engine import BaseAdaptiveEngine


def get_engine(engine_settings=None):
    """
    Get relevant engine for learner based on their experimental group
    Also assigns experimental group if none assigned
    """
    # if learner.experimental_group:
    #     engine_settings = learner.experimental_group.engine_settings
    #     return AdaptiveEngine(engine_settings)
    if not engine_settings:
        engine_settings = EngineSettings(
            L_star=2.2,
            r_star=0.0,
            W_r=2.0,  # demand
            W_c=1.0,  # continuity
            W_p=1.0,  # readiness
            W_d=0.5,  # difficulty
        )
    return AdaptiveEngine(engine_settings)


class NonAdaptiveEngine(object):
    """
    Engine that serves only activities that have the 'nonadaptive_order' 
    field populated (and in the order specified by that field)
    """
    def __init__(self):
        pass

    def initialize_learner(self, learner_id):
        """
        Don't need to initialize additional data for non-adaptive case
        """
        pass

    def update(self, score):
        """
        No additional action needed
        """
        score.save()

    def recommend(self, learner, collection, history=None):
        """
        Recommend activity according to 'nonadaptive_order' field
        """
        activity_urls = [item['activity'] for item in history]
        candidate_activities = collection.activity_set.exclude(url__in=activity_urls)
        return candidate_activities.first()


class AdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self, engine_settings):
        self.engine_settings = engine_settings

    def recommend(self, learner_id, collection_id, sequence):
        """

        :param learner_id:
        :param collection_id:
        :param sequence: list of activities learner has previously completed in sequence context
        :return:
        """
        return super().recommend(learner_id)

    def get_guess(self, activity_id=None):
        """
        Get guess matrix, or row of guess matrix if activity_id specified
        :param activity_id: url id of activity
        :return:
        """
        if activity_id is not None:
            activity = Activity.objects.get(pk=activity_id)
            return Matrix(Guess)[activity, ].values()
        else:
            return Matrix(Guess).values()

    def get_slip(self, activity_id=None):
        """
        Get slip matrix, or row of slip matrix if activity_id specified
        :param activity_id:
        :return:
        """
        if activity_id is not None:
            activity = Activity.objects.get(pk=activity_id)
            return Matrix(Slip)[activity, ].values()
        else:
            return Matrix(Slip).values()

    def get_transit(self, activity_id=None):
        """
        Get transit matrix, or row of transit matrix if activity_id specified
        :param activity_id:
        :return:
        """
        if activity_id is not None:
            activity = Activity.objects.get(pk=activity_id)
            return Matrix(Transit)[activity, ].values()
        else:
            return Matrix(Transit).values()

    def get_difficulty(self):
        """
        Get activity difficulty values
        :return:
        """
        return np.array(Activity.objects.values_list('difficulty', flat=True))

    def get_prereqs(self):
        """
        Get prereq matrix
        :return:
        """
        return Matrix(PrerequisiteRelation).values()

    def get_r_star(self, learner_id=None):
        """
        Get r_star parameter value for learner's experimental group engine settings
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.r_star

    def get_L_star(self, learner_id=None):
        """
        Get L_star parameter value for learner's experimental group engine settings
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.L_star

    def get_last_attempted_guess(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        user_scores = Score.objects.filter(learner_id=learner_id)
        if user_scores:
            last_attempted = user_scores.latest('timestamp').activity
            return Matrix(Guess)[last_attempted, ].values()
        else:
            return None

    def get_last_attempted_slip(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        user_scores = Score.objects.filter(learner_id=learner_id)
        if user_scores:
            last_attempted = user_scores.latest('timestamp').activity
            return Matrix(Slip)[last_attempted, ].values()
        else:
            return None

    def get_learner_mastery(self, learner_id=None):
        """
        :param learner_id: int, learner pk
        :return:
        """
        learner = Learner.objects.get(pk=learner_id)
        return Matrix(Mastery)[learner, ].values()

    def get_mastery_prior(self):
        """
        :return:
        """
        knowledge_components = KnowledgeComponent.objects.all()
        return np.array([kc.mastery_prior for kc in knowledge_components])

    def get_W_p(self, learner_id):
        """
        Get W_p parameter value for learner's experimental group engine settings
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.W_p

    def get_W_r(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.W_r

    def get_W_d(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.W_d

    def get_W_c(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        return self.engine_settings.W_c

    def get_scores(self):
        """
        The second column in this matrix should be the row index (0-indexed) of the activity's position
        in the Guess/Slip/Transit matrices
        :return: ? x 3 np.array
        """
        score_records = Score.objects.values_list('learner_id', 'activity_id', 'score')
        # convert activity pk to 0-indexed id, taking into account possible non-consecutive pks
        pks = Activity.objects.values_list('pk', flat=True)
        # map from pk to 0-index
        idx = {pk: i for i, pk in enumerate(pks)}
        for i, r in enumerate(score_records):
            score_records[i][1] = idx[r[1]]
        return np.asarray(score_records)

    def save_score(self, learner_id, activity_id, score):
        activity = Activity.objects.get(pk=activity_id)
        Score.objects.create(learner_id=learner_id, activity_id=activity.pk, score=score)

    def update_learner_mastery(self, learner_id, new_mastery):
        """
        :param learner_id: int, learner pk
        :param new_mastery: 1x(# LOs) np.array vector of new mastery values
        """
        learner = Learner.objects.get(pk=learner_id)
        Matrix(Mastery)[learner, ].update(new_mastery)

    def initialize_learner(self, learner_id):
        """
        Action to take when new learner is created
        """
        knowledge_components = KnowledgeComponent.objects.all()

        # add mastery row
        Mastery.objects.bulk_create([
            Mastery(
                learner_id=learner_id,
                knowledge_component=kc,
                value=kc.mastery_prior,
            ) for kc in knowledge_components
        ])
