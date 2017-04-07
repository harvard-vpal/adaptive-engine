bayesUpdate=function(p,k, score=1, p.slip=0.1, p.guess=0.1, p.transit=0.1){
  
  
  #This function takes the row of student mastery probabilities (a row of the matrix p.matrix) and returns it updated after one student/LO interaction.
  #The problem is tagged by the learning objectives with relevance values k (k is a row of the matrix m.k)

  
  #p.slip is probability of answering wrong despite knowing the skill
  #p.guess is probability of answering correct despite not knowing the skill
  #p.transit is probability of learning the skill because of the interaction, even if the answer was wrong.
  
  x.one=p*(1-p.slip)/(p*(1-p.slip)+(1-p)*p.guess)
  x.zero=p*p.slip/(p*p.slip+(1-p)*(1-p.guess))
  
  x=x.zero + (x.one-x.zero)*score
  
  
  # if(ans){
  #   x=p*(1-p.slip)/(p*(1-p.slip)+(1-p)*p.guess)
  # }else{
  #   x=p*p.slip/(p*p.slip+(1-p)*(1-p.guess))
  # }
  
  incr=k*(x+(1-x)*p.transit-p)
  p=p+incr
  
  p=pmax(p,epsilon)
  
  return(list(p=p,incr=incr))

}


recommend=function(u){
  
  ##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns NULL.
  p=m.p[u,]
  temp=pmin(t(as.matrix(p)/p.star),1)
  
  #Calculate the user readiness for LOs
  m.log=log(temp);
  m.r=exp(m.log %*% m.w);
  m.r[which(is.na(m.r))]=1 ##We agree that  0^0=1
  
  #Subset to the unseen problems and calculate problem readiness and demand
  ind.unseen=which(m.unseen[u,])
  if(length(ind.unseen)==0){##This means we ran out of problems, so we stop
    next.prob.id=NULL
  }else{
      m.k.unseen=m.k[ind.unseen,]
      R=m.k.unseen %*% pmax(t(m.r-r.star),0)
      D=m.k.unseen %*% pmax(t(1-temp),0)
      A=0
      
      d.temp=matrix(rep(difficulty[ind.unseen],n.los),ncol=n.los)
      p.temp=matrix(rep(p,length(ind.unseen)),ncol=n.los, byrow=T)
      A=diag(m.k.unseen %*% t(1-abs(d.temp-p.temp)))

      if(sum(D)==0){##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
        next.prob.id=NULL
      }else{
      next.prob.id=rownames(R)[which.max(V.r*R+V.d*D+V.a*A)]
      
      }
  }
  return(next.prob.id)
  
}