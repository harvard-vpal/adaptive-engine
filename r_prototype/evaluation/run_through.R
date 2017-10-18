##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

source("clean_slate.R")

time.start=proc.time()[3];


LogData$predicted=NA;
for(i in 1:nrow(transactions)){
    problem=transactions$problem_id[i]
    score=transactions$score[i]
    time=transactions$time[i]
    u=transactions$user_id[i]
    LogData$predicted[i]=predictCorrectness(u=u,problem=problem) ##Predict probability of success
    bayesUpdate(u=u,problem=problem,score=score,time=time,write=FALSE) ##Update the user's mastery matrix and history
}


cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")

