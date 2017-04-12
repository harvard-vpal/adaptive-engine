##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

bayesUpdate=function(u, problem, score=1){
  
  
  #This function takes the row of student mastery probabilities (log-odds of them) and returns it updated after one student/LO interaction.
  #The problem is tagged by the learning objectives with relevance values k (k is a row of the matrix m.k)
  
  ##The increment of log-odds due to evidence of the problem, but before the transfer
  x=m.x0[problem,]+score*m.k[problem,]
  L=m.L[u,]+x
  
  ##Add the transferred knowledge
  trans=m.trans[problem,]
  L=log(trans+(trans+1)*exp(L))
  
  return(list(L=L,x=x))

}

predictCorrectness=function(u, problem){
  
  
  #This function calculates the probability of correctness on a problem, as a prediction based on student's current mastery.
  
  L=m.L[u,]
  p.slip=m.p.slip[problem,];
  p.guess=m.p.guess[problem,];

  odds=exp(L);
  
  x=(odds*(1-p.slip)+p.guess)/(odds*p.slip+1-p.guess); ##Odds by LO
  x=prod(x) ##Total odds
  
  p=x/(1+x) ##Convert odds to probability
  return(p)
  
}


recommend=function(u){
  
  ##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns NULL.
  L=m.L[u,]
  p=L/(L+1)
  #Calculate the user readiness for LOs

  m.r=(pmin(L-L.star,0) %*% m.w);

  #Subset to the unseen problems and calculate problem readiness and demand
  ind.unseen=which(m.unseen[u,])
  if(length(ind.unseen)==0){##This means we ran out of problems, so we stop
    next.prob.id=NULL
  }else{
      m.k.unseen=m.k[ind.unseen,]
      
      ##Calculate the common normalization factor (R requires doing the case of 1 row separately.)
      if(length(ind.unseen)>1){
      normalization=1/rowSums(m.k.unseen);
      }else{
        normalization=sum(m.k.unseen)
      }
      
      R=(m.k.unseen %*% pmin(t(m.r+r.star),0))*normalization
      D=(m.k.unseen %*% pmax((L.star-L),0))*normalization
      A=0
      
      d.temp=matrix(rep(difficulty[ind.unseen],n.los),ncol=n.los)
      L.temp=matrix(rep(L,length(ind.unseen)),ncol=n.los, byrow=T)
      A=-diag(m.k.unseen %*% t(abs(L.temp-L.temp)))*normalization

      if(sum(D)==0){##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
        next.prob.id=NULL
      }else{
      next.prob.id=rownames(R)[which.max(V.r*R+V.d*D+V.a*A)]
      
      }
  }
  return(next.prob.id)
  
}