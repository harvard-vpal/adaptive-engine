##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
import numpy as np
import pandas as pd

n_users=10
n_los=8
n_items=40

epsilon=1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=0 ##Relevance threshold used in the BKT optimization procedure
M=0 ##Information threshold user in the BKT optimization procedure
L_star=3 #Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered

r_star=0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.
V_r=5 ##Importance of readiness in recommending the next item
V_d=3 ##Importance of demand in recommending the next item
V_a=1 ##Importance of appropriate difficulty in recommending the next item
V_c=1 ##Importance of continuity in recommending the next item

##Values prior to estimating model:
slip_probability=0.15
guess_probability=0.1
trans_probability=0.1
prior_knowledge_probability=0.2


##Store mappings of ids and names for users, LOs, items. These will serve as look-up tables for the rows and columns of data matrices
users='u'+np.char.array(range(n_users))
los='l'+np.char.array(range(n_los))
items='p'+np.char.array(range(n_items))

#Let problems be divided into several modules of adaptivity. In each module, only the items from that scope are used.
##Proposed code: 
# -1 - is not among the adaptively served ones
# 0 - problem can be served in any module
# n=1,2,3,...  - problem can be served in the module n
scope=np.repeat(1, n_items)

##List which items should be used for training the BKT
useForTraining=np.repeat(True, n_items)
useForTraining=np.where(useForTraining)[0]


#users=pd.DataFrame({'id' : 'u'+np.char.array(range(n_users)),
# 'name' : 'user '+np.char.array(range(n_users))
#  })
#
#los=pd.DataFrame({'id' : 'l'+np.char.array(range(n_los)),
# 'name' : 'LO '+np.char.array(range(n_los))
#  })
#
#items=pd.DataFrame({'id' : 'p'+np.char.array(range(n_items)),
# 'name' : 'problem '+np.char.array(range(n_items))
#  })

#Initial mastery of all LOs (a row of the initial mastery matrix)
#Logarithmic if additive formulation.

L_i=np.repeat(prior_knowledge_probability/(1.0-prior_knowledge_probability),n_los)

    
# Define the matrix of initial mastery by replicating the same row for each user
m_L_i=np.tile(L_i,(n_users,1))

##Define fake pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
m_w=np.random.rand(n_los,n_los);

for i in range(m_w.shape[0]):
  for j in range(m_w.shape[1]):
    des=(np.random.rand()>0.5)
    if des:
      m_w[i,j]=0.
    else:
      m_w[j,i]=0.


##


##Define the vector of difficulties that will be visible to users, between 0 and 1 (but we'll check and normalize)####
difficulty=np.repeat(1.,n_items)

##


##Define the preliminary relevance matrix: problems tagged with LOs. rownames are problems. Assumed that the entries are 0 or 1 ####

los_per_item=2 ##Number of los per problem

temp=np.append(np.repeat(1.0,los_per_item),np.repeat(0.0,n_los-los_per_item))

m_tagging=np.zeros([n_items,n_los])

for i in range(n_items) :
  m_tagging[i,]=np.random.choice(temp,size=len(temp),replace=False)

  
  ##CHeck that ther eare no zero rows or columns in tagging
  
ind=np.where(~m_tagging.any(axis=0))[0]

if(len(ind)>0):
  # print("LOs without a problem: ",los.id[ind])
  print("LOs without a problem: ",los[ind])
else:
  print("LOs without a problem: none\n")

  
  
ind=np.where(~m_tagging.any(axis=1))[0]

if(len(ind)>0):
  # print("Problem without an LO: ",items.id[ind])
  print("Problem without an LO: ",items[ind])
else:
  print("Problems without an LO: none\n")



##Define the matrix of transit odds ####
  
m_trans=(trans_probability/(1.0-trans_probability))*m_tagging
 ##
  
  ##Define the matrix of guess odds ####
m_guess=guess_probability/(1.0-guess_probability)*np.ones([n_items,n_los]);
m_guess[np.where(m_tagging==0.0)]=1.0

  ##
  
  ##Define the matrix of slip odds ####
m_slip=slip_probability/(1.0-slip_probability)*np.ones([n_items,n_los]);
m_slip[np.where(m_tagging==0.0)]=1.0
  ##

  
##Define the matrix which keeps track whether a LO for a user has ever been updated
#For convenience of adding users later, also define a row of each matrix
m_exposure=np.zeros([n_users,n_los])
row_exposure=m_exposure[0,]

#Define the matrix of confidence: essentially how much information we had for the mastery estimate
m_confidence=np.zeros([n_users,n_los])
row_confidence=m_confidence[0,]
  

##Define the matrix of "user has seen a problem or not": rownames are problems. ####
m_unseen=np.ones([n_users,n_items], dtype=bool)
row_unseen=m_unseen[0,]
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
transactions=pd.DataFrame()



##Define vector that will store the latest item seen by a user
last_seen=np.repeat(-1,n_users)




print("Initialization complete")