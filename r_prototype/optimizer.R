##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

knowledge=function(prob_id,correctness){
##This function finds the empirical knowledge of a single user given a chronologically ordered sequence of items submitted.
  
m.ku=m.k[prob_id,]
N=length(prob_id)
  
z=matrix(0,nrow=N+1,ncol=ncol(m.k));
x=rep(0,N)
z[1,]=(1-correctness) %*% m.ku;
z[N+1,]=correctness %*% m.ku;

for(n in 1:(N-1)){
  x[1:n]=correctness[1:n];
  x[(n+1):N]=1-correctness[(n+1):N]
  z[n+1,]=x %*% m.ku
}

knowledge=matrix(0,ncol=ncol(m.k),nrow=N);
rownames(knowledge)=prob_id;
colnames(knowledge)=colnames(m.k)
for (j in 1:ncol(z)){
ind=which(z[,j]==min(z[,j]))
for (i in ind){
  
  temp=rep(0,N);
  if (i==1){
    temp=rep(1,N)
  }else if (i<=N){
    temp[i:N]=1
  }
  
  knowledge[,j]=knowledge[,j]+temp
  
}

knowledge[,j]=knowledge[,j]/length(ind)

}

return(knowledge)


}



estimate=function(info.threshold=0){
  
##This function estimates the matrices of the BKT parameters from the user interaction data.
##To account for the fact that NaN and Inf elements of the estimated matrices should not be used as updates, this function replaces such elements with the corresponding elements of the current BKT parameter matrices.
##Thus, the outputs of this function do not contain any non-numeric values and should be used to simply replace the current BKT parameter matrices.

transit=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
transit.denom=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
guess=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
guess.denom=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
slip=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
slip.denom=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
p.i=rep(0,n.los);
p.i.denom=rep(0,n.los)

for (u in rownames(m.timestamp)){
  
  ##List problems that the user tried, in chronological order
  
  n.of.na=length(which(is.na(m.timestamp[u,])))
  prob_id=colnames(m.timestamp)[order(m.timestamp[u,])] ##It is important here that order() puts NAs at the end, so we remove them from there
  prob_id=prob_id[-((length(prob_id)-n.of.na+1):length(prob_id))] ##These are id_s of items submitted by user u, in chronological order.
  J=length(prob_id)
  if(J>0){
    
  m.ku=m.k[prob_id,]
  if(J==1){
    u.R=m.ku
  }else{
  u.R=colSums(m.ku)
  }
  u.knowledge=knowledge(prob_id, m.correctness[u,prob_id]);
  u.correctness=m.correctness[u,prob_id]
  
  ##Contribute to the averaged initial knowledge.
  p.i=p.i+u.knowledge[1,]*u.R
  p.i.denom=p.i.denom+u.R
  
  # m.u.R=matrix(rep(u.R,J),nrow=J,byrow=T)
  
  ##Contribute to the transit, guess and slip probabilities (numerators and denominators separately).
  if(J>1){
  
  u.transit.denom=(1-u.knowledge[-J,])
  transit[prob_id[-J],]=transit[prob_id[-J],]+(m.ku[-J,]*u.transit.denom)*u.knowledge[-1,] ##Order of multiplication is important, otherwise the row names get shifted (R takes them from 1st factor)
  transit.denom[prob_id[-J],]=transit.denom[prob_id[-J],]+m.ku[-J,]*u.transit.denom
  }
  guess[prob_id,]=guess[prob_id,]+(m.ku*(1-u.knowledge))*u.correctness #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  guess.denom[prob_id,]=guess.denom[prob_id,]+m.ku*(1-u.knowledge)
  
  slip[prob_id,]=slip[prob_id,]+(m.ku*u.knowledge)*(1-u.correctness) #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  slip.denom[prob_id,]=slip.denom[prob_id,]+(m.ku*u.knowledge)
  
  }

}

##Impose the information threshold:
p.i.denom[which(p.i.denom<info.threshold)]=0
transit.denom[which(transit.denom<info.threshold)]=0
guess.denom[which(guess.denom<info.threshold)]=0
slip.denom[which(slip.denom<info.threshold)]=0

##Normalize the results over users.
p.i=p.i/p.i.denom
transit=transit/transit.denom
guess=guess/guess.denom
slip=slip/slip.denom


#Replicate the initial knowledge to all users:
p.i=matrix(rep(p.i,n.users),nrow=n.users, byrow=T)
dimnames(p.i)=dimnames(m.p.i)

## Matrices contain NaNs or Infs in those elements that we do not want to update (it means we don't have sufficient data). Therefore, replace them by the previously stored values.

ind=which((is.na(p.i))|(is.infinite(p.i)))
p.i=pmax(replace(p.i,ind,m.p.i[ind]),epsilon)
ind=which((is.na(transit))|(is.infinite(transit)))
transit=replace(transit,ind,m.transit[ind])
ind=which((is.na(guess))|(is.infinite(guess)))
guess=replace(guess,ind,m.guess[ind])
ind=which((is.na(slip))|(is.infinite(slip)))
slip=replace(slip,ind,m.slip[ind])


return(list(p.i=p.i,transit=transit,guess=guess,slip=slip))

}
