import numpy as np

# a regularization cutoff, the smallest value of a mastery probability
EPSILON = 1e-10


class BaseAdaptiveEngine:

    def __init__(self):
        pass

    def get_guess(self, activity_id=None):
        """
        Get guess parameters for activity/activities
        :param activity_id: activity id to get parameters for
            If None, returns full Guess matrix by default
        :return: (# activities) x (# LOs) np.array matrix of guess parameter values
            or 1 x (# LOs) np.array vector of guess parameter values if activity_id is specified
        """
        raise NotImplementedError

    def get_slip(self, activity_id=None):
        """
        Get slip parameters for activity/activities
        :param activity_id: activity id to get guess parameters for.
            If None, returns full Slip matrix by default
        :return: (# activities) x (# LOs) np.array matrix of slip parameter values
            or 1 x (# LOs) np.array vector of slip parameter values if activity_id is specified
        """
        raise NotImplementedError

    def get_transit(self, activity_id=None):
        """
        Get transit parameters for activity/activities
        :param activity_ids: activity id to get transit parameters for.
            If None, returns full Slip matrix by default
        :return: (# activities) x (# LOs) np.array matrix of transit parameter values
            or 1 x (# LOs) np.array vector of transit parameter values if activity_id is specified
        """
        raise NotImplementedError

    def get_difficulty(self, activity_id=None):
        """
        Get difficulty values for activity/activities
        :param activity_id: activity id to get guess parameters for
        :return: 1 x (# activities) np.array vector of transit parameter values
            or difficulty parameter value (float) if activity_id is specified
        """
        raise NotImplementedError

    def get_prereqs(self):
        """
        Get prerequisite weight values
        :return: (# LOs)x(# LOs) np.array matrix - full Prerequisite matrix
        """
        raise NotImplementedError

    def get_r_star(self, learner_id=None):
        """
        Get r_star parameter value (possibly learner-specific)
        :param learner_id: int, learner id
        :return: float, r_star parameter value
        """
        raise NotImplementedError

    def get_L_star(self, learner_id=None):
        """
        Get L_star parameter value (possibly learner-specific)
        :param learner_id: int, learner id
        :return: float, L_star parameter value
        """
        raise NotImplementedError

    def get_last_attempted_guess(self, learner_id):
        """
        Return guess parameter values for the activity last attempted by the specified learner
        :param learner_id: learner id
        :return: 1x(# LOs) np.array vector of guess parameter values
        """
        raise NotImplementedError

    def get_last_attempted_slip(self, learner_id):
        """
        Return slip parameter values for the activity last attempted by the specified learner
        :param learner_id: learner id
        :return: 1x(#LOs) np.array vector of slip parameter values
        """
        raise NotImplementedError

    def get_learner_mastery(self, learner_id):
        """
        Return mastery parameter values for learner
        :param learner_id:
        :return: 1x(# LOs) np.array vector of mastery parameter values
        """
        raise NotImplementedError

    def get_W_p(self):
        """
        Get value of W_p
        :param learner_id:
        :return: float
        """
        raise NotImplementedError

    def get_W_r(self, learner_id):
        """
        Get value of W_p
        :param learner_id:
        :return: float
        """
        raise NotImplementedError

    def get_W_d(self, learner_id):
        """
        Get value of W_d
        :param learner_id:
        :return: float
        """
        raise NotImplementedError

    def get_W_c(self, learner_id):
        """
        Get value of W_c
        :param learner_id:
        :return: float
        """
        raise NotImplementedError

    def get_scores(self):
        """
        Get table of score records
        :return: ?x3 np.array of score records with columns (learner_id, activity_id, score_value)
        """
        raise NotImplementedError

    def save_score(self, learner_id, activity_id, score):
        """
        Save score (e.g. to database, or to a matrix)
        :param learner_id: learner id
        :param activity_id: activity id
        :param score: float
        """
        raise NotImplementedError

    def update_learner_mastery(self, learner_id, new_mastery):
        """
        Save new mastery parameter values for learner, replacing old values
        :param learner_id: learner id to save parameter values for
        :param new_mastery: New parameter values to save
        """
        raise NotImplementedError

    def update_guess(self, new_guess):
        """
        Update entire guess parameter matrix
        :param new_guess:
        """
        raise NotImplementedError

    def update_slip(self, new_slip):
        """
        Update entire slip parameter matrix
        :param new_slip: (# activities) x (# LOs) np.array containing new values for slip parameters
        """
        raise NotImplementedError

    def update_transit(self, new_transit):
        """
        Update entire transit matrix
        :param new_transit: (# activities) x (# LOs) np.array containing new values for transit parameters
        """
        raise NotImplementedError

    def update_prior_mastery(self, new_prior_mastery):
        """
        Update prior mastery values for LOs
        :param new_prior_mastery: 1 x (# LOs) np.array vector of new mastery values for all LOs
        """

    def get_recommend_params(self, learner_id, scope=None):
        """
        Retrieve features/params needed for doing recommendation
        Calls data/param retrieval functions that may be implementation(prod vs. prototype)-specific
        TODO: could subset params based on activities in collection scope, to reduce unneeded computation
        :param learner_id:
        :return: dictionary with following keys:
            guess: QxK np.array, guess parameter values for activities
            slip: QxK np.array, slip parameter values for activities
            difficulty: 1xQ np.array, difficulty values for activities
            prereqs: QxQ np.array, prerequisite matrix
            r_star: float, Threshold for forgiving lower odds of mastering pre-requisite LOs.
            L_star: float, Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered
            W_p: (float), weight on substrategy P
            W_r: (float), weight on substrategy R
            W_d: (float), weight on substrategy D
            W_c: (float), weight on substrategy C
            last_attempted_guess: 1xK vector of guess parameters for activity
            last_attempted_slip: 1xK vector of slip parameters for activity
            learner_mastery: 1xK vector of learner mastery values
        """
        return {
            'guess': self.get_guess(),
            'slip': self.get_slip(),
            'difficulty': self.get_difficulty(),
            'prereqs': self.get_prereqs(),
            'r_star': self.get_r_star(learner_id),
            'L_star': self.get_L_star(learner_id),
            'W_p': self.get_W_p(learner_id),
            'W_r': self.get_W_r(learner_id),
            'W_d': self.get_W_d(learner_id),
            'W_c': self.get_W_c(learner_id),
            'last_attempted_guess': self.get_last_attempted_guess(learner_id),
            'last_attempted_slip': self.get_last_attempted_slip(learner_id),
            'learner_mastery': self.get_learner_mastery(learner_id),
        }

    def recommend(self, learner_id, collection=None):
        """
        Workflow:
            get valid activities
            subset parameter matrices by relevance to valid activities
            compute scores for activities using subsetted matrices
            return 1 (or n) top items
        """
        # get relevant model parameters
        params = self.get_recommend_params(learner_id)

        scores = recommendation_score(
            params['guess'],
            params['slip'],
            params['learner_mastery'],
            params['prereqs'],
            params['r_star'],
            params['L_star'],
            params['difficulty'],
            params['W_p'],
            params['W_r'],
            params['W_d'],
            params['W_c'],
            params['last_attempted_guess'],
            params['last_attempted_slip']
        )
        return np.argmax(scores)

    def update_from_score(self, learner_id, activity_id, score):
        """
        Action to take when new score information is received
        :param learner_id: learner id used as input to get_learner_mastery(), update_learner_mastery(), save_score()
        :param activity_id: activity id used as input to get_guess(), get_slip(), get_transit()
        :param score: float
        :return:
        """
        mastery = self.get_learner_mastery(learner_id)
        guess = self.get_guess(activity_id)
        slip = self.get_slip(activity_id)
        transit = self.get_transit(activity_id)
        new_mastery = calculate_mastery_update(mastery, score, guess, slip, transit, EPSILON)
        # save new mastery values in mastery data store
        self.update_learner_mastery(learner_id, new_mastery)
        # save the new score in score data store
        self.save_score(learner_id, activity_id, score)

    def train(self, relevance_threshold=0.01, information_threshold=20, remove_degeneracy=True):
        """
        Estimates the BKT model using empirical probabilities
        :param relevance_threshold: TODO
        :param information_threshold: TODO
        :param remove_degeneracy: TODO
        :return:
        """
        mastery_prior = self.get_mastery_prior()
        scores = self.get_scores()
        guess = self.get_guess()
        slip = self.get_slip()
        transit = self.get_transit()
        new_params = estimate(scores, guess, slip, transit, mastery_prior, relevance_threshold, information_threshold,
                              remove_degeneracy)
        # save param matrices
        self.update_transit(new_params['trans'])
        self.update_guess(new_params['guess'])
        self.update_slip(new_params['slip'])
        return new_params


