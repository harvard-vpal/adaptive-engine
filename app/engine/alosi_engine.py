import numpy as np
from engine.models import Activity, Learner, Score, Guess, Slip, Transit, PrerequisiteRelation, KnowledgeComponent, \
    Mastery
from engine.data_structures import Matrix, Vector
from alosi.engine import BaseAdaptiveEngine


class DjangoAdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self):
        pass

    def get_guess(self, activity_id=None):
        """
        Get guess matrix, or row of guess matrix if activity_id specified
        :param activity_id: url id of activity
        :return:
        """
        if activity_id is not None:
            activity = Activity.objects.get(url=activity_id)
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
            activity = Activity.objects.get(url=activity_id)
            return Matrix(Slip)[activity, ]
        else:
            return Matrix(Slip).values()

    def get_transit(self, activity_id=None):
        """
        Get transit matrix, or row of transit matrix if activity_id specified
        :param activity_id:
        :return:
        """
        if activity_id is not None:
            activity = Activity.objects.get(url=activity_id)
            return Matrix(Transit)[activity, ]
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
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.r_star

    def get_L_star(self, learner_id=None):
        """
        Get L_star parameter value for learner's experimental group engine settings
        :param learner_id: int, learner pk
        :return:
        """
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.L_star

    def get_last_attempted_guess(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        last_attempted = Score.objects.filter(learner_id=learner_id).latest('timestamp').activity
        return Matrix(Guess)[last_attempted, ].values()

    def get_last_attempted_slip(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        last_attempted = Score.objects.filter(learner_id=learner_id).latest('timestamp').activity
        return Matrix(Slip)[last_attempted, ].values()

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
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_p

    def get_W_r(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_r

    def get_W_d(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_d

    def get_W_c(self, learner_id):
        """
        :param learner_id: int, learner pk
        :return:
        """
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_c

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
        activity = Activity.objects.get(url=activity_id)
        Score.objects.create(learner_id=learner_id, activity_id=activity.pk, score=score)

    def update_learner_mastery(self, learner_id, new_mastery):
        """
        :param learner_id: int, learner pk
        :param new_mastery: 1x(# LOs) np.array vector of new mastery values
        """
        learner = Learner.objects.get(pk=learner_id)
        Matrix(Mastery)[learner, ].update(new_mastery)
