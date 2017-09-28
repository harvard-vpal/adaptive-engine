from .models import *
from .data_structures import Matrix, Vector
import numpy as np


epsilon = 1e-10 # a regularization cutoff, the smallest value of a mastery probability


def pick_experimental_group():
    """
    Randomly pick an experimental group
    Currently weights all groups equally
    """
    return np.random.choice(ExperimentalGroup.objects.all())


def is_adaptive(learner):
    return bool(learner.experimental_group.engine_settings)


def get_activities(learner, collection=None, seen=False):
    """
    Arguments:
        learner (Learner)
        collection (Collection)
        seen (bool): True to return seen activities, 
            False to return unseen activities
    """
    activities = Activity.objects.distinct()
    learner_scores = Score.objects.filter(learner=learner)
    # get activities that haven't been seen before
    if seen == False:
        activities = activities.exclude(score__in=learner_scores)
    # alternatively, get activities that have been seen before
    else:
        activities = activities.filter(score__in=learner_scores)

    if collection:
        activities = activities.filter(collection=collection)

        # filtering based on adaptive/non-adaptive problems
        if is_adaptive(learner):
            activities.filter(include_adaptive=True)
        else:
            activities.filter(nonadaptive_order__isnull=False)

    return activities


def get_engine_settings_for_learner(learner):
    """
    Given learner, get the right engine instance for them (for A/B testing)
    """
    return EngineSettings.objects.get(pk=1)


def x0_mult(guess, slip):
    """
    Compute x0_mult element-wise
    Arguments:
        guess (np.array)
        slip (np.array)
    """
    return slip*(1.0+guess)/(1.0+slip)


def x1_0_mult(guess, slip):
    """
    Compute x1_0 element-wise
    Arguments:
        guess (np.array)
        slip (np.array)
    """
    return ((1.0+guess)/(guess*(1.0+slip)))/x0_mult(guess,slip)


def relevance(guess, slip):
    """
    Compute relevance element-wise (also known as m_k)
    Arguemnts:
        guess (np.array)
        slip (np.array)
    """
    return -np.log(guess)-np.log(slip)


def odds(p, clean=True):
    if clean:
        p = np.minimum(np.maximum(p,epsilon),1-epsilon)
    return p/(1.0-p)
    #np.minimum(np.maximum(slip,epsilon),1.0-epsilon)


def log_odds(p, clean=True):
    """
    Return log odds
    If 'clean'=True, replaces 0 and 1 in input with epsilon
    """
    return np.log(odds(p, clean=clean))

def replace_nan(A,B,inplace=True):
    """
    Replaces all NaN (or Inf) elements of A with the corresponding 
    elements of matrix B
    Arguments:
        A (ndarray): matrix with NaN values that should be replaced
        B (ndarray): matrix whose values will be used to fill in NaN
        spots in A
    """
    ind = np.where(np.isnan(A) | np.isinf(A))
    if not inplace:
        A = A.copy()
    A[ind] = B[ind]
    return A if not inplace else None


def difficulty(activities=None):
    """
    Return a vector of cleaned, normalized difficulties 
    from raw difficulty values (stored between 0 and 1)
    Corresponds to m_difficulty, without tileing
    """
    if not activities:
        activities = Activity.objects.filter(include_adaptive=True)
    difficulty_raw = activities.values_list('difficulty',flat=True)
    return log_odds(difficulty_raw, clean=True)


def knowledge(scores):
    """
    ##This function finds the empirical knowledge of a single user given a 
    chronologically ordered sequence of items submitted.

    Notes:
    - used in estimate: u_knowledge=knowledge(self, temp.problem_id, temp.score)
    """

    # get map of activity objects to matrix index
    activity_map = {a:i for i,a in enumerate(Activity.objects.all())}
    activity_idxs = [activity_map[s.activity] for s in scores]

    m_guess_u = -np.log(Matrix(Guess).values())[activity_idxs,]
    m_slip_u = -np.log(Matrix(Slip).values())[activity_idxs,]

    n_los = KnowledgeComponent.objects.count()

    N = scores.count()

    correctness = np.array([s.score for s in scores])
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
        
    return knowl


