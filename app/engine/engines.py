import numpy as np
from .data_structures import Matrix
from .models import *
from alosi.engine import BaseAdaptiveEngine, recommendation_score


def get_engine(engine_settings=None):
    """
    Get relevant engine for learner based on their experimental group
    Also assigns experimental group if none assigned
    :param engine_settings: EngineSettings model instance
    """
    if engine_settings is None:
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

    def initialize_learner(self, learner):
        """
        Don't need to initialize additional data for non-adaptive case
        :param learner: not used, kept in definition for api consistency
        """
        pass

    def update_from_score(self, learner, activity, score):
        """
        Saves score, no additional param initialization needed
        :param learner: Learner model instance
        :param activity: Learner model instance
        :param score: float, score value
        :return: n/a
        """
        Score.objects.create(learner=learner, activity=activity, score=score)

    def recommend(self, learner, collection, sequence=None):
        """
        Recommend activity according to 'nonadaptive_order' field
        :param learner: Learner model instance
        :param collection: Collection model instance
        :param sequence: list of activity dicts, learner's sequence history
        :return: n/a
        """

        activity_urls = [item['activity'] for item in sequence]
        candidate_activities = collection.activity_set.exclude(url__in=activity_urls)
        return candidate_activities.first()


class AdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self, engine_settings):
        self.engine_settings = engine_settings

    def get_guess(self, activity=None):
        """
        Get guess matrix, or row(s) of guess matrix if activity specified
        :param activity: Activity model instance or queryset
        :return:
        """
        if activity is not None:
            return Matrix(Guess)[activity, ].values()
        else:
            return Matrix(Guess).values()

    def get_slip(self, activity=None):
        """
        Get slip matrix, or row(s) of slip matrix if activity specified
        :param activity: Activity model instance or queryset
        :return:
        """
        if activity is not None:
            return Matrix(Slip)[activity, ].values()
        else:
            return Matrix(Slip).values()

    def get_transit(self, activity=None):
        """
        Get transit matrix, or row(s) of transit matrix if activity specified
        :param activity: Activity model instance or queryset
        :return: len(activity) x (# LOs) np.array
        """
        if activity is not None:
            return Matrix(Transit)[activity, ].values()
        else:
            return Matrix(Transit).values()

    def get_difficulty(self, activity=None):
        """
        Get activity difficulty values
        :param activity: Activity queryset
        :return: 1 x len(activity) np.array vector
        """
        if activity is not None:
            return np.array(activity.values_list('difficulty', flat=True))
        else:
            return np.array(Activity.objects.values_list('difficulty', flat=True))

    def get_prereqs(self):
        """
        Get Prerequisite matrix
        :return: (# LOs) x (# LOs) np.array matrix
        """
        return Matrix(PrerequisiteRelation).values()

    def get_last_attempted_guess(self, learner):
        """
        :param learner: Learner object instance
        :return: 1 x (# LOs) np.array vector
        """
        user_scores = Score.objects.filter(learner=learner)
        if user_scores:
            last_attempted = user_scores.latest('timestamp').activity
            return Matrix(Guess)[last_attempted, ].values()
        else:
            return None

    def get_last_attempted_slip(self, learner):
        """
        :param learner: Learner object instance
        :return: 1 x (# LOs) np.array vector
        """
        user_scores = Score.objects.filter(learner=learner)
        if user_scores:
            last_attempted = user_scores.latest('timestamp').activity
            return Matrix(Slip)[last_attempted, ].values()
        else:
            return None

    def get_learner_mastery(self, learner):
        """
        :param learner: Learner model instance
        :return: 1 x (# LOs) np.array vector
        """
        return Matrix(Mastery)[learner, ].values()

    def get_mastery_prior(self):
        """
        Get mastery prior values for learning objectives
        :return: 1 x (#LOs) np.array vector
        """
        knowledge_components = KnowledgeComponent.objects.all()
        return np.array([kc.mastery_prior for kc in knowledge_components])

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

    def save_score(self, learner, activity, score):
        """
        :param learner: Learner model instance
        :param activity: Activity model instance
        :param score: float, score value
        """
        Score.objects.create(learner=learner, activity=activity, score=score)

    def update_learner_mastery(self, learner, new_mastery):
        """
        :param learner_id: int, learner pk
        :param new_mastery: 1 x (# LOs) np.array vector of new mastery values
        """
        Matrix(Mastery)[learner, ].update(new_mastery)

    def initialize_learner(self, learner):
        """
        Action to take when new learner is created
        :param learner: Learner model instance
        """
        knowledge_components = KnowledgeComponent.objects.all()

        # add mastery row
        Mastery.objects.bulk_create([
            Mastery(
                learner=learner,
                knowledge_component=kc,
                value=kc.mastery_prior,
            ) for kc in knowledge_components
        ])

    def get_recommend_params(self, learner, valid_activities):
        """
        Retrieve features/params needed for doing recommendation
        Calls data/param retrieval functions that may be implementation(prod vs. prototype)-specific
        TODO: could subset params based on activities in collection scope, to reduce unneeded computation
        :param learner: Learner model instance
        :return: dictionary with following keys:
            guess: QxK np.array, guess parameter values for activities
            slip: QxK np.array, slip parameter values for activities
            difficulty: 1xQ np.array, difficulty values for activities
            prereqs: QxQ np.array, prerequisite matrix
            r_star: float, Threshold for forgiving lower odds of mastering pre-requisite LOs.
            L_star: float, Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered
            W_p: (float), weight on substrategy P
            W_r: (float), weight on substrategy R
            W_d: (float), weight on substrategy D
            W_c: (float), weight on substrategy C
            last_attempted_guess: 1xK vector of guess parameters for activity
            last_attempted_slip: 1xK vector of slip parameters for activity
            learner_mastery: 1xK vector of learner mastery values
        """
        return {
            'guess': self.get_guess(valid_activities),
            'slip': self.get_slip(valid_activities),
            'difficulty': self.get_difficulty(valid_activities),
            'prereqs': self.get_prereqs(),
            'last_attempted_guess': self.get_last_attempted_guess(learner),
            'last_attempted_slip': self.get_last_attempted_slip(learner),
            'learner_mastery': self.get_learner_mastery(learner),
            'r_star': self.engine_settings.r_star,
            'L_star': self.engine_settings.L_star,
            'W_p': self.engine_settings.W_p,
            'W_r': self.engine_settings.W_r,
            'W_d': self.engine_settings.W_d,
            'W_c': self.engine_settings.W_c,
        }

    def recommend(self, learner, collection, sequence):
        """
        Workflow:
            get valid activities (i.e. activities in collection)
            retrieve parameters (relevant to valid activities where applicable)
            compute scores for valid activities using parameters
            return top item by computed recommendation score
        :param learner: Learner model instance
        :param collection: Collection model instance
        :param sequence: list of activity dicts, learner's sequence history
        :return: Activity model instance
        """
        # determine valid activities that recommendation can output
        # recommendation activity scores will only be computed for valid activities
        valid_activities = collection.activity_set.all()

        # get relevant model parameters (limited to valid activities where applicable)
        params = self.get_recommend_params(learner, valid_activities)

        # compute recommendation scores for activities
        scores = recommendation_score(
            params['guess'],
            params['slip'],
            params['learner_mastery'],
            params['prereqs'],
            params['r_star'],
            params['L_star'],
            params['difficulty'],
            params['W_p'],
            params['W_r'],
            params['W_d'],
            params['W_c'],
            params['last_attempted_guess'],
            params['last_attempted_slip']
        )
        # get the index corresponding to the activity with the highest computed score
        activity_idx = np.argmax(scores)

        # convert matrix 0-idx to activity.pk / activity
        pks = list(valid_activities.values_list('pk', flat=True))
        return Activity.objects.get(pk=pks[activity_idx])
