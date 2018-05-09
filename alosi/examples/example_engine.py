import numpy as np
from alosi.engine import BaseAdaptiveEngine


class LocalAdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self):
        self.Scores = np.array([
            [0, 0, 1.0],
            [0, 1, 0.7],
        ])
        self.Mastery = np.array([
            [0.1, 0.2],
            [0.3, 0.5],
        ])
        self.MasteryPrior = np.array([0.1, 0.1])

    def get_guess(self, activity_id=None):
        GUESS = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6]
        ])
        if activity_id is not None:
            return GUESS[activity_id]
        else:
            return GUESS

    def get_slip(self, activity_id=None):
        return self.get_guess(activity_id)

    def get_transit(self, activity_id=None):
        return self.get_guess(activity_id)

    def get_difficulty(self):
        return np.array([0.1, 0.5, 0.9])

    def get_prereqs(self):
        return np.array([
            [0.0, 1.0],
            [0.0, 0.0]
        ])

    def get_r_star(self, learner_id=None):
        return 2.2

    def get_L_star(self, learner_id=None):
        return 0.0

    def get_last_attempted_guess(self, learner_id=None):
        return np.array([0.5, 0.3])

    def get_last_attempted_slip(self, learner_id=None):
        return np.array([0.5, 0.4])

    def get_learner_mastery(self, learner_id=None):
        return np.log([0.5, 0.7])

    def get_mastery_prior(self):
        return self.MasteryPrior

    def get_W_p(self, learner_id=None):
        return 0.25

    def get_W_r(self, learner_id=None):
        return 0.25

    def get_W_d(self, learner_id=None):
        return 0.25

    def get_W_c(self, learner_id=None):
        return 0.25

    def get_scores(self):
        return self.Scores

    def save_score(self, learner_id, activity_id, score):
        self.Scores = np.vstack((self.Scores, [learner_id, activity_id, score]))

    def update_learner_mastery(self, learner_id, new_mastery):
        self.Mastery[learner_id] = new_mastery


engine = LocalAdaptiveEngine()

engine.recommend(learner_id=1)

engine.update_from_score(learner_id=0, activity_id=0, score=0.5)

engine.train()

