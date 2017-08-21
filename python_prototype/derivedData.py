##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
import numpy as np

def calculate_derived_data(self):

    ##Define infinity cutoff and the log cutoff:
    self.inv_epsilon=1.0/self.epsilon

    self.log_epsilon=-np.log(self.epsilon)

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

    self.difficulty=np.minimum(np.maximum(self.difficulty,self.epsilon),1-self.epsilon)

    self.difficulty_mult=self.difficulty/(1.0-self.difficulty)
    self.difficulty_add=np.log(self.difficulty_mult)

    ##Define a matrix of problem difficulties clones for all LOs (used in recommendation)
    #m_difficulty_mult=np.tile(difficulty_mult,(n_los,1))
    n_los = len(self.los)
    self.m_difficulty=np.tile(self.difficulty_add,(n_los,1))
