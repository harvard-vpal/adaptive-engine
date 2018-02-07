##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

bayesUpdate=function(u, problem, score=1, time=1, attempts="all", write=TRUE){
  
  options(stringsAsFactors = FALSE)
  
  if((attempts!="first")|((attempts=="first")&(m.timessubmitted[u,problem]==0))){
    if(write){
      transactions<<-rbind(transactions,data.frame(user_id=u,problem_id=problem,time=time,score=score))
    }
    x=m.x0[problem,]*((m.x10[problem,])^score)
   L=m.L[u,]*x
  
    ##Add the transferred knowledge

    L=L+m.trans[problem,]*(L+1)
  }
  
  
  
  ##In case of maxing out to infinity or zero, apply cutoff.
  L[which(is.infinite(L))]=inv.epsilon
  L[which(L==0)]=epsilon
  m.L[u,]<<-L
  
  ##Bookkeeping:
  
  ##Record the problem's ID as the last seen by this user.
  last.seen[u]<<-problem
  
  ##Propagate the memory of all items for this user:
  m.item.memory[u,]<<-m.item.memory[u,]*m.forgetting[u,]
  ##Update the memory of the submitted item:
  m.item.memory[u,problem]<<-m.item.memory[u,problem]+1
  
  
  ##Record that item was submitted
  m.times.submitted[u,problem]<<-m.times.submitted[u,problem]+1
  ##Update exposure and confidence for this user/KC combinations
  m.exposure[u,]<<-m.exposure[u,]+m.tagging[problem,]
  m.confidence[u,]<<-m.confidence[u,]+m.k[problem,]
}

predictCorrectness=function(u, problem){
  
  
  #This function calculates the probability of correctness on a problem, as a prediction based on student's current mastery.
  
  L=m.L[u,]
  p.slip=m.p.slip[problem,];
  p.guess=m.p.guess[problem,];
  
  x=(L*(1-p.slip)+p.guess)/(L*p.slip+1-p.guess); ##Odds by LO
  # x=(L*(1-p.slip)+p.guess)/(L+1); ##Odds by LO
  x=prod(x) ##Total odds
  
  p=x/(1+x) ##Convert odds to probability
  if(is.na(p)|is.infinite(p)){
    p=1
  }
  return(p)
  
}