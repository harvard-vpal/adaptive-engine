##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

##This function maps the user_id to the user index used by other functions, and also adds new users
def mapUser(user_id):
    
    global users
    
    try:
        u=np.where(users==user_id)[0][0]
    except:
        global n_users, last_seen, m_L, m_exposure, m_unseen, m_correctness, m_timestamp
        u=n_users
        n_users+=1
        users=np.append(users,user_id)
        last_seen=np.append(last_seen,-1)
        m_L=np.vstack((m_L,L_i))
        m_exposure=np.vstack((m_exposure,row_exposure))
        m_unseen=np.vstack((m_unseen,row_unseen))
        m_correctness=np.vstack((m_correctness,row_correctness))
        m_timestamp=np.vstack((m_timestamp,row_timestamp))
        
    
    return(u)


def mapItem(item_id):
    
    global items
    
    item=np.where(items==item_id)[0][0]
        
    return(item)

def bayesUpdate(u, item, score=1, time=0):
  
  
  #This function updates the user mastery and record of interactions that will be needed for recommendation and estimation of the BKT
  
  global m_x0_add, m_k, m_L, m_trans, last_seen, m_unseen, m_correctness, m_timestamp, m_exposure, m_tagging, log_epsilon
  
  
  last_seen[u]=item
  if m_unseen[u,item]:
      m_unseen[u,item]=False
      m_correctness[u,item]=score
      m_timestamp[u,item]=time
      m_exposure[u,]+=m_tagging[item,]
  
  ##The increment of log-odds due to evidence of the problem, but before the transfer
  x=m_x0_add[item,]+score*m_k[item,]
  L=m_L[u,]+x
  
  ##Add the transferred knowledge
  trans=m_trans[item,]
  #L=np.log(trans+(trans+1)*np.exp(L))
  L=np.log(trans+(trans+1)*np.exp(L))
  
  L[np.isposinf(L)]=log_epsilon
  L[np.isneginf(L)]=-log_epsilon
  
  m_L[u,]=L
  #return{'L':L, 'x':x}
  



#This function calculates the probability of correctness on a problem, as a prediction based on student's current mastery.
def predictCorrectness(u, item):
    
    global m_L, m_p_slip, m_p_guess
    
    L=m_L[u,]
    p_slip=m_p_slip[item,];
    p_guess=m_p_guess[item,];
    
    odds=np.exp(L);
  
    x=(odds*(1.0-p_slip)+p_guess)/(odds*p_slip+1.0-p_guess); ##Odds by LO
    x=np.prod(x) ##Total odds
  
    p=x/(1+x) ##Convert odds to probability
    if np.isnan(p) or np.isinf(p):
          p=1.0
  
    return(p)



##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns None.
def recommend(u, stopOnMastery=True):
    
    global m_L, L_star, m_w, m_unseen, m_k, r_star, last_seen, m_difficulty_add, V_r, V_d, V_a, V_c
            
    #Subset to the unseen problems and calculate problem readiness and demand
    ind_unseen=np.where(m_unseen[u,])[0]

    N=len(ind_unseen)
    
    if(N==0): ##This means we ran out of problems, so we stop
        next_item = None
        
    else:
        L=m_L[u,]
        
        #Calculate the user readiness for LOs
        
        m_r=np.dot(np.minimum(L-L_star,0), m_w);
        m_k_unseen=m_k[ind_unseen,]
        R=np.dot(m_k_unseen, np.minimum((m_r+r_star),0))
        D=np.dot(m_k_unseen, np.maximum((L_star-L),0))
        
        if last_seen[u]<0:
            C=np.repeat(0.0,N)
        else:
            C=np.dot(m_k_unseen, m_k[last_seen[u],])
            
        #A=0.0
        d_temp=m_difficulty_add[:,ind_unseen]
        L_temp=np.tile(L,(N,1)).transpose()
        A=-np.diag(np.dot(m_k_unseen,np.abs(L_temp-d_temp)))
        
        if stopOnMastery and sum(D)==0: ##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
            next_item=None
        else:
            temp=1.0/(A.max()-A.min());
            if(~np.isinf(temp)):
                A=A*temp
            
            temp=1.0/(D.max()-D.min());
            if(~np.isinf(temp)):
                D=D*temp
                            
            temp=1.0/(R.max()-R.min());
            if(~np.isinf(temp)):
                R=R*temp
            
            temp=1.0/(C.max()-C.min());
            if(~np.isinf(temp)):
                C=C*temp     
            
            next_item=ind_unseen[np.argmax(V_r*R+V_d*D+V_a*A+V_c*C)]
            
    
    return(next_item)
  

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
    
    
    global n_items,n_los, m_k, m_timestamp, m_correctness, L_i, m_trans, m_guess, m_slip, epsilon
    
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
        
        
    
    ##Zero-out denominators under the information cutoff
    p_i_denom*=(p_i_denom>information_threshold)
    trans_denom*=(trans_denom>information_threshold)
    guess_denom*=(guess_denom>information_threshold)
    slip_denom*=(slip_denom>information_threshold)
    
    ##Normalize the results over users.
    p_i/=p_i_denom
    trans/=trans_denom
    guess/=guess_denom
    slip/=slip_denom
    
    ##Remove guess and slip probabilities of 0.5 and above (degeneracy):
    if(remove_degeneracy):
        guess[guess>=0.5]=np.nan
        slip[slip>=0.5]=np.nan

    #Convert to odds (logarithmic in case of p.i):
    p_i=np.minimum(np.maximum(p_i,epsilon),1.0-epsilon)
    trans=np.minimum(np.maximum(trans,epsilon),1.0-epsilon)
    guess=np.minimum(np.maximum(guess,epsilon),1.0-epsilon)
    slip=np.minimum(np.maximum(slip,epsilon),1.0-epsilon)
    
    L=np.log(p_i/(1.0-p_i))
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
    

#This function updates the BKT model using the estimates from student data.
def updateModel():
    
    global eta, M, L_i, m_exposure, m_L, m_L_i, m_trans, m_guess, m_slip
    est=estimate(eta, M)

    L_i=1.0*est['L_i']
    m_L_i=np.tile(L_i,(m_L.shape[0],1))
    
    ind_pristine=np.where(m_exposure==0.0)
    m_L[ind_pristine]=m_L_i[ind_pristine]
    m_trans=1.0*est('trans')
    m_guess=1.0*est('guess')
    m_slip=1.0*est('slip')
