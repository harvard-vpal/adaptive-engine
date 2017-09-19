from .models import EngineSettings
import numpy as np

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

odds = lambda p: p/(1.0-p)

def get_engine_settings_for_learner(learner):
    """
    Given learner, get the right engine instance for them (for A/B testing)
    """
    return EngineSettings.objects.first()


def calculate_derived_data(self):


    ## Calculate the useful matrices of guess and slip probabilities and of negative logs of the odds.
    self.m_guess_neg_log= -np.log(self.m_guess)
    self.m_p_guess= self.m_guess/(self.m_guess+1.0)

    self.m_slip_neg_log= -np.log(self.m_slip)
    self.m_p_slip= self.m_slip/(self.m_slip+1.0)

    #m_trans_log = np.log(m_trans)
    #m_g_trans = m_trans_log-m_trans

    ##Define the matrix of mixed odds:

    #m_x0_add= np.log(m_slip*(1.0+m_guess)/(1.0+m_slip)) ##Additive formulation

    #Multiplicative formulation
    self.m_x0_mult= self.m_slip*(1.0+self.m_guess)/(1.0+self.m_slip)
    #m_x1_mult=(1.0+m_guess)/(m_guess*(1.0+m_slip))
    self.m_x1_0_mult=((1.0+self.m_guess)/(self.m_guess*(1.0+self.m_slip)))/self.m_x0_mult


    #m_x1_0_mult= (1.0+m_guess)/(m_guess*(1.0+m_slip))-m_x0_mult


    ##Define the matrix of relevance m_k
    self.m_k= -np.log(self.m_guess)-np.log(self.m_slip)


    ##Normalize and prepare difficulty vector:

    #if(difficulty.max()!=difficulty.min()):
    #    difficulty=(difficulty-difficulty.min())/(difficulty.max()-difficulty.min())

    # cleaning
    self.difficulty=np.minimum(np.maximum(self.difficulty,self.epsilon),1-self.epsilon)

    self.difficulty_mult=self.difficulty/(1.0-self.difficulty)
    self.difficulty_add=np.log(self.difficulty_mult)

    ##Define a matrix of problem difficulties clones for all LOs (used in recommendation)
    #m_difficulty_mult=np.tile(difficulty_mult,(n_los,1))
    n_los = len(self.los)
    self.m_difficulty=np.tile(self.difficulty_add,(n_los,1))



def knowledge(self, problems,correctness):
    """
    ##This function finds the empirical knowledge of a single user given a 
    chronologically ordered sequence of items submitted.
    """
    # global m_slip_neg_log, m_guess_neg_log, n_los
    n_los = len(self.los)

    m_slip_u=self.m_slip_neg_log[problems,]
    m_guess_u=self.m_guess_neg_log[problems,]
    N=len(problems)
    
    
    #### In case there is only one problem, need to make sure the result of subsetting is a 1-row matrix, not a 1D array. Later, for dot product to work out.
    m_slip_u=m_slip_u.reshape(N,n_los)
    m_guess_u=m_guess_u.reshape(N,n_los)
    ####
    
    z=np.zeros((N+1,n_los))
    x=np.repeat(0.0,N)
    z[0,]=np.dot((1.0-correctness),m_slip_u)
    z[N,]=np.dot(correctness,m_guess_u)
    
    if N>1:
        
        for n in range(1,N):
            x[range(n)]=correctness[range(n)]
            x[range(n,N)]=1.0-correctness[range(n,N)]
            temp=np.vstack((m_guess_u[range(n),],m_slip_u[n:,]))
            z[n,]=np.dot(x, temp)
    
    knowl=np.zeros((N,n_los))
    
    for j in range(n_los):
        
        ind=np.where(z[:,j]==min(z[:,j]))[0]
        
        for i in ind:
            
            temp=np.repeat(0.0,N)
            if (i==0):
                temp=np.repeat(1.0,N)
            elif (i<N):
                temp[i:N]=1.0
             
            knowl[:,j]=knowl[:,j]+temp
        
        knowl[:,j]=knowl[:,j]/len(ind) ##We average the knowledge when there are multiple candidates (length(ind)>1)
        
    return(knowl)

#This function estimates the BKT model using empirical probabilities
##To account for the fact that NaN and Inf elements of the estimated matrices should not be used as updates, this function replaces such elements with the corresponding elements of the current BKT parameter matrices.
##Thus, the outputs of this function do not contain any non-numeric values and should be used to simply replace the current BKT parameter matrices.
def estimate(self, relevance_threshold=0.01,information_threshold=20, remove_degeneracy=True):
    
    
    # global n_items,n_los, m_k, transactions, L_i, m_trans, m_guess, m_slip, self.epsilon, useForTraining, n_users
    n_items = len(self.items)
    n_los = len(self.los)
    n_users = len(self.users)

    trans=np.zeros((n_items,n_los))
    trans_denom=trans.copy()
    guess=trans.copy()
    guess_denom=trans.copy()
    slip=trans.copy()
    slip_denom=trans.copy()
    p_i=np.repeat(0.,n_los)
    p_i_denom=p_i.copy()
    
    #if ~('training_set' in globals()):
    training_set=range(n_users)

    
    for u in training_set:
        
        ##List problems that the user tried, in chronological order
        
