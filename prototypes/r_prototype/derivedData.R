##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


inv.epsilon<<-1/epsilon

log.epsilon<<--log(epsilon)

## Calculate the useful matrices of guess and slip probabilities and of negative logs of the odds.
m.guess.neg.log<<- -log(m.guess)
m.p.guess<<- m.guess/(m.guess+1)

m.slip.neg.log<<- -log(m.slip)
m.p.slip<<- m.slip/(m.slip+1)

# m.trans.log <<- log(m.trans)
# m.g.trans <<- m.trans.log-m.trans


##Define the matrix of mixed odds and of relevance m.k:
m.x0<<- (m.slip*(1+m.guess)/(1+m.slip))
m.x1<<- ((1+m.guess)/(m.guess*(1+m.slip)))
#m.x10<<-m.x1-m.x0
m.x10<<-m.x1/m.x0

 m.k<<- -log(m.guess)-log(m.slip)




 ##Define a matrix of problem difficulties clones for all LOs (used in recommendation)
 m.difficulty<<-matrix(rep(difficulty,n.los),ncol=n.los, byrow = FALSE)
 rownames(m.difficulty)=probs$id
 colnames(m.difficulty)=los$id
 m.difficulty=t(m.difficulty)

 