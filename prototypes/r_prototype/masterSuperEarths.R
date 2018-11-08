##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("/Users/ilr548/Dropbox/BKT/multiplicative formulation/propagator.R")
source("/Users/ilr548/Dropbox/BKT/multiplicative formulation/optimizer.R")


source("initialsSuperEarths.R")

m.L<<- m.L.i

source("/Users/ilr548/Dropbox/BKT/multiplicative formulation/derivedData.R")
time.start=proc.time()[3];
if(!before.optimizing){
  curve=matrix(NA,nrow=1,ncol=n.los)
Pcheck$predicted=NA;
for(i in 1:nrow(Pcheck)){
    problem=Pcheck$problem_id[i]
    score=Pcheck$correctness[i]
    time=Pcheck$time[i]
    u=Pcheck$username[i]
    Pcheck$predicted[i]=predictCorrectness(u=u,problem=problem) ##Predict probability of success
    bayesUpdate(u=u,problem=problem,score=score,time=time) ##Update the user's mastery matrix and history
    
    ##This matrix tracks whether this is the situation when the user had no prior interaction with the learning objectives
    temp=(m.exposure[u,,drop=F]) %*% t(m.tagging[problem,,drop=F])
    m.exposure.before.problem[u,problem]=temp

    # if(u=="DevonBMason"){
    #   curve=rbind(curve,m.L[u,])
    # }
      
    
}


cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")
}

# 
# p=plot_ly()
# for ( i in 1:ncol(curve)){
#   p=p%>%add_trace(x=1:nrow(curve),y=curve[,i]/(1+curve[,i]),type="scatter",mode="markers+lines", name=los$name[i])
# }
# p=p%>%layout(title="Learning curves of user 1", xaxis=list(title="Time"),yaxis=list(title="probability of mastery"))
# print(p)


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