#        n_of_na=np.count_nonzero(np.isnan(m_timestamp[u,]))
#        problems=m_timestamp[u,].argsort() ##It is important here that argsort() puts NaNs at the end, so we remove them from there
#        if n_of_na>0:        
#            problems=problems[:-n_of_na] ##These are indices of items submitted by user u, in chronological order.
#            
#        problems=np.intersect1d(problems, useForTraining)
        
        
        temp=self.transactions.loc[(self.transactions.user_id==u)&(self.transactions.problem_id.isin(self.useForTraining))]
        temp=temp.sort_values('time')
        temp.index=range(np.shape(temp)[0])
        ## Now temp is the data frame of submits of a particular user u, arranged in chronological order. In particular, temp.problem_id is the list of problems in chronological order.
        
        J=np.shape(temp)[0]
        if(J>0):
            m_k_u=self.m_k[temp.problem_id,]
            ##Reshape for the case J=1, we still want m_k_u to be a 2D array, not 1D.
            m_k_u=m_k_u.reshape(J,n_los)
            
            #Calculate the sum of relevances of user's experience for a each learning objective
            if(J==1):
                u_R=m_k_u[0]
            else:
                u_R=np.sum(m_k_u,axis=0)
                          
            ##Implement the relevance threshold: zero-out what is not above it, set the rest to 1
            #u_R=u_R*(u_R>relevance_threshold)
            #u_R[u_R>0]=1 
            u_R=(u_R>relevance_threshold) 
            #m_k_u=m_k_u*(m_k_u>relevance_threshold)
            #m_k_u[m_k_u>0]=1
            m_k_u=(m_k_u>relevance_threshold)
            
            #u_correctness=m_correctness[u,problems]
            #u_knowledge=knowledge(problems, u_correctness)
            u_knowledge=knowledge(self, temp.problem_id, temp.score)
            #Now prepare the matrix by replicating the correctness column for each LO.
            #u_correctness=np.tile(u_correctness,(n_los,1)).transpose()          


            ##Contribute to the averaged initial knowledge.
            p_i+=u_knowledge[0,]*u_R
            p_i_denom+=u_R
                        
            
            ##Contribute to the trans, guess and slip probabilities (numerators and denominators separately).
            for pr in range(J):
                prob_id=temp.problem_id[pr]
                
                shorthand=m_k_u[pr,]*(1.0-u_knowledge[pr,])
                
                guess[prob_id,]+=shorthand*temp.score[pr]
                guess_denom[prob_id,]+=shorthand
                                
                shorthand=m_k_u[pr,]-shorthand   ##equals m_k_u*u_knowledge
                slip[prob_id,]+=shorthand*(1.0-temp.score[pr])
                slip_denom[prob_id,]+=shorthand
                
                if pr<(J-1):
                    shorthand=m_k_u[pr,]*(1.0-u_knowledge[pr,])
                    trans[prob_id,]+=shorthand*u_knowledge[pr+1,]
                    trans_denom[prob_id,]+=shorthand
        
    
    ##Normalize the results over users.
    ind=np.where(p_i_denom!=0)
    p_i[ind]/=p_i_denom[ind]
    ind=np.where(trans_denom!=0)
    trans[ind]/=trans_denom[ind]
    ind=np.where(guess_denom!=0)
    guess[ind]/=guess_denom[ind]
    ind=np.where(slip_denom!=0)
    slip[ind]/=slip_denom[ind]
    
    
    ##Replace with nans where denominators are below information cutoff
    p_i[(p_i_denom<information_threshold)|(p_i_denom==0)]=np.nan
    trans[(trans_denom<information_threshold)|(trans_denom==0)]=np.nan
    guess[(guess_denom<information_threshold)|(guess_denom==0)]=np.nan
    slip[(slip_denom<information_threshold)|(slip_denom==0)]=np.nan
    
    ##Remove guess and slip probabilities of 0.5 and above (degeneracy):
    if remove_degeneracy:
        # these two lines will throw warnings for comparisons to np.nan's
        ind_g=np.where((guess>=0.5) | (guess+slip>=1))
        ind_s=np.where((slip>=0.5) | (guess+slip>=1))
                
        guess[ind_g]=np.nan
        slip[ind_s]=np.nan


    #Convert to odds (logarithmic in case of p.i):
    p_i=np.minimum(np.maximum(p_i,self.epsilon),1.0-self.epsilon)
    trans=np.minimum(np.maximum(trans,self.epsilon),1.0-self.epsilon)
    guess=np.minimum(np.maximum(guess,self.epsilon),1.0-self.epsilon)
    slip=np.minimum(np.maximum(slip,self.epsilon),1.0-self.epsilon)
    
    #L=np.log(p_i/(1-p_i))
    L=p_i/(1.0-p_i)
    trans=trans/(1.0-trans)
    guess=guess/(1.0-guess)
    slip=slip/(1.0-slip)
    
    ##Keep the versions with NAs in them:
    L_i_nan=L.copy()
    trans_nan=trans.copy()
    guess_nan=guess.copy()
    slip_nan=slip.copy()
    
    
    ind=np.where(np.isnan(L) | np.isinf(L))
    L[ind]=self.L_i[ind]
    ind=np.where(np.isnan(trans) | np.isinf(trans))
    trans[ind]=self.m_trans[ind]
    ind=np.where(np.isnan(guess) | np.isinf(guess))
    guess[ind]=self.m_guess[ind]
    ind=np.where(np.isnan(slip) | np.isinf(slip))
    slip[ind]=self.m_slip[ind]
        
        
    return {
        'L_i':L, 
        'trans':trans,
        'guess':guess, 
        'slip':slip, 
        'L_i_nan':L_i_nan, 
        'trans_nan':trans_nan,
        'guess_nan':guess_nan, 
        'slip_nan':slip_nan
    }
