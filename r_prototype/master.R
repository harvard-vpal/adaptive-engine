##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")

####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=0 ##Relevance threshold used in the BKT optimization procedure
M=20 ##Information threshold user in the BKT optimization procedure
L.star<<- 3 #Threshold odds. If mastery odds are >= than L.star, the LO is considered mastered
r.star<<- 0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.
V.r<<-5 ##Importance of readiness in recommending the next item
V.d<<-3 ##Importance of demand in recommending the next item
V.a<<-1 ##Importance of appropriate difficulty in recommending the next item
V.c<<-1 ##Importance of continuity in recommending the next item
#####

####Initialize with fake data####
source("fakeInitials.R")
#####

m.L<<- m.L.i

source("derivedData.R")


curve=as.data.frame(t(m.L["u1",]))


##Simulate user interactions: at each moment of time, a randomly picked user submits a problem
for (t in 1:4000){
    u=sample(users$id,1)
    problem=recommend(u=u) ## Get the recommendation for the next question to serve to the user u. If there is no problem (list exhausted), will be NULL.
    if(!is.null(problem)){
      
      p.predict=predictCorrectness(u=u,problem=problem) ##Predict probability of success
      score=as.numeric(runif(1)<p.predict) ##Assume that the user succeeds with the predicted probability
      score=as.numeric(runif(1)<0.7)
        m.unseen[u,problem]=F  ##Record that the user has seen this problem.
        m.correctness[u,problem]=score ##Record the user's answer to the problem.
        m.timestamp[u,problem]=t ##Record the time.
        last.seen[u]=problem ##Record this problem as the last seen by the user
        
        b=bayesUpdate(u=u,problem=problem,score=score) ##Update the user's mastery matrix
        m.L[u,]=b$L
        m.pristine[u,]=m.pristine[u,]&(b$x==0) ##keep track if some LOs have never been updated from the initial value; These will be affected once we optimize the initial values.
    }
  curve=rbind(curve,t(m.L["u1",])) ##Track the learning curves of user 1.
}

curve=exp(curve)
curve=curve/(curve+1)

##Some plots
# p0=plot_ly(z=m.p.i,type="heatmap")
# p1=plot_ly(z=m.p,type="heatmap")
# print(subplot(p0,p1,nrows=1))

p=plot_ly()
for ( i in 1:ncol(curve)){
  p=p%>%add_trace(y=curve[,i],type="scatter",mode="points+lines", name=los$name[i])
}
p=p%>%layout(title="Learning curves of user 1", xaxis=list(title="Time"),yaxis=list(title="probability of mastery"))
print(p)

##Optimize the BKT parameters
# est=estimate(relevance.threshold=eta, information.threshold=M,remove.degeneracy=T)
# m.L.i=est$L.i  ##Update the prior-knowledge matrix
# 
# ind.pristine=which(m.pristine); ##Update the pristine elements of the current mastery probability matrix
# 
# m.L=replace(m.L,ind.pristine,m.L.i[ind.pristine])
# #Update the transit, guess, slip odds
# m.transit=est$transit
# m.guess=est$guess
# m.slip=est$slip
source("derivedData.R")
