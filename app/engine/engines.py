import logging
import random
from django.http import Http404
from django.db.models import Model
import numpy as np
from alosi.engine import BaseAlosiAdaptiveEngine, recommendation_score, odds, EPSILON, \
    recommendation_score_P, recommendation_score_R, recommendation_score_D, recommendation_score_C, \
    calculate_relevance, calculate_mastery_update, fillna
from .data_structures import Matrix, Vector, pk_index_map, convert_pk_to_index
from .models import *


log = logging.getLogger(__name__)

GUESS_DEFAULT = odds(0.1)
SLIP_DEFAULT = odds(0.15)
TRANSIT_DEFAULT = odds(0.1)


def inverse_odds(x):
    return np.exp(x)/(1+np.exp(x))


def get_tagging_matrix(activities=None, knowledge_components=None):
    """
    Create Q x K matrix, where element is 1 if item q is tagged with KC k, else 0
    TODO could be revised - any way to utilize matrix/vector data structures?
    :param activities:
    :param knowledge_components:
    :return: QxK matrix if Q and K both > 1, or vector if either Q or K = 1 TODO
    """
    if activities is None:
        activities = Activity.objects.order_by('pk')
    # case: single model - replace idx args with querysets of len=1
    if isinstance(activities, Model):
        activities = Activity.objects.filter(pk=activities.pk)
    if isinstance(knowledge_components, Model):
        knowledge_components = KnowledgeComponent.objects.filter(pk=knowledge_components.pk)
    if knowledge_components is None:
        knowledge_components = KnowledgeComponent.objects.order_by('pk')
    pk_tuples = activities.values_list('pk', 'knowledge_components')
    idx = convert_pk_to_index(pk_tuples, [activities, knowledge_components])
    output_matrix = np.full((activities.count(), knowledge_components.count()), 0.0)
    # list(zip(*idx)) converts list of tuples to np-formatted array index
    output_matrix[list(zip(*idx))] = 1.0
    return output_matrix


def recommendation_score(relevance, learner_mastery, prereqs, r_star, L_star, difficulty, W_p, W_r, W_d, W_c,
                         last_attempted_guess=None, last_attempted_slip=None):
    """
    Modifys base recommendation_score method to convert np.nan's to 0's in subscores
    :param args:
    :param kwargs:
    :return:
    """
    P = recommendation_score_P(relevance, learner_mastery, prereqs, r_star, L_star)
    R = recommendation_score_R(guess, slip, learner_mastery, L_star)
    C = recommendation_score_C(guess, slip, last_attempted_guess, last_attempted_slip)
    D = recommendation_score_D(guess, slip, learner_mastery, difficulty)

    subscores = np.array([P, R, C, D])

    # for debugging
    subscore_labels = ['P', 'R', 'C', 'D']
    for subscore, label in zip(subscores, subscore_labels):
        log.debug('Subscore {}: {}'.format(label, subscore))

    # compute weighted average of subscores
    weights = np.array([W_p, W_r, W_d, W_c])
    scores = np.dot(weights, subscores)
    log.debug("Combined activity scores: {}".format(scores))
    return scores


