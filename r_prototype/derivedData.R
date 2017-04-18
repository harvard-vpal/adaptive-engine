##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

## Calculate the useful matrices of guess and slip probabilities and of negative logs of the odds.
m.guess.neg.log<<- -log(m.guess)
m.p.guess<<- m.guess/(m.guess+1)

m.slip.neg.log<<- -log(m.slip)
m.p.slip<<- m.slip/(m.slip+1)

m.trans.log <<- log(m.trans)
m.g.trans <<- m.trans.log-m.trans


##Define the matrix of mixed odds and of relevance m.k:
m.x0<<- log(m.slip*(1+m.guess)/(1+m.slip))
m.k<<- -log(m.guess)-log(m.slip)


