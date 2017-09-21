import numpy as np
from data_structures import Matrix, Vector
from models import * 
import utils

from django.dispatch import receiver
from django.db.models.signals import post_save


def get_engine_for_learner(learner):
    """
    Get relevant engine for learner
    """
    return Engine(utils.get_engine_settings_for_learner(learner))


class Engine(object):
    def __init__(self, engine_settings):
        """
        self.engine_instance gives access to engine-specific params:
            epsilon
            eta
            M
            r_star
            L_star
            W_r
            W_c
            W_d
            W_p
            stop_on_mastery
            prior_knowledge_probability
        """
        if isinstance(engine_settings,EngineSettings):
            self.settings = engine_settings
        else:
            raise ValueError
        
        #### convenience values ####
        self.prior_knowledge_probability = self.settings.prior_knowledge_probability



        self.guess_initial = utils.odds(self.settings.guess_probability)
        self.trans_initial = utils.odds(self.settings.trans_probability)
        self.slip_initial = utils.odds(self.settings.trans_probability)



    #### utils ####

    def initialize_learner(self, learner):
        """
        Arguments:
            learner_id (int): pk of new learner model instance

        This method is called right after a new learner is created in db
        Creates placeholder values in data matrices
            - populates learner's Mastery values using current KC priors
        This method is under the Engine class in case engine instance attributes 
        are needed for setting initial values in the future
        """
        print "Triggered initialize learner for learner = {}".format(learner.pk)
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

    def bayes_update(self, score):
        """
        Arguments:
            learner (Learner django model instance)
            activity (Activity django model instance)
            score (Score django model instance)

        What persistent values are updated?
            - row of L/Mastery
            - row of Confidence

        Note: use of {last_seen, m_unseen, transactions} replaced by Score database table
        Note: saving score to database is handled outside this function

        """
        print "Bayes update method triggered"

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
            relevance = -np.log(guess) - np.log(slip)
            confidence = Matrix(Confidence)[learner,] # vector
            confidence.update(confidence.values() + relevance) # update database values

        # row of mastery table for learner
        mastery = Matrix(Mastery)[learner,]
        # The increment of odds due to evidence of the problem, but before the transfer
        x = utils.x0_mult(guess,slip) * np.power(utils.x1_0_mult(guess,slip), score_value)
        L = mastery.values() * x
        # Add the transferred knowledge
        L += Matrix(Transit)[activity,].values()*(L+1)
        # Clean up invalid values
        L[np.where(np.isposinf(L))] = utils.inv_epsilon
        L[np.where(L==0.0)] = utils.epsilon

        # update row of mastery values in database
        mastery.update(L)


    def recommend(self, learner, collection=None):
        """
        This function returns the id of the next recommended problem in an adaptive module. 
        If none is recommended (list of problems exhausted or the user has reached mastery) it returns None.
        """
        valid_activities = utils.get_valid_activities(learner, collection)
        # check if we still have available problems
        if not valid_activities.exists():
            # return next_item = None if no items left to serve
            return None 

        # TODO: get rid of this example after implementation
        # next_item = valid_activities.first()

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

        P = np.dot(m_k_unseen, np.minimum((m_r+self.settings.r_star),0))
        R = np.dot(m_k_unseen, np.maximum((self.settings.L_star-L),0))

        if not Score.objects.filter(learner=learner).exists():
            C = np.repeat(0.0,N)
        else:
            last_seen = Score.objects.filter(learner=learner).latest('timestamp').activity
            relevance_lastseen = self.relevance(
                Matrix(Guess)[last_seen,].values(),
                Matrix(Slip)[last_seen,].values()
            )
            C = np.sqrt(np.dot(relevance_unseen, relevance_lastseen))

        # vector of difficulties for valid activities
        difficulty = self.difficulty(valid_activities)
        d_temp = np.tile(difficulty,(N,1)).T # repeated column vector
        L_temp = np.tile(L,(N,1)).T # repeated column vector
        D =- np.diag(np.dot(m_k_unseen,np.abs(L_temp-d_temp)))
                
        next_item = valid_activities[np.argmax(
            self.settings.W_p * P 
            + self.settings.W_r * R
            + self.settings.W_d * D
            + self.settings.W_c * C
        )]          
        
        return next_item


    def updateModel(self):
        """
        Notes:
            Updates initial mastery
        """
        try:
            est=utils.estimate(self, self.eta, self.M)

            self.L_i=1.0*est['L_i']
            self.m_L_i=np.tile(self.L_i,(self.m_L.shape[0],1))
            
            ind_pristine=np.where(self.m_exposure==0.0)
            self.m_L[ind_pristine]=self.m_L_i[ind_pristine]
            m_trans=1.0*est['trans']
            m_guess=1.0*est['guess']
            m_slip=1.0*est['slip']

            # calculate_derived_data(self)
        except:
            pass
