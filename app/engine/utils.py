from .models import *
from .data_structures import Matrix, Vector
import numpy as np

epsilon = 1e-10
inv_epsilon = 1.0/epsilon
log_epsilon = -np.log(epsilon)

def get_valid_activities(learner, collection=None):
    """
    Arguments:
        learner: Learner object
        collection: Collection object
    Get set of valid activities to do recommendation on
    Returns a queryset
    """
    # determine unseen activities within scope
    valid_activities = (Activity.objects.distinct()
        .exclude(score__in=Score.objects.filter(learner=learner))
    )
    # restrict to activities for the given collection
    if collection:
        valid_activities = valid_activities.filter(collection=collection)

    return valid_activities
 

def get_engine_settings_for_learner(learner):
    """
    Given learner, get the right engine instance for them (for A/B testing)
    """
    return EngineSettings.objects.get(pk=1)

#### convenience computations that involve arguments ####


# def guess_neg_log(self, guess):
#     return -np.log(guess)

# def p_guess(self, guess):
#     return guess/(guess+1.0)

# def slip_neg_log(slip):
#     return -np.log(slip)

# def p_slip(slip):

#     return slip/(slip+1.0)

def x0_mult(guess, slip):
    """
    Compute x0_mult element
    Assume slip and guess are single values, and run this element-wise
    original formula: # self.m_x0_mult= self.m_slip*(1.0+self.m_guess)/(1.0+self.m_slip)
    """
    return slip*(1.0+guess)/(1.0+slip)

def x1_0_mult(guess, slip):
    """
    Compute x1_0 element
    """
    return ((1.0+guess)/(guess*(1.0+slip)))/x0_mult(guess,slip)


def relevance(guess, slip):
    """
    relevance matrix, also known as m_k
    """
    return -np.log(guess)-np.log(slip)

# def clean_difficulty(self, difficulty):
#     """
#     Ensure there are no 1.0 or 0.0 in difficulty values
#     """
#     return np.minimum(np.maximum(difficulty,self.settings.epsilon),1-self.settings.epsilon)

# def normalize_difficulty(self, difficulty):
#     """
#     normalize difficulty value(s) - corresponds to "difficulty_add"
#     """
#     difficulty_mult = difficulty/(1.0-difficulty)
#     return np.log(difficulty_mult)

def odds(p):
    return p/(1.0-p)

def probability(odds):
    """
    convert to probability from odds
    """
    return odds/(odds+1.0)

inverse_odds = probability

def log_odds(p, clean=True):
    """
    Return log odds
    If 'clean'=True, replaces 0 and 1 in input with epsilon
    """
    if clean:
        p = np.minimum(np.maximum(p,epsilon),1-epsilon)
    return np.log(odds(p))

def difficulty(activities=None):
    """
    Return a vector of cleaned, normalized difficulties 
    from raw difficulty values (stored between 0 and 1)
    Corresponds to m_difficulty, without tileing
    """
    if not activities:
        activities = Activity.objects.all()
    difficulty_raw = activities.values_list('difficulty',flat=True)
    return log_odds(difficulty_raw, clean=True)
    
