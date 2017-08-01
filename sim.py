##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

#Should L be mastery odds(for multiplicative) or logarithmic odds (for additive formulation)?
multiplicative=True
execfile('multiplicativeFormulation.py')
execfile('empiricalEstimation.py')
execfile('fakeInitials.py')
execfile('derivedData.py')


T=2000

user_ids=np.random.choice(users,T)
score=np.random.choice([0,1],T)

m_L=m_L_i.copy()

for t in range(T):
    
    u=mapUser(user_ids[t])
    rec_item=recommend(u)
    
    if rec_item!=None:
        bayesUpdate(u,rec_item,score[t],t)
        
        
updateModel()
        
