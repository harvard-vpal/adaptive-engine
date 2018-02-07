recommend=function(u, module=1, stopOnMastery=FALSE,maxitems=1){
  
  ##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns NULL.
  
  ##Exclude from the pool items that have been submitted too many times and which do not belong to the scope
  ind.pool=which(((m.times.submitted[u,]<probs$maxsubmits.for.serving)|(is.na(probs$maxsubmits.for.serving))) & scope[,module])
  
  #Check for the presence of a required next id. If yes, and if it is in the pool, return it and the recommendation is over.
  if(last.seen[u]!=''){
    next.prob.id=probs$required.next.id[match(last.seen[u],probs$id)]
    if(next.prob.id %in% names(ind.pool)){
      return(next.prob.id)
    }
  }
  
  
  L=log(m.L[u,])
  
  if (stopOnMastery){
    m.k.pool=m.k[ind.pool,,drop=FALSE]
    D=(m.k.pool %*% pmax((L.star-L),0))
    ind.pool=ind.pool[D!=0]
  }
  
  N=length(ind.pool)
  
  
  if(N==0){##This means we ran out of problems, so we stop
    next.prob.id=NULL
  }else{
    
    
    ## Subset relevance matrix to the pool
    m.k.pool=m.k[ind.pool,,drop=FALSE]
    scaling.factors=rowSums(m.k.pool)
    
    #Readiness substrategy
    m.r=(pmin(L-L.star,0) %*% m.w);  
    strategy$readiness=(m.k.pool %*% pmin(t(m.r+r.star),0))*W['readiness']
    
    #Remediation substrategy
    strategy$remediation=(m.k.pool %*% pmax((L.star-L),0))*W['remediation']
    
    #Continuity substrategy
    if(last.seen[u]==""){
      strategy$continuity=rep(0,N)
    }else{
      strategy$continuity=sqrt(m.k.pool %*% m.k[last.seen[u],])
    }
    strategy$continuity=strategy$continuity*W['continuity']
    
    #Difficulty matching substrategy  
    d.temp=m.difficulty[,ind.pool]
    L.temp=matrix(rep(L,N),nrow=n.los, byrow=F)
    strategy$difficulty=-diag(m.k.pool %*% (abs(L.temp-d.temp)))*W['difficulty']
    
    #Memory substrategy
    strategy$memory=(-m.item.memory[u,ind.pool]*scaling.factors)*W['memory']
    
    #Next suggested item substrategy
    strategy$suggested=(names(ind.pool)==probs$suggested.next.id[match(last.seen[u],probs$id)])*scaling.factors*W['suggested']
    
     
    
    
    #Combine sub-strategies and rank items 
    next.prob.id=names(ind.pool)[rev(order(Reduce('+',strategy)))]
    next.prob.id=next.prob.id[1:min(length(next.prob.id),maxitems)]
    
    
    
    
  }
  
  return(next.prob.id)
  
}