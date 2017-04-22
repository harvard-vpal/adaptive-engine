##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

bayesUpdate=function(u, problem, score=1, simplified.transit=F){
  
  
  #This function takes the row of student mastery probabilities (log-odds of them) and returns it updated after one student/LO interaction.
  #The problem is tagged by the learning objectives with relevance values k (k is a row of the matrix m.k)
  
  ##The increment of log-odds due to evidence of the problem, but before the transfer
  x=m.x0[problem,]+score*m.k[problem,]
  L=m.L[u,]+x
  
  ##Add the transferred knowledge
  trans=m.trans[problem,]
  
  if(simplified.transit){
    temp=L+trans
    temp[L<m.g.trans[problem,]]=m.trans.log[problem,]
    L=temp
  }else{
  L=log(trans+(trans+1)*exp(L))
  }
  
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
  if(is.na(p)){
    p=1
  }
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
      
      
      R=(m.k.unseen %*% pmin(t(m.r+r.star),0))
      D=(m.k.unseen %*% pmax((L.star-L),0))
      
      if(is.na(last.seen[u])){
        C=0
      }else{
        C=m.k.unseen %*% m.k[last.seen[u],]
      }
      
      A=0
      
      d.temp=matrix(rep(difficulty[ind.unseen],n.los),ncol=n.los)
      L.temp=matrix(rep(L,length(ind.unseen)),ncol=n.los, byrow=T)
      A=-diag(m.k.unseen %*% t(abs(L.temp-d.temp)))

      if(sum(D)==0){##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
        next.prob.id=NULL
      }else{
        
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
      
     
  }
  return(next.prob.id)
  
}