def x0_mult(guess, slip):
    """
    Compute x0_mult element-wise
    :param guess: guess (np.array)
    :param slip: slip (np.array)
    :return: np.array
    """
    return slip*(1.0+guess)/(1.0+slip)


def x1_0_mult(guess, slip):
    """
    Compute x1_0 element-wise
    :param guess: (np.array)
    :param slip: (np.array)
    :return: np.array
    """
    return ((1.0+guess)/(guess*(1.0+slip)))/x0_mult(guess,slip)


def calculate_mastery_update(mastery, score, guess, slip, transit, epsilon):
    """
    Calculate bayesian update of learner mastery based on new score information
    :param mastery: 1xL np.array vector of current mastery parameters for learner
    :param score: float, score value for activity
    :param guess: 1xL np.array vector of guess parameters for activity
    :param slip: 1xL np.array vector of slip parameters for activity
    :param transit: 1xL np.array vector of transit parameters for activity
    :param epsilon: smallest value of mastery probability to allow
    :return: 1xL np.array vector of new masteries for learner
    """
    # The increment of odds due to evidence of the problem, but before the transfer
    x = x0_mult(guess, slip) * np.power(x1_0_mult(guess, slip), score)
    L = mastery * x
    # Add the transferred knowledge
    L += transit * (L + 1)
    # Clean up invalid values
    L[np.where(np.isposinf(L))] = 1.0 / epsilon
    L[np.where(L == 0.0)] = epsilon
    return L


