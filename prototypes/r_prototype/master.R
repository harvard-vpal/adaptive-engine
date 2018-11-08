##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")
source("recommendation.R")

####Initialize with fake data####
source("fakeInitials.R")
#####

m.L<<- m.L.i

source("derivedData.R")

TotalTime=50
curve=as.data.frame(t(m.L["u1",]))
user_ids=sample(users$id,TotalTime,replace=TRUE)
##Simulate user interactions: at each moment of time, a randomly picked user submits a problem
learningCurve=matrix(NA,ncol=ncol(m.L),nrow=TotalTime)
colnames(learningCurve)=colnames(m.L)

for (t in 1:TotalTime){
    
  u=user_ids[t]
    problem=recommend(u=u) ## Get the recommendation for the next question to serve to the user u. If there is no problem (list exhausted), will be NULL.
    if(!is.null(problem)){
      score=predictCorrectness(u,problem)
      
      bayesUpdate(u=u,problem=problem,score=score, time=t) ##Update the user's mastery matrix and the rest

    }
    
    learningCurve[t,]=m.L[u,]
    cat(problem,'\n')
}

learningCurve=learningCurve/(1+learningCurve)

#Optimize the BKT parameters
est=estimate(relevance.threshold=eta, information.threshold=M,remove.degeneracy=TRUE)
m.L.i=est$L.i  ##Update the prior-knowledge matrix

ind.pristine=which(m.exposure==0); ##Update the pristine elements of the current mastery probability matrix

m.L=replace(m.L,ind.pristine,m.L.i[ind.pristine])
#Update the transit, guess, slip odds
m.transit=est$transit
m.guess=est$guess
m.slip=est$slip
source("derivedData.R")
