##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("./multiplicative formulation/propagator.R")
source("./multiplicative formulation/optimizer.R")





source("initialsSuperEarths.R")

m.L<<- m.L.i

source("./multiplicative formulation/derivedData.R")


time.start=proc.time()[3];

##df is the course data: Each row is a user submit event. The necessary columns: user_id, problem_id, timestamp,correctness. Only one attempt per problem (in SuperEarths I subsetted the data to 1st attempts only)
# curve=as.data.frame(t(m.L["DevonBMason",]))
for(u in users$id){
  df=subset(Pcheck,username==u)
  df=df[order(df$time),]
  for (i in 1:nrow(df)){
        problem=df$problem_id[i]
        score=df$correctness[i]
        t=df$time[i]
        m.predicted[u,problem]=predictCorrectness(u=u,problem=problem) ##Predict probability of success
        bayesUpdate(u=u,problem=problem,score=score) ##Update the user's mastery matrix and history

        ##This matrix tracks whether this is the situation when the user had no prior interaction with the learning objectives
        temp=(m.exposure[u,,drop=F]) %*% t(m.tagging[problem,,drop=F])
        m.exposure.before.problem[u,problem]=temp
        
        # if(u=="DevonBMason"){
        # curve=rbind(curve,t(m.L["DevonBMason",])) ##Track the learning curves of user 1.
        # }
  }
}
cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")

# curve=curve/(curve+1)
# p=plot_ly()
# for ( i in 1:ncol(curve)){
#   p=p%>%add_trace(y=curve[,i],type="scatter",mode="points+lines", name=los$name[i])
# }
# p=p%>%layout(title="Learning curves of user 1", xaxis=list(title="Time"),yaxis=list(title="probability of mastery"))
# print(p)

source("evaluate.R")


if(before.optimizing){
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
}
