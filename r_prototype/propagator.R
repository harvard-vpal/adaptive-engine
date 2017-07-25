##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

bayesUpdate=function(u, problem, score=1, time=1, attempts="all"){
  
  last.seen[u]<<-problem
  

  if(m.unseen[u,problem]){
    m.unseen[u,problem]<<-FALSE
    m.exposure[u,]<<-m.exposure[u,]+m.tagging[problem,]
    m.confidence[u,]<<-m.confidence[u,]+m.k[problem,]
    
    if(attempts=="first"){
      transactions<<-rbind(transactions,data.frame(user_id=u,problem_id=problem,time=time,score=score))
      x=m.x0[problem,]*((m.x10[problem,])^score)
      L=m.L[u,]*x
      
      ##Add the transferred knowledge
      
      L=L+m.trans[problem,]*(L+1)
    }
    
  }
  
  if(attempts!="first"){
    transactions<<-rbind(transactions,data.frame(user_id=u,problem_id=problem,time=time,score=score))
    x=m.x0[problem,]*((m.x10[problem,])^score)
   L=m.L[u,]*x
  
    ##Add the transferred knowledge

    L=L+m.trans[problem,]*(L+1)
  }
  
  
  
  ##In case of maxing out to infinity or zero, apply cutoff.
  L[which(is.infinite(L))]=inv.epsilon
  L[which(L==0)]=epsilon
  
  m.L[u,]<<-L

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


recommend=function(u, module=1, stopOnMastery=TRUE){
  
  ##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns NULL.
  
  ind.unseen=which(m.unseen[u,] & ((scope==module)|(scope==0)))
  L=log(m.L[u,])
  
  if (stopOnMastery){
    m.k.unseen=m.k[ind.unseen,]
    D=(m.k.unseen %*% pmax((L.star-L),0))
    ind.unseen=ind.unseen[D!=0]
  }
  
  N=length(ind.unseen)
  
  if(N==0){##This means we ran out of problems, so we stop
    next.prob.id=NULL
  }else{
    #Calculate the user readiness for LOs
    m.r=(pmin(L-L.star,0) %*% m.w);  
    m.k.unseen=m.k[ind.unseen,]
      
    R=(m.k.unseen %*% pmin(t(m.r+r.star),0))
    D=(m.k.unseen %*% pmax((L.star-L),0))
    if(last.seen[u]==""){
      C=rep(0,N)
    }else{
      C=m.k.unseen %*% m.k[last.seen[u],]
    }
      
    d.temp=m.difficulty[,ind.unseen]
    L.temp=matrix(rep(L,N),nrow=n.los, byrow=F)
    A=-diag(m.k.unseen %*% (abs(L.temp-d.temp)))

    next.prob.id=NULL
  
    temp=1/diff(range(A));
    if(!is.infinite(temp)){A=A*temp}
    temp=1/diff(range(D));
    if(!is.infinite(temp)){D=D*temp}
    temp=1/diff(range(R));
    if(!is.infinite(temp)){R=R*temp}
    temp=1/diff(range(C));
    if(!is.infinite(temp)){C=C*temp}
        
        
      next.prob.id=rownames(R)[which.max(V.r*R+V.d*D+V.a*A+V.c*C)]
      
      
      
     
  }
  return(next.prob.id)
  
}