def recommendation_score(guess, slip, learner_mastery, prereqs, r_star, L_star, difficulty, W_p, W_r, W_d, W_c,
                         last_attempted_guess=None, last_attempted_slip=None):
    """
    Computes recommendation scores for activities
    Scores are a weighted average of 4 different scoring substrategies:
        P: Readiness
        R: Remediation / demand
        D: Appropirate Difficulty
        C: Continuity
    :param guess: QxK matrix of item-KC guess parameters
    :param slip: QxK matrix of item-KC slip parameters
    :param learner_mastery: 1xK vector of learner mastery values
    :param prereqs:
    :param r_star: Threshold for forgiving lower odds of mastering pre-requisite LOs.
    :param L_star: Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered
    :param difficulty:
    :param W_p:
    :param W_r:
    :param W_d:
    :param W_c:
    :param last_attempted_guess:
    :param last_attempted_slip:
    :return:
    """
    P = recommendation_score_P(guess, slip, learner_mastery, prereqs, r_star, L_star)
    R = recommendation_score_R(guess, slip, learner_mastery, L_star)
    C = recommendation_score_C(guess, slip, last_attempted_guess, last_attempted_slip)
    D = recommendation_score_D(guess, slip, learner_mastery, difficulty)
    return (
        W_p * P
        + W_r * R
        + W_d * D
        + W_c * C
    )


