##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")

####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=3 ##Information threshold used in the BKT optimization procedure
p.star<<-0.95 #Threshold probability. If mastery probability is >= than p.star, the LO is considered mastered
r.star<<-1 #Threshold for forgiving lower probability of mastering pre-requisite LOs.
V.r<<-3 ##Importance of readiness in recommending the next item
V.d<<-1 ##Importance of demand in recommending the next item
V.a<<-3 ##Importance of appropriatness in recommending the next item

#####

####Initialize with fake data####
n.users<<-20
n.los<<-10
n.probs<<-100
users=data.frame("id"=paste0("u",1:n.users),"name"=paste0("user ",1:n.users))
users$id=as.character(users$id)
los=data.frame("id"=paste0("l",1:n.los),"name"=paste0("LO ",1:n.los))
los$id=as.character(los$id)
probs=data.frame("id"=paste0("p",1:n.probs),"name"=paste0("problem ",1:n.probs))
probs$id=as.character(probs$id)
source("fakeInitials.R")
#####

m.p=pmax(m.p.i,epsilon)

m.log.odds=log(m.p)-log(1-m.p)

curve=as.data.frame(t(m.p["u1",]))


##Simulate user interactions: at each moment of time, a randomly picked user submits a problem
for (t in 1:2000){
    u=sample(users$id,1)
    problem=recommend(u=u) ## Get the recommendation for the next question to serve to the user u. If there is no problem (list exhausted), will be NULL.
    if(!is.null(problem)){
      
      score=0.01*qbinom(runif(1),100,0.5) #User's score.
        m.unseen[u,problem]=F  ##Record that the user has seen this problem.
        m.correctness[u,problem]=score ##Record the user's answer to the problem.
        m.timestamp[u,problem]=t ##Record the time.
        
        b=bayesUpdate(log.odds=m.log.odds[u,], k=m.k[problem,], score=score, odds.incr.zero=m.odds.incr.zero[problem,],odds.incr.slope=m.odds.incr.slope[problem,],p.transit=m.transit[problem,]) ##Update the user's mastery matrix
        # b=bayesUpdate(p=m.p[u,], k=m.k[problem,], score=score, p.slip=m.slip[problem,],p.guess=m.guess[problem,],p.transit=m.transit[problem,]) ##Update the user's mastery matrix
        m.log.odds[u,]=b$log.odds
        m.p[u,]=b$p
        m.p.pristine[u,]=m.p.pristine[u,]&(b$odds.incr==0) ##keep track if some LOs have never been updated from the initial value; These will be affected once we optimize the initial values.
        # m.p[u,]=b$p
        # m.p.pristine[u,]=m.p.pristine[u,]&(b$incr==0) ##keep track if some LOs have never been updated from the initial value; These will be affected once we optimize the initial values.
        
    }
  curve=rbind(curve,t(m.p["u1",])) ##Track the learning curves of user 1.
}



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
est=estimate(eta)
m.p.i=est$p.i  ##Update the prior-knowledge matrix

ind.pristine=which(m.p.pristine); ##Update the pristine elements of the current mastery probability matrix
m.p=replace(m.p,ind.pristine,m.p.i[ind.pristine]) ##Apply the optimized priors to the pristine mastery probabilities

#Update the transit, guess, slip matrices
m.transit=est$transit
m.guess=est$guess
m.slip=est$slip

m.odds.incr.zero<<- log(pmax(m.slip,epsilon)) - log(1-pmax(m.guess,epsilon))
m.odds.incr.slope<<- log((1-pmax(m.slip,epsilon))/pmax(m.slip,epsilon)) + log((1-pmax(m.guess,epsilon))/pmax(m.guess,epsilon))
