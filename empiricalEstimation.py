##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

######################################
####Estimation functions are below####
######################################
##This function finds the empirical knowledge of a single user given a chronologically ordered sequence of items submitted.
def knowledge(problems,correctness):
    
    global m_slip_neg_log, m_guess_neg_log, n_los
    m_slip_u=m_slip_neg_log[problems,]
    m_guess_u=m_guess_neg_log[problems,]
    N=len(problems)
    
    z=np.zeros((N+1,n_los))
    x=np.repeat(0.0,N)
    z[0,]=np.dot((1.0-correctness),m_slip_u)
    z[N,]=np.dot(correctness,m_guess_u)
    
    if(N>1):
        
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
def estimate(relevance_threshold=0,information_threshold=20, remove_degeneracy=True):
    
    
    global n_items,n_los, m_k, m_timestamp, m_correctness, L_i, m_trans, m_guess, m_slip, epsilon, useForTraining
    
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
        
        n_of_na=np.count_nonzero(np.isnan(m_timestamp[u,]))
        problems=m_timestamp[u,].argsort() ##It is important here that argsort() puts NaNs at the end, so we remove them from there
        if n_of_na>0:        
            problems=problems[:-n_of_na] ##These are indices of items submitted by user u, in chronological order.
            
        problems=np.intersect1d(problems, useForTraining)
        
        J=len(problems)
        if(J>0):
            m_k_u=m_k[problems,]
            
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
            
            u_correctness=m_correctness[u,problems]
            u_knowledge=knowledge(problems, u_correctness);
            #Now prepare the matrix by replicating the correctness column for each LO.
            u_correctness=np.tile(u_correctness,(n_los,1)).transpose()          


            ##Contribute to the averaged initial knowledge.
            p_i+=u_knowledge[0,]*u_R
            p_i_denom+=u_R
                        
            ##Contribute to the trans, guess and slip probabilities (numerators and denominators separately).
            temp=m_k_u*(1.0-u_knowledge)
            guess[problems,]+=temp*u_correctness
            guess_denom[problems,]+=temp
            
            temp=m_k_u-temp   ##equals m_k_u*u_knowledge
            slip[problems,]+=temp*(1.0-u_correctness)
            slip_denom[problems,]+=temp
  
            if(J>1):
                u_trans_denom=(1-u_knowledge[:-1,])
                trans[problems[:-1],]+=(m_k_u[:-1,]*u_trans_denom)*u_knowledge[1:,]
                trans_denom[problems[:-1],]+=m_k_u[:-1,]*u_trans_denom
        
        
    
    
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
    if(remove_degeneracy):
        guess[guess>=0.5]=np.nan
        slip[slip>=0.5]=np.nan

    #Convert to odds (logarithmic in case of p.i):
    p_i=np.minimum(np.maximum(p_i,epsilon),1.0-epsilon)
    trans=np.minimum(np.maximum(trans,epsilon),1.0-epsilon)
    guess=np.minimum(np.maximum(guess,epsilon),1.0-epsilon)
    slip=np.minimum(np.maximum(slip,epsilon),1.0-epsilon)
    
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
    
    
    ind=np.isnan(L) | np.isinf(L)
    L[ind]=L_i[ind]
    ind=np.isnan(trans) | np.isinf(trans)
    trans[ind]=m_trans[ind]
    ind=np.isnan(guess) | np.isinf(guess)
    guess[ind]=m_guess[ind]
    ind=np.isnan(slip) | np.isinf(slip)
    slip[ind]=m_slip[ind]
        
        
        
    return{'L_i':L, 'trans':trans,'guess':guess, 'slip':slip, 'L_i_nan':L_i_nan, 'trans_nan':trans_nan,'guess_nan':guess_nan, 'slip_nan':slip_nan}