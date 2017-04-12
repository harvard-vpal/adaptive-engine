## Calculate the useful matrices of gues and slip probabilities and of negative logs of the odds.
m.guess.neg.log<<- -log(m.guess)
m.p.guess<<- m.guess/(m.guess+1)

m.slip.neg.log<<- -log(m.slip)
m.p.slip<<- m.slip/(m.slip+1)


##Define the matrix of mixed odds and of relevance m.k:
m.x0<<- log(m.slip*(1+m.guess)/(1+m.slip))
m.k<<- -log(m.guess)-log(m.slip)
