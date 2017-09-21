from .models import *
from .data_structures import Matrix, Vector
import numpy as np

odds = lambda p: p/(1.0-p)

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
