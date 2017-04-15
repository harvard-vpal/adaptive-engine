##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

knowledge=function(prob_id,correctness){
##This function finds the empirical knowledge of a single user given a chronologically ordered sequence of items submitted.
  
m.k.u=m.k[prob_id,]
m.slip.u=m.slip.neg.log[prob_id,]
m.guess.u=m.guess.neg.log[prob_id,]
N=length(prob_id)
  
z=matrix(0,nrow=N+1,ncol=ncol(m.k));
x=rep(0,N)
z[1,]=(1-correctness) %*% m.slip.u;
z[N+1,]=correctness %*% m.guess.u;
if(N>1){
  for(n in 1:(N-1)){
    # x[1:n]=correctness[1:n];
    # x[(n+1):N]=1-correctness[(n+1):N]
    # z[n+1,]=x %*% m.k.u
    
    x[1:n]=correctness[1:n]
    x[(n+1):N]=1-correctness[(n+1):N]
    temp=rbind(m.guess.u[1:n,],m.slip.u[(n+1):N,])
    z[n+1,]=x %*% temp
  }
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
  # knowledge[which(knowledge[,j]!=temp),j]=0.5
  
}

knowledge[,j]=knowledge[,j]/length(ind) ##We average the knowledge when there are multiple candidates (length(ind)>1)

}

return(knowledge)


}



estimate=function(relevance.threshold=0, information.threshold=20,remove.degeneracy=T){
  
##This function estimates the matrices of the BKT parameters from the user interaction data.
##To account for the fact that NaN and Inf elements of the estimated matrices should not be used as updates, this function replaces such elements with the corresponding elements of the current BKT parameter matrices.
##Thus, the outputs of this function do not contain any non-numeric values and should be used to simply replace the current BKT parameter matrices.

trans=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
trans.denom=matrix(0,nrow=n.probs,ncol=n.los,dimnames=list(probs$id,los$id))
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
    
  m.k.u=m.k[prob_id,]
  
  ##Calculate the sum of relevances of user's experience for a each learning objective
  if(J==1){
    u.R=m.k.u
  }else{
  u.R=colSums(m.k.u)
  }
  
  ##Implement the relevance threshold:
  u.R[u.R<=relevance.threshold]=0
  u.R[u.R>0]=1
  
  m.k.u[m.k.u<=relevance.threshold]=0
  m.k.u[m.k.u>0]=1
  # m.k.u=m.tagging[prob_id,]
  
  u.knowledge=knowledge(prob_id, m.correctness[u,prob_id]);
  u.correctness=m.correctness[u,prob_id]
  
  ##Contribute to the averaged initial knowledge.
  p.i=p.i+u.knowledge[1,]*u.R
  p.i.denom=p.i.denom+u.R
  
  # m.R.u=matrix(rep(u.R,J),nrow=J,byrow=T)

  

  
  ##Contribute to the trans, guess and slip probabilities (numerators and denominators separately).
  if(J>1){
  u.trans.denom=(1-u.knowledge[-J,])
  trans[prob_id[-J],]=trans[prob_id[-J],]+(m.k.u[-J,]*u.trans.denom)*u.knowledge[-1,] ##Order of multiplication is important, otherwise the row names get shifted (R takes them from 1st factor)
  trans.denom[prob_id[-J],]=trans.denom[prob_id[-J],]+m.k.u[-J,]*u.trans.denom
  }
  
  guess[prob_id,]=guess[prob_id,]+(m.k.u*(1-u.knowledge))*u.correctness #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  guess.denom[prob_id,]=guess.denom[prob_id,]+m.k.u*(1-u.knowledge)
  
  slip[prob_id,]=slip[prob_id,]+(m.k.u*u.knowledge)*(1-u.correctness) #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  slip.denom[prob_id,]=slip.denom[prob_id,]+(m.k.u*u.knowledge)
  
  }

}

##Impose the information threshold:

# info.threshold.vector=info.threshold*u.R/J
# 
# temp=t(t(p.i.denom)/info.threshold.vector)
# p.i.denom[which(abs(temp)<1)]=0
# temp=t(t(trans.denom)/info.threshold.vector)
# trans.denom[which(abs(temp)<1)]=0
# temp=t(t(guess.denom)/info.threshold.vector)
# guess.denom[which(abs(temp)<1)]=0
# temp=t(t(slip.denom)/info.threshold.vector)
# slip.denom[which(abs(temp)<1)]=0


p.i.denom[which(p.i.denom<information.threshold)]=0
trans.denom[which(trans.denom<information.threshold)]=0
guess.denom[which(guess.denom<information.threshold)]=0
slip.denom[which(slip.denom<information.threshold)]=0

##Normalize the results over users.
p.i=p.i/p.i.denom
trans=trans/trans.denom
guess=guess/guess.denom
slip=slip/slip.denom

##Remove guess and slip probabilities of 0.5 and above (degeneracy):

if(remove.degeneracy){
guess[which(guess>=0.5)]=NA
slip[which(slip>=0.5)]=NA
}
#Replicate the initial knowledge to all users:
p.i=matrix(rep(p.i,n.users),nrow=n.users, byrow=T)
dimnames(p.i)=dimnames(m.L.i)

## Matrices contain NaNs or Infs in those elements that we do not want to update (it means we don't have sufficient data). Therefore, replace them by the previously stored values.

# ind=which((is.na(p.i))|(is.infinite(p.i)))
# p.i=pmax(replace(p.i,ind,m.p.i[ind]),epsilon)
# ind=which((is.na(trans))|(is.infinite(trans)))
# trans=replace(trans,ind,m.trans[ind])
# ind=which((is.na(guess))|(is.infinite(guess)))
# guess=replace(guess,ind,m.guess[ind])
# ind=which((is.na(slip))|(is.infinite(slip)))
# slip=replace(slip,ind,m.slip[ind])

#Convert to odds (logarithmic in case of p.i):
p.i=pmin(pmax(p.i,epsilon),1-epsilon)
trans=pmin(pmax(trans,epsilon),1-epsilon)
guess=pmin(pmax(guess,epsilon),1-epsilon)
slip=pmin(pmax(slip,epsilon),1-epsilon)

L.i=log(p.i/(1-p.i))
trans=trans/(1-trans)
guess=guess/(1-guess)
slip=slip/(1-slip)

##Keep the versions with NAs in them:
L.i.na=L.i
trans.na=trans
guess.na=guess
slip.na=slip

ind=which((is.na(L.i))|(is.infinite(L.i)))
L.i=replace(L.i,ind,m.L.i[ind])
ind=which((is.na(trans))|(is.infinite(trans)))
trans=replace(trans,ind,m.trans[ind])
ind=which((is.na(guess))|(is.infinite(guess)))
guess=replace(guess,ind,m.guess[ind])
ind=which((is.na(slip))|(is.infinite(slip)))
slip=replace(slip,ind,m.slip[ind])



return(list(L.i=L.i,trans=trans,guess=guess,slip=slip, L.i.na=L.i.na,trans.na=trans.na,guess.na=guess.na,slip.na=slip.na))

}
