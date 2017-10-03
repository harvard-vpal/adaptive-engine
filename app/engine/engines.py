import numpy as np
from .data_structures import Matrix, Vector
from .models import * 
from . import utils


def initialize_learner(learner, experimental_group_id=None):
    """
    Initializes learner by assigning an experimental group (can be specified manually)
    """
    if experimental_group_id:
        learner.experimental_group = ExperimentalGroup.objects.get(pk=experimental_group_id)
    else:
        learner.experimental_group = utils.pick_experimental_group()
    learner.save()
    engine = get_engine(learner)
    # engine-specific initialize learner method
    engine.initialize_learner(learner)


def get_engine(learner):
    """
    Get relevant engine for learner based on their experimental group
    Also assigns experimental group if none assigned
    """
    experimental_group = learner.experimental_group
    if not experimental_group:
        initialize_learner(learner)
    engine_settings = learner.experimental_group.engine_settings
    # engine settings will exist if experimental group is adaptive
    if engine_settings:
        return AdaptiveEngine(engine_settings)
    # otherwise they will have non-adaptive behavior
    else:
        return NonAdaptiveEngine()


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
        """
        pass

    def update(self, score):
        """
        No additional action needed
        """
        score.save()

    def recommend(self, learner, collection):
        """
        Recommend activity according to 'nonadaptive_order' field
        """
        utils.get_activities(learner, collection, seen=False).order_by('nonadaptive_order').first()


class AdaptiveEngine(object):
    """
    Adaptive engine class that does internal parameter updates (Mastery, 
    Guess, Slip, etc) and recommends activities according to adaptive 
    algorithm
    """
    def __init__(self, engine_settings):
        """
        Arguments:
            engine_settings (EngineSettings): EngineSettings model instance containing parameter settings
        """
        if isinstance(engine_settings,EngineSettings):
            self.settings = engine_settings
        else:
            raise ValueError
        

    def initialize_learner(self, learner):
        """
        Arguments:
            learner (Learner): new learner model instance
            experimental_group (ExperimentalGroup): optional experimental group to assign

        This method is called right after a new learner is created in db
        Creates placeholder values in data matrices
            - populates learner's Mastery values using current KC priors
        This method is under the Engine class in case engine instance attributes 
        are needed for setting initial values in the future
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
        # add confidence row
        Confidence.objects.bulk_create([
            Confidence(
                learner=learner,
                knowledge_component=kc,
                value=0,
            ) for kc in knowledge_components
        ])


    # TODO: how about updates when a new knowledge component is added?


    #### engine functionality ####

    def update(self, score):
        """
        Arguments:
            learner (Learner django model instance)
            activity (Activity django model instance)
            score (Score django model instance)

        Updates:
            - row of L/Mastery
            - row of Confidence

        Note: use of {last_seen, m_unseen, transactions} replaced by Score database table
        Note: saving score to database is handled outside this function
        """

        activity = score.activity
        learner = score.learner
        score_value = score.score
        
        # vector of values, corresponding to row of guess and slip matrices for single activity
        guess = Matrix(Guess)[activity,].values() # nparray [1 x # KCs]
        slip = Matrix(Slip)[activity,].values() # nparray vector [1 x # KCs]

        ## If this is the first time learner sees/does the problem...
        ## e.g. is there a score for the activity in the learner's transaction history
        if not Score.objects.filter(learner=learner,activity=activity).exists():
            # update row of confidence matrix
            relevance = utils.relevance(guess,slip)
            confidence = Matrix(Confidence)[learner,] # vector
            confidence.update(confidence.values() + relevance) # update database values

        # row of mastery table for learner
        mastery = Matrix(Mastery)[learner,]
        # The increment of odds due to evidence of the problem, but before the transfer
        x = utils.x0_mult(guess,slip) * np.power(utils.x1_0_mult(guess,slip), score_value)
        L = mastery.values() * x
        # Add the transferred knowledge
        L += Matrix(Transit)[activity,].values() * (L+1)
        # Clean up invalid values
        L[np.where(np.isposinf(L))] = 1.0/utils.epsilon
        L[np.where(L==0.0)] = utils.epsilon

        # update row of mastery values in database
        mastery.update(L)

        # save score to database
        score.save()


    def recommend(self, learner, collection):
        """
        This function returns the id of the next recommended problem in an adaptive module. 
        If none is recommended (list of problems exhausted or the user has reached mastery) it returns None.
        """
        # enforce max problems limit for collection
        if collection.max_problems:
            if utils.get_activities(learner, collection, seen=True).count() > collection.max_problems:
                return None

        # get unseen activities within module that are valid to serve to adaptive group
        valid_activities = utils.get_activities(learner, collection, seen=False)

        # check if we still have available problems
        if not valid_activities.exists():
            # return next_item = None if no items left to serve
            return None 

        # check for preadaptive activities
        valid_preadaptive_activities = valid_activities.filter(preadaptive_order__isnull=False)
        if valid_preadaptive_activities.exists():
            return valid_preadaptive_activities.order_by('preadaptive_order').first()

        # row of mastery values matrix
        L = np.log(Matrix(Mastery)[learner,].values())

        # N is number of available problems
        N = valid_activities.count()

        # check if we still have available problems
        if N == 0:
            return None

        #Calculate the user readiness for LOs
        m_w = Matrix(PrerequisiteRelation).values()
        m_r = np.dot(np.minimum(L-self.settings.L_star,0), m_w)

        guess = Matrix(Guess)[valid_activities,].values()
        slip = Matrix(Slip)[valid_activities,].values()
        # m_k is matrix of relevance (derived from guess/slip)
        relevance_unseen = utils.relevance(guess,slip)

        P = np.dot(relevance_unseen, np.minimum((m_r+self.settings.r_star),0))
        R = np.dot(relevance_unseen, np.maximum((self.settings.L_star-L),0))

        if not Score.objects.filter(learner=learner).exists():
            C = np.repeat(0.0,N)
        else:
            last_seen = Score.objects.filter(learner=learner).latest('timestamp').activity
            relevance_lastseen = utils.relevance(
                Matrix(Guess)[last_seen,].values(),
                Matrix(Slip)[last_seen,].values()
            )
            C = np.sqrt(np.dot(relevance_unseen, relevance_lastseen))
        # vector of difficulties for valid activities
        difficulty = utils.difficulty(valid_activities)
        # number of learning objectives
        K = KnowledgeComponent.objects.count()
        d_temp = np.tile(difficulty,(K,1)) # repeated column vector
        L_temp = np.tile(L,(N,1)).T # repeated column vector
        D =- np.diag(np.dot(relevance_unseen,np.abs(L_temp-d_temp)))
                
        next_item = valid_activities[np.argmax(
            self.settings.W_p * P 
            + self.settings.W_r * R
            + self.settings.W_d * D
            + self.settings.W_c * C
        )]
        
        return next_item


def update_model(eta=0.0, M=20.0):
    """
    Updates initial mastery and tranit/guess/slip matrices

    Arguments:
        eta (float): Relevance threshold used in the BKT optimization procedure
        M (float): Information threshold user in the BKT optimization procedure
    """
    est = utils.estimate(eta, M)

    # save L_i
    L_i = Vector(KnowledgeComponent.objects.all(),value_field='mastery_prior')
    L_i.update(1.0*est['L_i'])
    
    # save param matrices
    Matrix(Transit).update(1.0*est['trans'])
    Matrix(Guess).update(1.0*est['guess'])
    Matrix(Slip).update(1.0*est['slip'])
