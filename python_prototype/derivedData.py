##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
import numpy as np

##Define infinity cutoff and the log cutoff:
inv_epsilon=1.0/epsilon

log_epsilon=-np.log(epsilon)

## Calculate the useful matrices of guess and slip probabilities and of negative logs of the odds.
m_guess_neg_log= -np.log(m_guess)
m_p_guess= m_guess/(m_guess+1.0)

m_slip_neg_log= -np.log(m_slip)
m_p_slip= m_slip/(m_slip+1.0)

#m_trans_log = np.log(m_trans)
#m_g_trans = m_trans_log-m_trans

##Define the matrix of mixed odds:

#m_x0_add= np.log(m_slip*(1.0+m_guess)/(1.0+m_slip)) ##Additive formulation

#Multiplicative formulation
m_x0_mult= m_slip*(1.0+m_guess)/(1.0+m_slip)
#m_x1_mult=(1.0+m_guess)/(m_guess*(1.0+m_slip))
m_x1_0_mult=((1.0+m_guess)/(m_guess*(1.0+m_slip)))/m_x0_mult


#m_x1_0_mult= (1.0+m_guess)/(m_guess*(1.0+m_slip))-m_x0_mult


##Define the matrix of relevance m_k
m_k= -np.log(m_guess)-np.log(m_slip)


##Normalize and prepare difficulty vector:

#if(difficulty.max()!=difficulty.min()):
#    difficulty=(difficulty-difficulty.min())/(difficulty.max()-difficulty.min())

difficulty=np.minimum(np.maximum(difficulty,epsilon),1-epsilon)

difficulty_mult=difficulty/(1.0-difficulty)
difficulty_add=np.log(difficulty_mult)

##Define a matrix of problem difficulties clones for all LOs (used in recommendation)
#m_difficulty_mult=np.tile(difficulty_mult,(n_los,1))
m_difficulty=np.tile(difficulty_add,(n_los,1))
