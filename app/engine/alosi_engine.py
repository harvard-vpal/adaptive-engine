import numpy as np
from engine.models import Activity, Learner, Score, Guess, Slip, Transit, PrerequisiteRelation, KnowledgeComponent, \
    Mastery
from engine.data_structures import Matrix, Vector
from alosi.engine import BaseAdaptiveEngine


class DjangoAdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self):
        pass

    def get_guess(self, activity_id=None):
        if activity_id is not None:
            activity = Activity.objects.get(url=activity_id)
            return Matrix(Guess)[activity, ].values()
        else:
            return Matrix(Guess).values()

    def get_slip(self, activity_id=None):
        if activity_id is not None:
            activity = Activity.objects.get(url=activity_id)
            return Matrix(Slip)[activity, ]
        else:
            return Matrix(Slip).values()

    def get_transit(self, activity_id=None):
        if activity_id is not None:
            activity = Activity.objects.get(url=activity_id)
            return Matrix(Transit)[activity, ]
        else:
            return Matrix(Transit).values()

    def get_difficulty(self):
        return np.array(Activity.objects.values_list('difficulty', flat=True))

    def get_prereqs(self):
        return Matrix(PrerequisiteRelation).values()

    def get_r_star(self, learner_id=None):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.r_star

    def get_L_star(self, learner_id=None):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.L_star

    def get_last_attempted_guess(self, learner_id=None):
        last_attempted = Score.objects.filter(learner_id=learner_id).latest('timestamp').activity
        return Matrix(Guess)[last_attempted, ].values()

    def get_last_attempted_slip(self, learner_id=None):
        last_attempted = Score.objects.filter(learner_id=learner_id).latest('timestamp').activity
        return Matrix(Slip)[last_attempted, ].values()

    def get_learner_mastery(self, learner_id=None):
        learner = Learner.objects.get(pk=learner_id)
        return Matrix(Mastery)[learner, ].values()

    def get_mastery_prior(self):
        knowledge_components = KnowledgeComponent.objects.all()
        return np.array([kc.mastery_prior for kc in knowledge_components])

    def get_W_p(self, learner_id):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_p

    def get_W_r(self, learner_id):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_r

    def get_W_d(self, learner_id):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_d

    def get_W_c(self, learner_id):
        settings = Learner.objects.get(pk=learner_id).experimental_group.engine_settings
        return settings.W_c

    def get_scores(self):
        return np.asarray(Score.objects.values_list('learner_id', 'activity_id', 'score'))

    def save_score(self, learner_id, activity_id, score):
        activity = Activity.objects.get(url=activity_id)
        Score.objects.create(learner_id=learner_id, activity_id=activity.pk, score=score)

    def update_learner_mastery(self, learner_id, new_mastery):
        learner = Learner.objects.get(pk=learner_id)
        Matrix(Mastery)[learner, ].update(new_mastery)