def get_engine(engine_settings=None):
    """
    Get relevant engine for learner based on their experimental group
    :param engine_settings: EngineSettings model instance
    """
    if engine_settings is None:
        engine_settings = EngineSettings(
            L_star=0.9,
            r_star=0.0,
            W_r=2.0,  # demand
            W_c=1.0,  # continuity
            W_p=2.0,  # readiness
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


class AdaptiveEngine(BaseAlosiAdaptiveEngine):
    """
    Specific implementation of adaptive engine for django context
    """

    def __init__(self, engine_settings):
        self.engine_settings = engine_settings

    @staticmethod
    def get_tagging_parameter_values(model, activities=None, knowledge_components=None, default_value=0.1):
        """
        Base method for retrieving parameters associated with a activity-kc relationship
        e.g. guess, slip, transit
        :param model: Model, django model representing parameter (either Guess, Slip, Transit)
        :param activities: queryset of Activity model instances (convert model to qset before using this method)
        :param knowledge_components: queryset of KnowledgeComponent model instances
        :param default_value: float, default value to use for parameter if value missing
        :return: np.ndarray of size [len(activities) x len(knowledge_components)]
        """
        # default to entire set of objects if queryset not specified
        if activities is None:
            activities = Activity.objects.order_by('pk')
        if knowledge_components is None:
            knowledge_components = KnowledgeComponent.objects.order_by('pk')

        # retrieve parameter values
        output = Matrix(model)[activities, knowledge_components].values()

        # tagging matrix is the same size as the output (activity x kcs)
        # where element = 1 if activity-kc relation exists, else 0
        tagging_matrix = get_tagging_matrix(activities, knowledge_components)

        # for activity-kc relationships with no parameter provided, replace with default value
        output[np.where(tagging_matrix == 1)] = default_value

        return output

    def get_guess(self, activities=None, knowledge_components=None):
        """
        Get guess matrix, or row(s) of guess matrix if activity specified
        :param activities: Activity model instance or queryset
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: np.ndarray of size [len(activities) x len(knowledge_components)]
        """
        return self.get_tagging_parameter_values(Guess, activities, knowledge_components, default_value=GUESS_DEFAULT)

    def get_slip(self, activities=None, knowledge_components=None):
        """
        Get slip matrix, or row(s) of slip matrix if activity specified
        :param activities: Activity model instance or queryset
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: np.ndarray of size [len(activities) x len(knowledge_components)]
        """
        return self.get_tagging_parameter_values(Slip, activities, knowledge_components, default_value=SLIP_DEFAULT)

    def get_transit(self, activities=None, knowledge_components=None):
        """
        Get transit matrix, or row(s) of transit matrix if activity specified
        :param activities: Activity model instance or queryset
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: np.ndarray of size [len(activities) x len(knowledge_components)]
        """
        return self.get_tagging_parameter_values(Transit, activities, knowledge_components, default_value=TRANSIT_DEFAULT)

    @staticmethod
    def get_difficulty(activities=None):
        """
        Get activity difficulty values
        If activities not specified, defaults to getting difficulty for all existing Activity instances
        :param activities: Activity queryset
        :return: np.array of size [len(activity) x 0]
        """
        if activities is not None:
            output = activities.values_list('difficulty', flat=True)
        else:
            output = Activity.objects.values_list('difficulty', flat=True)
        # convert None's to np.nan
        output = np.array([x if x is not None else np.nan for x in output])
        return output

    @staticmethod
    def get_prereqs(knowledge_components):
        """
        Get Prerequisite matrix
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: (# LOs) x (# LOs) np.array matrix
        """
        return Matrix(PrerequisiteRelation)[knowledge_components, knowledge_components].values()

    @staticmethod
    def get_last_attempted_guess(learner, knowledge_components):
        """
        :param learner: Learner object instance
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: 1 x (# LOs) np.array vector
        """
        user_scores = Score.objects.filter(learner=learner)
        if user_scores:
            last_attempted_activity = user_scores.latest('timestamp').activity
            return Matrix(Guess)[last_attempted_activity, knowledge_components].values()
        else:
            return None

    @staticmethod
    def get_last_attempted_slip(learner, knowledge_components):
        """
        :param learner: Learner object instance
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: 1 x (# LOs) np.array vector
        """
        user_scores = Score.objects.filter(learner=learner)
        if user_scores:
            last_attempted_activity = user_scores.latest('timestamp').activity
            return Matrix(Slip)[last_attempted_activity, knowledge_components].values()
        else:
            return None

    @staticmethod
    def get_learner_mastery(learner, knowledge_components=None):
        """
        Constructs a 1 x (# LOs) vector of mastery odds values for learner
        Optionally, subset and order can be defined using knowledge_components argument
        If mastery value for a KC does not exist, populates the corresponding array element with the prior mastery
        value of the KC
        output vector represents mastery values of KCs in knowledge_components arg; defines the vector "axis"
        :param learner: Learner model instance
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: 1 x (# LOs) np.array vector
        """
        matrix = Matrix(Mastery)[learner, knowledge_components]
        # fill unpopulated values with appropriate kc prior values, from mastery_prior field on KC object
        matrix_values = fill_nan_from_index_field(matrix, 'mastery_prior')
        # convert to odds
        return odds(matrix_values)

    @staticmethod
    def get_mastery_prior(knowledge_components=None):
        """
        Get mastery prior values for learning objectives
        :param knowledge_components: KnowledgeComponent model instance or queryset
        :return: 1 x (#LOs) np.array vector
        """
        knowledge_components = KnowledgeComponent.objects.all()
        return np.array([kc.mastery_prior for kc in knowledge_components])

    @staticmethod
    def get_scores():
        """
        The values in the second column of the output matrix should be the row index (0-indexed) of the activity's position
        in the full Guess/Slip/Transit matrices
        :return: ?x3 np.array of score records with columns (learner, activity, score)
        """
        score_records = Score.objects.values_list('learner_id', 'activity_id', 'score')

        # convert activity pk to 0-indexed id, taking into account possible non-consecutive pks
        activity_pk_to_idx_map = pk_index_map(Activity.objects.order_by('pk'))  # map from pk to 0-index
        for i, row in enumerate(score_records):
            score_records[i][1] = activity_pk_to_idx_map[row[1]]

        return np.asarray(score_records)

    def update_from_score(self, learner, activity, score):
        """
        Action to take when new score information is received
        Doesn't add anything new to base class method, except new
        Also expects different input types for some args; see docstring
        TODO verify correctness of implementation
        :param learner: Learner object instance
        :param activity: Activity object instance
        :param score: float
        :return:
        """
        # subset to relevant knowledge components from activity
        knowledge_components = activity.knowledge_components.all().order_by('pk')
        # ensure that there are knowledge components for the activity, otherwise mastery update is not relevant
        if not knowledge_components.exists():
            log.debug("Skipping engine update from score; no tagged knowledge components found for activity.")
            return
        mastery = self.get_learner_mastery(learner, knowledge_components)

        # convert activity into queryset with single element
        activity_qset = Activity.objects.filter(pk=activity.pk)

        # flatten from ndarray to vector before passing to calculation methods
        guess = self.get_guess(activity_qset, knowledge_components).flatten()
        slip = self.get_slip(activity_qset, knowledge_components).flatten()
        transit = self.get_transit(activity_qset, knowledge_components).flatten()

        new_mastery = calculate_mastery_update(mastery, score, guess, slip, transit, EPSILON)
        # save new mastery values in mastery data store
        self.update_learner_mastery(learner, new_mastery, knowledge_components)
        # save the new score in score data store
        self.save_score(learner, activity, score)

    @staticmethod
    def save_score(learner, activity, score):
        """
        :param learner: Learner model instance
        :param activity: Activity model instance
        :param score: float, score value
        """
        Score.objects.create(learner=learner, activity=activity, score=score)

    @staticmethod
    def update_learner_mastery(learner, new_mastery, knowledge_components=None):
        """
        Saves updated mastery values in database
        Converts odds to normal probability
        :param learner: learner model instance
        :param new_mastery: 1 x (# LOs) np.array vector of new odds mastery values
        :param knowledge_components: KnowledgeComponent queryset - KC's to update values for
        """
        Matrix(Mastery)[learner, knowledge_components].update(inverse_odds(new_mastery))

    @staticmethod
    def initialize_learner(learner):
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

    def get_recommend_params(self, learner, valid_activities, valid_kcs):
        """
        Retrieve features/params needed for doing recommendation
        Calls data/param retrieval functions that may be implementation(prod vs. prototype)-specific
        Does shared calculations before passing derived features to subscore calculators
        TODO: consider QuerySet.select_related() for optimization https://docs.djangoproject.com/en/2.0/ref/models/querysets/#select-related
        :param learner: Learner model instance
        :param valid_activities: Queryset of Activity objects
        :param valid_kcs: Queryset of KnowledgeComponent objects
        :return: dictionary with following keys:
            guess: QxK np.array, guess parameter values for activities
            slip: QxK np.array, slip parameter values for activities
            difficulty: 1xQ np.array, difficulty values for activities
            prereqs: KxK np.array, prerequisite matrix
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
        # retrieve or calculate features
        guess = self.get_guess(valid_activities, valid_kcs)
        slip = self.get_slip(valid_activities, valid_kcs)
        relevance = calculate_relevance(guess, slip)
        last_attempted_relevance = calculate_relevance(
            self.get_last_attempted_guess(learner, valid_kcs),
            self.get_last_attempted_slip(learner, valid_kcs)
        )
        learner_mastery_odds = odds(get_learner_mastery(learner, valid_kcs))

        # fill missing values with 0.0
        fillna(relevance)
        fillna(last_attempted_relevance)
        fillna(learner_mastery_odds)

        # construct param dict
        return {
            'relevance': relevance,
            'difficulty': self.get_difficulty(valid_activities),
            'prereqs': self.get_prereqs(valid_kcs),
            'last_attempted_relevance': last_attempted_relevance,
            'learner_mastery_odds': learner_mastery_odds,
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
        :param sequence: list of activity objects, learner's sequence history
        :return: Activity model instance
        """
        # Determine valid activities that recommendation can output

        # recommendation activity scores will only be computed for valid activities
        valid_activities = collection.activity_set.all().order_by('pk')
        # exclude activities already completed
        learner_scores = Score.objects.filter(learner=learner)
        valid_activities = valid_activities.exclude(score__in=learner_scores)
        # Can also exclude based on activities in provided sequence
        # somewhat redundant but this addresses non-problem activities that don't have associated grades
        # TODO would need to adjust this if we want to support activity repetition
        valid_activities = valid_activities.exclude(pk__in=[activity.pk for activity in sequence])
        # remove activities whose prerequisites are not satisfied yet (this should be the last filter)
        valid_activities = valid_activities.exclude(prerequisite_activities__in=valid_activities)

        # KC set associated with the remaining valid activities
        valid_kcs = get_kcs_in_activity_set(valid_activities).order_by('pk')

        # skip score calculation for base cases
        if not valid_activities.exists():
            log.debug("No valid activities left: {}".format(collection))
            return None
        if len(valid_activities) == 1:
            return valid_activities.first()
        if not valid_kcs.exists():
            log.warning("No knowledge components detected for collection activities; returning random activity")
            return random.choice(valid_activities)

        # get relevant model parameters
        params = self.get_recommend_params(learner, valid_activities, valid_kcs)

        # compute recommendation scores for activities
        scores = recommendation_score(
            params['relevance'],
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


def get_kcs_in_activity_set(activities):
    """
    Given a queryset of activities, return the unique queryset of KCs activities are tagged with
    :return: Queryset of KnowledgeComponents
    """
    valid_pks = (activities
                 .filter(knowledge_components__isnull=False)
                 .values_list('knowledge_components', flat=True)
                 )
    return KnowledgeComponent.objects.filter(pk__in=valid_pks)


def fill_nan_from_index_field(data, field, axis=None):
    """
    Gets values from data_structures.Matrix or data_structures.Vector,
    with missing (np.nan) values replaced by field values from index
    :param data: data_structures.Matrix or data_structures.Vector
    :param field: name of the column model field that should be used for default values
    :param axis: if matrix, specifies which axis should be used (0 = row index, 1 = col index). Not necessary for Vector
    :return: np.array
    """
    if isinstance(data, Matrix):
        if not axis:
            raise ValueError('Axis must be specified for Matrix objects')
        fill_values = data.axes[axis].index.values_list(field, flat=True)
    elif isinstance(data, Vector):
        fill_values = data.axis.index.values_list(field, flat=True)
        axis = 0
    else:
        raise ValueError('data input arg not a recognized object type')
    values = data.values()
    nan_idxs = np.where(np.isnan(values))  # indices in matrix that are np.nan's
    values[nan_idxs] = np.take(fill_values, nan_idxs[axis])  # fill in values by column
    return values
