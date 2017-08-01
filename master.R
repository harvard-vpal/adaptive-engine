##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")

####Initialize with fake data####
source("fakeInitials.R")
#####

m.L<<- m.L.i

source("derivedData.R")

TotalTime=2000
curve=as.data.frame(t(m.L["u1",]))
user_ids=sample(users$id,TotalTime,replace=TRUE)
##Simulate user interactions: at each moment of time, a randomly picked user submits a problem
# for(u in users$id[users$group==0]){
# for (t in 1:n.probs){
for (t in 1:TotalTime){
    
  u=user_ids[t]
    problem=recommend(u=u) ## Get the recommendation for the next question to serve to the user u. If there is no problem (list exhausted), will be NULL.
    if(!is.null(problem)){
      score=predictCorrectness(u,problem)
      # score=0.1+0.2*runif(1)
      # score=0.1;
      # score=0
      
      bayesUpdate(u=u,problem=problem,score=score, time=t) ##Update the user's mastery matrix

    }
 # curve=rbind(curve,t(m.L["u1",])) ##Track the learning curves of user 1.
}
# }
curve=curve/(curve+1)

##Some plots
# p0=plot_ly(z=m.p.i,type="heatmap")
# p1=plot_ly(z=m.p,type="heatmap")
# print(subplot(p0,p1,nrows=1))
# 
# p=plot_ly()
# for ( i in 1:ncol(curve)){
#   p=p%>%add_trace(y=curve[,i],type="scatter",mode="points+lines", name=los$name[i])
# }
# p=p%>%layout(title="Learning curves of user 1", xaxis=list(title="Time"),yaxis=list(title="probability of mastery"))
# print(p)

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
