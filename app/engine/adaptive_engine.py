
import numpy as np
from data_structures import Matrix, Vector
from models import * 

#### adaptive engine parameter settings ####
# ENGINE_PARAMS = dict(
#     epsilon=1e-10, # a regularization cutoff, the smallest value of a mastery probability
#     eta=0.0, ##Relevance threshold used in the BKT optimization procedure
#     M=0.0, ##Information threshold user in the BKT optimization procedure
#     L_star=2.2, #Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered

#     r_star=0.0, #Threshold for forgiving lower odds of mastering pre-requisite LOs.
#     W_p=5.0, ##Importance of readiness in recommending the next item
#     W_r=3.0, ##Importance of demand in recommending the next item
#     W_d=1.0, ##Importance of appropriate difficulty in recommending the next item
#     W_c=1.0, ##Importance of continuity in recommending the next item

#     ##Values prior to estimating model:
#     slip_probability=0.15,
#     guess_probability=0.1,
#     trans_probability=0.1,
#     prior_knowledge_probability=0.2,
# )


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
        self.engine_settings = engine_settings
        
        #### convenience values ####
        self.epsilon = self.engine_settings.epsilon
        self.prior_knowledge_probability = self.engine_settings.prior_knowledge_probability

        self.inv_epsilon = 1.0/self.epsilon
        self.log_epsilon = -np.log(self.epsilon)


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
        return slip*(1.0+m_guess)/(1.0+slip)

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

    def new_learner(self, learner_pk):
        """
        Arguments:
            learner_pk (int): pk of new learner model instance

        call this function when a new learner is created
        creates placeholder values in data matrices
        """
        # add mastery row
        v = self.prior_knowledge_probability/(1.0-self.prior_knowledge_probability)
        Mastery.objects.bulk_create([
            Mastery(
                learner=learner_pk, 
                knowledge_component=kc, 
                value=v
            ) for kc in KnowledgeComponent.objects.values_list('pk',flat=True)
        ])

    # TODO: how about updates when a new knowledge component is added?


    #### engine functionality ####

    def bayes_update(self, learner, activity, score):
        """
        Arguments:
            learner (Learner django model instance)
            activity (Activity django model instance)
            score (Score django model instance)

        What persistent values are updated?
            - row of L/Mastery
            - row of Confidence
        """
        # vector of values, corresponding to row of guess and slip matrices for single activity
        guess = Matrix(Guess)[activity,].values() # nparray [1 x # KCs]
        slip = Matrix(Slip)[activity,].values() # nparray vector [1 x # KCs]
        # mastery row for learner (queryset)
        mastery = Matrix(Mastery)[learner,] # nparray vector [1 x # KCs]

        # update last_seen entry to reflect that learner has just seen activity (TODO consider if this is needed)
        LastSeen.objects.get(learner=learner).update(value=activity.pk)

        ## if this is the first time learner sees/does the problem
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
            confidence = Matrix(Confidence)['learner',] # vector
            confidence.update(confidence.values() + relevance) # update database values

        # Record the transaction by appending a new row to the data frame "transactions":
        Score.create(learner=learner, activity=activity, score=score)

        # The increment of odds due to evidence of the problem, but before the transfer
        x = x0_mult(guess,slip) * np.power(self.x1_0_mult(guess,slip), score) #vector-wise multiply
        L = mastery.values() * x  # L is an nparray vector
        # Add the transferred knowledge
        L += Matrix(Transfer)[item,].values()*(L+1)

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

        # TODO: get rid of this example
        next_item = Activity.objects.first()

        # actual functionality

        
        # determined unseen activities within scope
        # User.objects.distinct().filter(widget__in=your_widget_queryset)
        # valid_activities = (Activity.objects.distinct()
        #     .exclude(score__in=Score.objects.filter(learner=learner))
        # )
        # if collection:
        #     valid_activities = valid_activities.filter(collections__in=[collection])

        # L = np.log(Matrix(Mastery)[learner,].values())


        # if self.stopOnMastery:

        #     guess = Matrix(Guess)[learner,].filter(activity__in=valid_activities).values()
        #     slip = Matrix(Slip)[learner,].filter(activity__in=valid_activities).values()

        #     k_unseen = self.relevance(guess,slip)
        #     R = np.dot(k_unseen, np.maximum(self.L_star-L,0))
        #     valid_activity_ids = valid_activities.values_list('pk')[R!=0]
        #     valid_activities = valid_activities.filter(activity__in=valid_activity_ids)

        # # check if we still have available problems
        # if valid_activities.count() == 0:
        #     return None # return next_item = None if no items left to serve

        # #Calculate the user readiness for LOs
        # r = np.dot(np.minimum(L-self.L_star,0), Matrix(PrerequisiteRelation).values())
        # k_unseen = self.relevance(guess,slip)


        #### progress placeholder ####
        

        #     #L=np.log(m_L[u,])
            
        #     #Calculate the user readiness for LOs
            
        #     m_r=np.dot(np.minimum(L-self.L_star,0), self.m_w);
        #     m_k_unseen=self.m_k[ind_unseen,]
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
