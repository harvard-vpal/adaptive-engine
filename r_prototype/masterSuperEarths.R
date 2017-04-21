##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")





source("initialsSuperEarths.R")

m.L<<- m.L.i

source("derivedData.R")


##

m.include=!m.unseen;

time.start=proc.time()[3];

##df is the course data: Each row is a user submit event. The necessary columns: user_id, problem_id, timestamp,correctness. Only one attempt per problem (in SuperEarths I subsetted the data to 1st attempts only)

for(u in users$id){
  # cat(u,"\n")
  df=subset(Pcheck,username==u)
  df=df[order(df$time),]
  for (i in 1:nrow(df)){
        problem=df$problem_id[i]
        score=df$correctness[i]
        t=df$time[i]
        temp=predictCorrectness(u=u,problem=problem) ##Predict probability of success
        m.predicted[u,problem]=temp
        m.correctness[u,problem]=score ##Record the user's answer to the problem.
        m.unseen[u,problem]=F  ##Record that the user has seen this problem.
        m.timestamp[u,problem]=t ##Record the time.
        b=bayesUpdate(u=u,problem=problem,score=score) ##Update the user's mastery matrix
        m.L[u,]=b$L

        ##This matrix tracks whether this is the situation when the user had no prior interaction with the learning objectives
        temp=(m.exposure[u,,drop=F]) %*% t(m.tagging[problem,,drop=F])
        m.exposure.before.problem[u,problem]=temp
        
        m.exposure[u,]=m.exposure[u,]+m.tagging[problem,]

  }
}
cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")

source("evaluate.R")


if(before.optimizing){
#Optimize the BKT parameters
time.start=proc.time()[3]
est=estimate(relevance.threshold=eta, information.threshold=M,remove.degeneracy=T)
cat("Elapsed seconds in estimating: ",round(proc.time()[3]-time.start,3),"\n")
m.L.i=est$L.i  ##Update the prior-knowledge matrix

ind.pristine=which(m.exposure==0); ##Update the pristine elements of the current mastery probability matrix

m.L=replace(m.L,ind.pristine,m.L.i[ind.pristine])
#Update the transit, guess, slip odds
m.trans=est$trans
m.guess=est$guess
m.slip=est$slip
}
# source("derivedData.R")