def recommendation_score_P(guess, slip, learner_mastery, prereqs, r_star, L_star):
    """
    Compute scores according to Substrategy P
    :param slip:
    :param learner_mastery:
    :param prereqs:
    :param r_star:
    :param L_star:
    :return:
    """
    m_w = prereqs
    L = learner_mastery
    relevance = calculate_relevance(guess, slip)
    m_r = np.dot(np.minimum(L - L_star, 0), m_w)
    P = np.dot(relevance, np.minimum((m_r + r_star), 0))
    return P


def recommendation_score_R(guess, slip, learner_mastery, L_star):
    """
    Computes a recommendation score for each activity according to substrategy R
    :param guess: (# activities) x (# LOs) np.array of guess parameter values for activities
    :param slip: (# activities) x (# LOs) np.array of slip parameter values for activities
    :param learner_mastery:
    :param L_star:
    :return: 1 x (# activities) vector of recommendation score values
    """
    L = learner_mastery
    relevance = calculate_relevance(guess, slip)
    R = np.dot(relevance, np.maximum((L_star - L), 0))
    return R


def recommendation_score_C(guess, slip, last_attempted_guess=None, last_attempted_slip=None):
    """
    Compute scores according to Substrategy C
    :param guess: (# activities) x (# LOs) np.array of guess parameter values for activities
    :param slip: (# activities) x (# LOs) np.array of slip parameter values for activities
    :param last_attempted_guess: 1 x (# LOs) np.array vector of guess parameter values for last attempted activity
    :param last_attempted_slip: 1 x (# LOs) np.array vector of slip parameter values for last attempted activity
    :return: 1 x (# activities) vector of recommendation score values
    """
    # Q is number of activities
    Q = guess.shape[0]
    relevance = calculate_relevance(guess, slip)
    if last_attempted_guess is not None and last_attempted_slip is not None:
        C = np.repeat(0.0, Q)
    else:
        relevance_last_attempted = calculate_relevance(
            last_attempted_guess,
            last_attempted_slip
        )
        C = np.sqrt(np.dot(relevance, relevance_last_attempted))
    return C


def recommendation_score_D(guess, slip, learner_mastery, difficulty):
    """
    Substrategy D
    learner_mastery: vector of mastery values for learner (1xK)
    difficulty: vector of item difficulties (Qx1)
    :param guess:
    :param slip:
    :param learner_mastery:
    :param difficulty:
    :return: 1 x (# activities) vector of recommendation score values
    """
    # number of learning objectives
    Q = len(difficulty)
    K = len(learner_mastery)
    L = learner_mastery
    relevance = calculate_relevance(guess, slip)
    d_temp = np.tile(difficulty, (K, 1))  # repeated column vector
    L_temp = np.tile(L, (Q, 1)).T  # repeated column vector
    D = -np.diag(np.dot(relevance, np.abs(L_temp - d_temp)))
    return D


def calculate_relevance(guess, slip):
    """
    Compute relevance element-wise
    Arguments:
        guess (np.array)
        slip (np.array)
    """
    return -np.log(guess)-np.log(slip)


def odds(p, clean=True):
    if clean:
        p = np.minimum(np.maximum(p,EPSILON),1-EPSILON)
    return p/(1.0-p)


def replace_nan(A, B, inplace=True):
    """
    Replaces all NaN (or Inf) elements of A with the corresponding
    elements of matrix B
    :param A: (ndarray) matrix with NaN values that should be replaced
    :param B: (ndarray) matrix whose values will be used to fill in NaN
        spots in A
    :param inplace: whether to replace inplace or return a copy
    """
    ind = np.where(np.isnan(A) | np.isinf(A))
    if not inplace:
        A = A.copy()
    A[ind] = B[ind]
    return A if not inplace else None


