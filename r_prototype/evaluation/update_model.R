#Optimize the BKT parameters
time.start=proc.time()[3]

##Estimate on the training set
est=estimate(relevance.threshold=eta, information.threshold=M,remove.degeneracy=T, training.set)
cat("Elapsed seconds in estimating: ",round(proc.time()[3]-time.start,3),"\n")
m.L.i=est$L.i  ##Update the prior-knowledge matrix
ind.pristine=which(m.exposure==0); 
##Update the pristine elements of the current mastery probability matrix
m.L=replace(m.L,ind.pristine,m.L.i[ind.pristine])
#Update the transit, guess, slip odds
m.trans=est$trans
m.guess=est$guess
m.slip=est$slip