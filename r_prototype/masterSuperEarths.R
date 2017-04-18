##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


library(plotly)
source("propagator.R")
source("optimizer.R")

####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
# eta=0 ##Relevance threshold used in the BKT optimization procedure
# M=50 ##Information threshold user in the BKT optimization procedure
L.star<<- 3 #Threshold odds. If mastery odds are >= than L.star, the LO is considered mastered
r.star<<- 0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.
V.r<<-5 ##Importance of readiness in recommending the next item
V.d<<-3 ##Importance of demand in recommending the next item
V.a<<-1 ##Importance of appropriate difficulty in recommending the next item

#####

####Initialize data####
# source("fakeInitials.R")


# if(before.optimizing){
source("initialsSuperEarths.R")
# }
  #####

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
        temp=(!m.pristine[u,,drop=F]) %*% t(m.tagging[problem,,drop=F])
        m.include[u,problem]=(temp>0)
        
        m.pristine[u,]=m.pristine[u,]&(b$x==0) ##keep track if some LOs have never been updated from the initial value; These will be affected once we optimize the initial values.
        
        #############################################################################
        ##The first several scores from a user are not included into the evaluation##
        #############################################################################
        # if(i>4){
        #   m.include[u,problem]=T
        # }
        

        
        
        
        
  # curve=rbind(curve,t(m.L["u1",])) ##Track the learning curves of user 1.
  }
}
cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")

source("evaluate.R")

# curve=exp(curve)
# curve=curve/(curve+1)

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

if(before.optimizing){
#Optimize the BKT parameters
time.start=proc.time()[3]
est=estimate(relevance.threshold=eta, information.threshold=M,remove.degeneracy=T)
cat("Elapsed seconds in estimating: ",round(proc.time()[3]-time.start,3),"\n")
m.L.i=est$L.i  ##Update the prior-knowledge matrix

ind.pristine=which(m.pristine); ##Update the pristine elements of the current mastery probability matrix

m.L=replace(m.L,ind.pristine,m.L.i[ind.pristine])
#Update the transit, guess, slip odds
m.trans=est$trans
m.guess=est$guess
m.slip=est$slip
}
# source("derivedData.R")