def knowledge(scores, guess, slip):
    """
    ##This function finds the empirical knowledge of a single user given a
    chronologically ordered sequence of items submitted.
    Notes:
    - used in estimate: u_knowledge=knowledge(self, temp.problem_id, temp.score)
    :param scores: ?x3 np.array of score information for single learner
        col 1: learner (should be all same)
        col 2: activity
        col 3: score value
    :param guess: full guess param matrix
    :param slip: full slip param matrix
    """

    # list of matrix 0-based indices for activities associated with scores
    activity_idxs = scores[:, 1].astype(int)

    m_guess_u = -np.log(guess[activity_idxs, ])
    m_slip_u = -np.log(slip[activity_idxs, ])

    # number of knowledge components
    n_los = guess.shape[1]

    # number of scores
    N = scores.shape[0]

    # list of score values
    correctness = scores[:, 2]

    z = np.zeros((N+1, n_los))
    x = np.repeat(0.0, N)
    z[0, ] = np.dot((1.0 - correctness), m_slip_u)
    z[N, ] = np.dot(correctness, m_guess_u)

    if N > 1:
        for n in range(1, N):
            x[range(n)] = correctness[range(n)]
            x[range(n, N)] = 1.0 - correctness[range(n, N)]
            temp = np.vstack((m_guess_u[range(n), ], m_slip_u[n:, ]))
            z[n, ] = np.dot(x, temp)

    knowl = np.zeros((N, n_los))

    for j in range(n_los):
        ind = np.where(z[:, j] == min(z[:, j]))[0]
        for i in ind:
            temp = np.repeat(0.0, N)
            if i == 0:
                temp = np.repeat(1.0, N)
            elif i < N:
                temp[i:N] = 1.0
            knowl[:, j] = knowl[:, j] + temp
        # We average the knowledge when there are multiple candidates (length(ind)>1)
        knowl[:, j] = knowl[:, j] / len(ind)

    return knowl


