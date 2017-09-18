##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

#Should L be mastery odds(for multiplicative) or logarithmic odds (for additive formulation)?

from multiplicativeFormulation import MultiplicativeFormulation
import numpy as np

n_users=10
n_los=8
n_items=40
n_modules=2

# initialize users, los, items
##Store mappings of ids and names for users, LOs, items. These will serve as look-up tables for the rows and columns of data matrices
users='u'+np.char.array(range(n_users))
los='l'+np.char.array(range(n_los))
items='p'+np.char.array(range(n_items))

engine = MultiplicativeFormulation(
    users = users, 
    los=los, 
    items=items,
    n_modules=n_modules,

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
)

# initialize random user response data
T=2000
user_ids=np.random.choice(users,T)
score=np.random.choice([0,1],T)

for t in range(T):
    
    u=engine.mapUser(user_ids[t])
    rec_item=engine.recommend(u)
    
    if rec_item!=None:
        engine.bayesUpdate(u,rec_item,score[t],t)
        
print "updating model"        
engine.updateModel()
        
