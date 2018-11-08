##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

source("clean_slate.R")

time.start=proc.time()[3];


LogData$predicted=NA;
LogData$med_mastery_odds=NA

for(i in 1:nrow(transactions)){
    problem=transactions$problem_id[i]
    score=transactions$score[i]
    time=transactions$time[i]
    u=transactions$user_id[i]
    LogData$predicted[i]=predictCorrectness(u=u,problem=problem) ##Predict probability of success

    bayesUpdate(u=u,problem=problem,score=score,time=time,write=FALSE) ##Update the user's mastery matrix and history
    LogData$med_mastery_odds[i]=median(m.L[u,])
    
}

LogData$med_mastery_prob=LogData$med_mastery_odds/(1+LogData$med_mastery_odds)
LogData=LogData[order(LogData$user_id,LogData$time),]
LogData$nproblem=ave(LogData$score,LogData$user_id,FUN=seq_along)



cat("Elapsed seconds in knowledge tracing: ",round(proc.time()[3]-time.start,3),"\n")