def estimate(score_records, current_guess, current_slip, current_transit, mastery_prior, relevance_threshold=0.01,
             information_threshold=20, remove_degeneracy=True):
    """
    This function estimates the BKT model using empirical probabilities
    To account for the fact that NaN and Inf elements of the estimated
    matrices should not be used as updates, this function replaces such
    elements with the corresponding elements of the current BKT parameter
    matrices.
    Thus, the outputs of this function do not contain any non-numeric
    values and should be used to simply replace the current BKT parameter
    matrices.
    :param score_records: ?x3 np.array, first column is learner, second column is activity, third column is score
    :param current_guess: guess parameter matrix
    :param current_slip: slip parameter matrix
    :param current_transit: transit parameter matrix
    :param mastery_prior: 1x(# LOs) vector of mastery prior values
    :param relevance_threshold: float
    :param information_threshold: float
    :param remove_degeneracy: bool, Whether to remove guess and slip probabilities of 0.5 and above (degeneracy)
    :return: dict with keys:
        L_i: new mastery prior values for learning objectives
        trans: new transit matrix,
        guess: new guess matrix,
        slip: slip
        L_i_nan: new mastery prior values for learning objectives (with NaNs)
        trans_nan: new transit matrix (with NaNs)
        guess_nan: new guess matrix (with NaNs)
        slip_nan: new slip matrix (with NaNs)
    """

    n_items = current_guess.shape[0]
    n_los = current_guess.shape[1]

    trans = np.zeros((n_items, n_los))
    trans_denom = trans.copy()
    guess = trans.copy()
    guess_denom = trans.copy()
    slip = trans.copy()
    slip_denom = trans.copy()
    p_i = np.repeat(0., n_los)
    p_i_denom = p_i.copy()

    # full QxK relevance matrix
    m_k = calculate_relevance(guess, slip)

    score_learner = score_records[:, 0]
    score_activity = score_records[:, 1]
    # score_value = score_records[:, 2]

    # list of unique learner ids to iterate through
    learners = np.unique(score_learner)

    for learner in learners:
        # subset of score_records table for a particular learner
        user_score_records = score_records[score_activity == learner]

        # user_scores is a list of scores for a particular user u, arranged in chronological order.
        user_scores = user_score_records[:, 2]

        # if no data for learner, go to next learner
        if len(user_scores) == 0:
            continue

        # get activity matrix 0-based index values for each activity in user scores
        activity_idxs = user_score_records[:, 1].astype(int)

        # relevance values for each activity attempted by user
        m_k_u = m_k[activity_idxs, ]

        # Calculate the sum of relevances of user's experience for each learning objective
        u_R = np.sum(m_k_u, axis=0)

        # Implement the relevance threshold: zero-out what is not above it, set the rest to 1
        u_R = (u_R > relevance_threshold)
        m_k_u = (m_k_u > relevance_threshold)

        # calculate knowledge based on user scores
        u_knowledge = knowledge(user_score_records, current_guess, current_slip)

        # Contribute to the averaged initial knowledge.
        p_i += u_knowledge[0, ] * u_R
        p_i_denom += u_R

        # Contribute to the trans, guess and slip probabilities
        # (numerators and denominators separately).

        J = len(user_scores)

        # j is index within user_scores, score is score object
        for j, score in enumerate(user_scores):
            # q is matrix index for activity associated with score
            q = activity_idxs[j]

            shorthand = m_k_u[j, ] * (1.0 - u_knowledge[j,])
            guess[q, ] += shorthand * user_scores[j]
            guess_denom[q, ] += shorthand

            shorthand = m_k_u[j, ] - shorthand  # equals m_k_u * u_knowledge
            slip[q, ] += shorthand * (1.0 - user_scores[j])
            slip_denom[q, ] += shorthand

            if j < (J - 1):
                shorthand = m_k_u[j, ] * (1.0 - u_knowledge[j, ])
                trans[q, ] += shorthand * u_knowledge[j + 1, ]
                trans_denom[q, ] += shorthand

    # Normalize the results over users.
    ind = np.where(p_i_denom != 0)
    p_i[ind] /= p_i_denom[ind]
    ind = np.where(trans_denom != 0)
    trans[ind] /= trans_denom[ind]
    ind = np.where(guess_denom != 0)
    guess[ind] /= guess_denom[ind]
    ind = np.where(slip_denom != 0)
    slip[ind] /= slip_denom[ind]

    # Replace with nans where denominators are below information cutoff
    p_i[(p_i_denom < information_threshold) | (p_i_denom == 0)] = np.nan
    trans[(trans_denom < information_threshold) | (trans_denom == 0)] = np.nan
    guess[(guess_denom < information_threshold) | (guess_denom == 0)] = np.nan
    slip[(slip_denom < information_threshold) | (slip_denom == 0)] = np.nan

    # Remove guess and slip probabilities of 0.5 and above (degeneracy):
    if remove_degeneracy:
        # these two lines will throw warnings for comparisons to np.nan's
        ind_g = np.where((guess >= 0.5) | (guess + slip >= 1))
        ind_s = np.where((slip >= 0.5) | (guess + slip >= 1))

        guess[ind_g] = np.nan
        slip[ind_s] = np.nan

    # Convert to odds:
    L = odds(p_i)
    trans = odds(trans)
    guess = odds(guess)
    slip = odds(slip)

    # Keep the versions with NAs in them:
    L_i_nan = L.copy()
    trans_nan = trans.copy()
    guess_nan = guess.copy()
    slip_nan = slip.copy()

    # get existing matrices
    L_i = mastery_prior
    m_trans = current_transit
    m_guess = current_guess
    m_slip = current_slip

    # replace invalid values
    replace_nan(L, L_i, inplace=True)
    replace_nan(trans, m_trans, inplace=True)
    replace_nan(guess, m_guess, inplace=True)
    replace_nan(slip, m_slip, inplace=True)

    return {
        'L_i': 1.0*L,
        'trans': 1.0*trans,
        'guess': 1.0*guess,
        'slip': 1.0*slip,
        'L_i_nan': 1.0*L_i_nan,
        'trans_nan': 1.0*trans_nan,
        'guess_nan': 1.0*guess_nan,
        'slip_nan': 1.0*slip_nan
    }