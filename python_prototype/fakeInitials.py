##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
import numpy as np
import pandas as pd

def initialize_variables(self, 

    
    users=None,
    los=None,
    items=None,
    # n_users=10, 
    # n_los=8, 
    # n_items=40, 
    n_modules=2,

    epsilon=1e-10, # a regularization cutoff, the smallest value of a mastery probability
    eta=0.0, ##Relevance threshold used in the BKT optimization procedure
    M=0.0, ##Information threshold user in the BKT optimization procedure
    L_star=2.2, #Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered

    r_star=0.0, #Threshold for forgiving lower odds of mastering pre-requisite LOs.
    W_p=5.0, ##Importance of readiness in recommending the next item
    W_r=3.0, ##Importance of demand in recommending the next item
    W_d=1.0, ##Importance of appropriate difficulty in recommending the next item
    W_c=1.0, ##Importance of continuity in recommending the next item

    ##Values prior to estimating model:
    slip_probability=0.15,
    guess_probability=0.1,
    trans_probability=0.1,
    prior_knowledge_probability=0.2,

    los_per_item=2, ##Number of los per problem
    ):

    # self.n_users=10
    # self.n_los=8
    # self.n_items=40
    # self.n_modules=2

    # self.epsilon=1e-10 # a regularization cutoff, the smallest value of a mastery probability
    # self.eta=0.0 ##Relevance threshold used in the BKT optimization procedure
    # self.M=0.0 ##Information threshold user in the BKT optimization procedure
    # self.L_star=2.2 #Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered

    # self.r_star=0.0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.
    # self.W_p=5.0 ##Importance of readiness in recommending the next item
    # self.W_r=3.0 ##Importance of demand in recommending the next item
    # self.W_d=1.0 ##Importance of appropriate difficulty in recommending the next item
    # self.W_c=1.0 ##Importance of continuity in recommending the next item

    # ##Values prior to estimating model:
    # self.slip_probability=0.15
    # self.guess_probability=0.1
    # self.trans_probability=0.1
    # self.prior_knowledge_probability=0.2

    self.epsilon=epsilon # a regularization cutoff, the smallest value of a mastery probability
    self.eta=eta ##Relevance threshold used in the BKT optimization procedure
    self.M=M ##Information threshold user in the BKT optimization procedure
    self.L_star=L_star #Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered

    self.r_star=r_star #Threshold for forgiving lower odds of mastering pre-requisite LOs.
    self.W_p=W_p ##Importance of readiness in recommending the next item
    self.W_r=W_r ##Importance of demand in recommending the next item
    self.W_d=W_d ##Importance of appropriate difficulty in recommending the next item
    self.W_c=W_c ##Importance of continuity in recommending the next item
  

    # ##Store mappings of ids and names for users, LOs, items. These will serve as look-up tables for the rows and columns of data matrices
    self.users=users
    self.los=los
    self.items=items

    n_users = len(users)
    n_los = len(los)
    n_items = len(items)

    #Let problems be divided into several modules of adaptivity. In each module, only the items from that scope are used.
    self.scope=np.ones([n_items,n_modules],dtype=bool)
    self.scope[:,1]=False

    ##List which items should be used for training the BKT
    self.useForTraining=np.repeat(True, n_items)
    self.useForTraining=np.where(self.useForTraining)[0]


    #Initial mastery of all LOs (a row of the initial mastery matrix)
    #Logarithmic if additive formulation.

    self.L_i=np.repeat(prior_knowledge_probability/(1.0-prior_knowledge_probability),n_los)

        
    # Define the matrix of initial mastery by replicating the same row for each user
    self.m_L_i=np.tile(self.L_i,(n_users,1))

    # Define a copy to update
    self.m_L=self.m_L_i.copy()

    ##Define fake pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
    self.m_w=np.random.rand(n_los,n_los)

    for i in range(self.m_w.shape[0]):
      for j in range(self.m_w.shape[1]):
        des=(np.random.rand()>0.5)
        if des:
          self.m_w[i,j]=0.
        else:
          self.m_w[j,i]=0.



    ##Define the vector of difficulties that will be visible to users, between 0 and 1 (but we'll check and normalize)####
    self.difficulty=np.repeat(1.,n_items)

    ##


    ##Define the preliminary relevance matrix: problems tagged with LOs. rownames are problems. Assumed that the entries are 0 or 1 ####

    # los_per_item=2 ##Number of los per problem

    temp=np.append(np.repeat(1.0,los_per_item),np.repeat(0.0,n_los-los_per_item))

    self.m_tagging=np.zeros([n_items,n_los])

    for i in range(n_items) :
        self.m_tagging[i,]=np.random.choice(temp,size=len(temp),replace=False)

      
      ##CHeck that ther eare no zero rows or columns in tagging
      
    ind=np.where(~self.m_tagging.any(axis=0))[0]

    if(len(ind)>0):
        # print("LOs without a problem: ",los.id[ind])
        print("LOs without a problem: ",los[ind])
    else:
        print("LOs without a problem: none\n")

      
      
    ind=np.where(~self.m_tagging.any(axis=1))[0]

    if(len(ind)>0):
      # print("Problem without an LO: ",items.id[ind])
      print("Problem without an LO: ",items[ind])
    else:
      print("Problems without an LO: none\n")



    ##Define the matrix of transit odds ####
      
    self.m_trans=(trans_probability/(1.0-trans_probability))*self.m_tagging
     ##
      
      ##Define the matrix of guess odds ####
    self.m_guess=guess_probability/(1.0-guess_probability)*np.ones([n_items,n_los]);
    self.m_guess[np.where(self.m_tagging==0.0)]=1.0

      ##
      
      ##Define the matrix of slip odds ####
    self.m_slip=slip_probability/(1.0-slip_probability)*np.ones([n_items,n_los]);
    self.m_slip[np.where(self.m_tagging==0.0)]=1.0
      ##

      
    ##Define the matrix which keeps track whether a LO for a user has ever been updated
    #For convenience of adding users later, also define a row of each matrix
    self.m_exposure=np.zeros([n_users,n_los])
    self.row_exposure=self.m_exposure[0,]

    #Define the matrix of confidence: essentially how much information we had for the mastery estimate
    self.m_confidence=np.zeros([n_users,n_los])
    self.row_confidence=self.m_confidence[0,]
      

    ##Define the matrix of "user has seen a problem or not": rownames are problems. ####
    self.m_unseen=np.ones([n_users,n_items], dtype=bool)
    self.row_unseen=self.m_unseen[0,]
    ##
    ###Define the matrix of results of user interactions with problems.####
    #m_correctness=np.empty([n_users,n_items])
    #m_correctness[:]=np.nan
    #row_correctness=m_correctness[0,]
    #
    ###Define the matrix of time stamps of results of user interactions with problems.####
    #m_timestamp=np.empty([n_users,n_items])
    #m_timestamp[:]=np.nan
    #row_timestamp=m_timestamp[0,]

    #Initialize the data frame which will store the results of users submit-transactions (much like problem_check in Glenn's data)
    self.transactions=pd.DataFrame()



    ##Define vector that will store the latest item seen by a user
    self.last_seen=np.repeat(-1,n_users)

