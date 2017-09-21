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
        self.epsilon = self.settings.epsilon
        self.prior_knowledge_probability = self.settings.prior_knowledge_probability

        self.inv_epsilon = 1.0/self.epsilon
        self.log_epsilon = -np.log(self.epsilon)

        self.guess_initial = utils.odds(self.settings.guess_probability)
        self.trans_initial = utils.odds(self.settings.trans_probability)
        self.slip_initial = utils.odds(self.settings.trans_probability)

    #### convenience computations that involve arguments ####

    def guess_neg_log(self, guess):
        return -np.log(guess)

    def p_guess(self, guess):
        return guess/(guess+1.0)

    def slip_neg_log(slip):
        return -np.log(slip)

    def p_slip(slip):
        """
        May consider just a prob transformation function
        """
        return slip/(slip+1.0)

    def x0_mult(self, guess, slip):
        """
        Compute x0_mult element
        Assume slip and guess are single values, and run this element-wise
        original formula: # self.m_x0_mult= self.m_slip*(1.0+self.m_guess)/(1.0+self.m_slip)
        """
        return slip*(1.0+guess)/(1.0+slip)

    def x1_0_mult(self, guess, slip):
        """
        Compute x1_0 element
        """
        return ((1.0+guess)/(guess*(1.0+slip)))/self.x0_mult(guess,slip)


    def relevance(self, guess, slip):
        """
        relevance matrix, also known as m_k
        """
        return -np.log(guess)-np.log(slip)

    def clean_difficulty(self, difficulty):
        """
        Ensure there are no 1.0 or 0.0 in difficulty values
        """
        return np.minimum(np.maximum(difficulty,self.epsilon),1-self.epsilon)

    def normalize_difficulty(self, difficulty):
        """
        normalize difficulty value(s)
        """
        difficulty_mult = self.difficulty/(1.0-self.difficulty)
        return np.log(self.difficulty_mult)

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
        Doesnt save score to database
        """


        print "Bayes update method triggered"

        activity = score.activity
        learner = score.learner
        score_value = score.score


        # vector of values, corresponding to row of guess and slip matrices for single activity
        guess = Matrix(Guess)[activity,].values() # nparray [1 x # KCs]
        slip = Matrix(Slip)[activity,].values() # nparray vector [1 x # KCs]
        
        # Updating last_seen is replaced with updating Score database table outside of this function

        ## If this is the first time learner sees/does the problem...
        ## e.g. is there a score object for the activity in the learner's transaction history apart from this one
        ## Replaces use of LastSeen

        if not Score.objects.filter(learner=learner,activity=activity).exists():

            # increment exposure values for learner to the particular learning objective(s)
            # could this be moved to model update function?
            # self.m_exposure[u,]+=self.m_tagging[item,]
            # Exposure.objects.filter(
            #     learner=learner, 
            #     knowledge_component__in=activity.knowledge_component_set.values('pk')
            # ).update(value=F('value')+1)

            # update row of confidence matrix
            relevance = -np.log(guess) - np.log(slip)
            confidence = Matrix(Confidence)[learner,] # vector
            confidence.update(confidence.values() + relevance) # update database values

        # save score to database outside this function

        # row of mastery table for learner
        mastery = Matrix(Mastery)[learner,] # Vector [1 x # KCs]

        # The increment of odds due to evidence of the problem, but before the transfer
        x = self.x0_mult(guess,slip) * np.power(self.x1_0_mult(guess,slip), score_value) #vector-wise multiply
        L = mastery.values() * x  # L is an nparray vector
        # Add the transferred knowledge
        L += Matrix(Transfer)[activity,].values()*(L+1)

        # cleaning invalid mastery values
        L[np.where(np.isposinf(L))] = self.inv_epsilon
        L[np.where(L==0.0)] = self.epsilon

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
        next_item = valid_activities.first()

        # row of mastery values matrix
        L = np.log(Matrix(Mastery)[learner,].values())

        # check if we still have available problems
        if valid_activities.count() == 0:
            return None
        # R=np.dot(m_k_unseen, np.maximum((self.L_star-L),0))


        #Calculate the user readiness for LOs
        m_w = Matrix(PrerequisiteRelation).values()
        m_r = np.dot(np.minimum(L-self.settings.L_star,0), m_w)

        guess = Matrix(Guess)[valid_activities,].values()
        slip = Matrix(Slip)[valid_activities,].values()
        # m_k is matrix of relevance (derived from guess/slip)
        m_k_unseen = self.relevance(guess,slip)


        # P=np.dot(m_k_unseen, np.minimum((m_r+self.r_star),0))
        # R=np.dot(m_k_unseen, np.maximum((self.L_star-L),0))


        #### progress placeholder ####
        

        #     P=np.dot(m_k_unseen, np.minimum((m_r+self.r_star),0))
        #     R=np.dot(m_k_unseen, np.maximum((self.L_star-L),0))
            
        #     if self.last_seen[u]<0:
        #         C=np.repeat(0.0,N)
        #     else:
        #         C=np.sqrt(np.dot(m_k_unseen, self.m_k[self.last_seen[u],]))
                
        #     #A=0.0
        #     d_temp=self.m_difficulty[:,ind_unseen]
        #     L_temp=np.tile(L,(N,1)).transpose()
        #     D=-np.diag(np.dot(m_k_unseen,np.abs(L_temp-d_temp)))
            
        #     #if stopOnMastery and sum(D)==0: ##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
        #     next_item=None
        #     #else:
                
        #     if normalize:
        #         temp=(D.max()-D.min());
        #         if(temp!=0.0):
        #             D=D/temp     
        #         temp=(R.max()-R.min());
        #         if(temp!=0.0):
        #             R=R/temp
        #         temp=(P.max()-P.min());
        #         if(temp!=0.0):
        #             P=P/temp
        #         temp=(C.max()-C.min());
        #         if(temp!=0.0):
        #             C=C/temp     
                
        #     next_item=ind_unseen[np.argmax(self.W_p*P+self.W_r*R+self.W_d*D+self.W_c*C)]          
        
        return next_item


    # def updateModel(self):
    #     """
    #     Notes:
    #         Updates initial mastery
    #     """
    #     try:
    #         est=utils.estimate(self, self.eta, self.M)

    #         self.L_i=1.0*est['L_i']
    #         self.m_L_i=np.tile(self.L_i,(self.m_L.shape[0],1))
            
    #         ind_pristine=np.where(self.m_exposure==0.0)
    #         self.m_L[ind_pristine]=self.m_L_i[ind_pristine]
    #         m_trans=1.0*est['trans']
    #         m_guess=1.0*est['guess']
    #         m_slip=1.0*est['slip']

    #         # calculate_derived_data(self)
    #     except:
    #         pass
