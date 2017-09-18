from .models import EngineSettings
# from .models import Mastery, Learner, KnowledgeComponent

# def new_learner(learner_pk, prior_knowledge_probability):
#     """
#     Arguments:
#         learner_pk (int): pk of new learner model instance

#     call this function when a new learner is created
#     creates placeholder values in data matrices
#     """
#     # add mastery row
#     L_i = prior_knowledge_probability/(1.0-prior_knowledge_probability)
#     Mastery.objects.bulk_create([
#         Mastery(
#             learner=learner_pk, 
#             knowledge_component=kc, 
#             value=value
#         ) for kc in KnowledgeComponent.objects.values_list('pk',flat=True)
#     ])

def get_engine_settings_for_learner(learner):
    """
    Given learner, get the right engine instance for them (for A/B testing)
    """
    return EngineSettings.objects.first()