def estimate(relevance_threshold=0.01,information_threshold=20, remove_degeneracy=True):
    """
    This function estimates the BKT model using empirical probabilities
    To account for the fact that NaN and Inf elements of the estimated 
    matrices should not be used as updates, this function replaces such 
    elements with the corresponding elements of the current BKT parameter 
    matrices.
    Thus, the outputs of this function do not contain any non-numeric 
    values and should be used to simply replace the current BKT parameter 
    matrices.
    """   
    n_items = Activity.objects.count()
    n_los = KnowledgeComponent.objects.count()
    learners = Learner.objects.all()
    n_users = learners.count()

    trans=np.zeros((n_items,n_los))
    trans_denom=trans.copy()
    guess=trans.copy()
    guess_denom=trans.copy()
    slip=trans.copy()
    slip_denom=trans.copy()
    p_i=np.repeat(0.,n_los)
    p_i_denom=p_i.copy()

    # full QxK relevance matrix
    m_k = relevance(Matrix(Guess).values(),Matrix(Slip).values())

    # last filter might be redundant
    scores = Score.objects.order_by('timestamp').filter(activity__include_adaptive=True)
    activities = Activity.objects.all()

    # get map of activity objects to matrix index
    # key = activity object, value = index corresponding to position in data matrix
    activity_map = {a:i for i,a in enumerate(activities)}

    # for u in training_set:
    for learner in learners:

        ## user_scores is a queryset of scores for a particular user u, arranged in chronological order. 
        user_scores = Score.objects.filter(learner=learner).order_by('timestamp')
        ## score_values is a list of problems in chronological order.
        score_values = np.array([s.score for s in user_scores])

        # Number of items submitted by the learner
        J = user_scores.count()
        if J > 0:

            # get column of activity matrix index values
            activity_idxs = [activity_map[s.activity] for s in user_scores]
            m_k_u = m_k[activity_idxs,]
            
            #Calculate the sum of relevances of user's experience for a each learning objective
            u_R=np.sum(m_k_u,axis=0)
                          
            ##Implement the relevance threshold: zero-out what is not above it, set the rest to 1
            u_R=(u_R>relevance_threshold) 
            m_k_u=(m_k_u>relevance_threshold)

            # calculate knowledge based on user scores
            u_knowledge = knowledge(user_scores)

            ## Now prepare the matrix by replicating the correctness column for each LO.

            # Contribute to the averaged initial knowledge.
            p_i+=u_knowledge[0,]*u_R
            p_i_denom+=u_R
                        
            ##Contribute to the trans, guess and slip probabilities 
            ## (numerators and denominators separately).

            # j is index within user_problems, score is score object
            for j, score in enumerate(user_scores):
                # q is matrix index for activity associated with score
                q = activity_idxs[j]
                activity = score.activity

                shorthand=m_k_u[j,]*(1.0-u_knowledge[j,])
                
                guess[q,]+=shorthand*user_scores[j].score
                guess_denom[q,]+=shorthand
                                
                shorthand=m_k_u[j,]-shorthand   ##equals m_k_u*u_knowledge
                slip[q,]+=shorthand*(1.0-user_scores[j].score)
                slip_denom[q,]+=shorthand
                
                if j<(J-1):
                    shorthand=m_k_u[j,]*(1.0-u_knowledge[j,])
                    trans[q,]+=shorthand*u_knowledge[j+1,]
                    trans_denom[q,]+=shorthand

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

    #Convert to odds:
    L = odds(p_i)
    trans = odds(trans)
    guess = odds(guess)
    slip = odds(slip)
    
    ##Keep the versions with NAs in them:
    L_i_nan=L.copy()
    trans_nan=trans.copy()
    guess_nan=guess.copy()
    slip_nan=slip.copy()

    # get exisisting matrices
    knowledge_components = KnowledgeComponent.objects.all()
    L_i = np.array([kc.mastery_prior for kc in knowledge_components])
    m_trans = Matrix(Transit).values()
    m_guess = Matrix(Guess).values()
    m_slip = Matrix(Slip).values()

    # replace invalid values
    replace_nan(L, L_i, inplace=True)
    replace_nan(trans, m_trans, inplace=True)
    replace_nan(guess, m_guess, inplace=True)
    replace_nan(slip, m_slip, inplace=True)
        
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

