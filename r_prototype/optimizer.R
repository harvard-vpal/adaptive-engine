##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


knowledge=function(prob_id,correctness, method="average"){
##This function finds the empirical knowledge of a single user given a chronologically ordered sequence of items submitted.
  
method=tolower(method)
if(!(method %in% c("average","min","max"))){
  method="average"
}  
  
  
m.k.u=m.k[prob_id,,drop=FALSE]
m.slip.u=m.slip.neg.log[prob_id,,drop=FALSE]
m.guess.u=m.guess.neg.log[prob_id,,drop=FALSE]
N=length(prob_id)
  
z=matrix(0,nrow=N+1,ncol=ncol(m.k));
x=rep(0,N)
z[1,]=(1-correctness) %*% m.slip.u;
z[N+1,]=correctness %*% m.guess.u;
if(N>1){
  for(n in 1:(N-1)){
    x[1:n]=correctness[1:n]
    x[(n+1):N]=1-correctness[(n+1):N]
    temp=rbind(m.guess.u[1:n,,drop=FALSE],m.slip.u[(n+1):N,,drop=FALSE])
    z[n+1,]=x %*% temp
  }
}
knowledge=matrix(0,ncol=ncol(m.k),nrow=N);
rownames(knowledge)=prob_id;
colnames(knowledge)=colnames(m.k)

for (j in 1:ncol(z)){
ind=which(z[,j]==min(z[,j]))

if(method=="average"){
  for (i in ind){
  
    temp=rep(0,N);
    if (i==1){
      temp=rep(1,N)
    }else if (i<=N){
      temp[i:N]=1
    }
  
    knowledge[,j]=knowledge[,j]+temp
  
  }

  knowledge[,j]=knowledge[,j]/length(ind) ##We average the knowledge when there are multiple candidates (length(ind)>1)

}

if(method=="max"){
  i=max(ind)
  temp=rep(0,N);
  if (i==1){
    temp=rep(1,N)
  }else if (i<=N){
    temp[i:N]=1
  }
  
 knowledge[,j]=temp 
}

if(method=="min"){
  i=min(ind)
  temp=rep(0,N);
  if (i==1){
    temp=rep(1,N)
  }else if (i<=N){
    temp[i:N]=1
  }
  
  knowledge[,j]=temp 
}

}

return(knowledge)


}



estimate=function(relevance.threshold=0.01, information.threshold=20,remove.degeneracy=TRUE, training.set=NULL){
  
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

if(is.null(training.set)){
training.set=users$id
}

for (u in training.set){
  
  ##List problems that the user tried, in chronological order
  
  temp=subset(transactions,(transactions$user_id==u)&(transactions$problem_id %in% useForTraining))
  temp=temp[order(temp$time),]
  
  J=length(temp$problem_id)
  if(J>0){
    
  m.k.u=m.k[temp$problem_id,,drop=FALSE]
  
  ##Calculate the sum of relevances of user's experience for a each learning objective
  if(J==1){
    u.R=m.k.u
  }else{
      u.R=colSums(as.matrix(m.k.u)) 
  }
  
  ##Implement the relevance threshold:
  
  u.R=(u.R>relevance.threshold)
  
  m.k.u=(m.k.u>relevance.threshold)
  
  #u.knowledge=knowledge(prob_id, m.correctness[u,prob_id], method="average");
  #u.correctness=m.correctness[u,prob_id]
  
  
  # u.correctness=temp$score
  # prob_id=temp$problem_id
  u.knowledge=knowledge(temp$problem_id, temp$score, method="average");
  
  ##Contribute to the averaged initial knowledge.
  p.i=p.i+u.knowledge[1,]*u.R
  p.i.denom=p.i.denom+u.R
  
  # m.R.u=matrix(rep(u.R,J),nrow=J,byrow=T)

  

  
  ##Contribute to the trans, guess and slip probabilities (numerators and denominators separately).
  # if(J>1){
  # u.trans.denom=(1-u.knowledge[-J,])
  # trans[prob_id[-J],]=trans[prob_id[-J],]+(m.k.u[-J,]*u.trans.denom)*u.knowledge[-1,] ##Order of multiplication is important, otherwise the row names get shifted (R takes them from 1st factor)
  # trans.denom[prob_id[-J],]=trans.denom[prob_id[-J],]+m.k.u[-J,]*u.trans.denom
  # }
  # 
  # guess[prob_id,]=guess[prob_id,]+(m.k.u*(1-u.knowledge))*u.correctness #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  # guess.denom[prob_id,]=guess.denom[prob_id,]+m.k.u*(1-u.knowledge)
  # 
  # slip[prob_id,]=slip[prob_id,]+(m.k.u*u.knowledge)*(1-u.correctness) #This relies on the fact that R regards matrices as filled by column. This is not a matrix multiplication!
  # slip.denom[prob_id,]=slip.denom[prob_id,]+(m.k.u*u.knowledge)
  
  for (pr in 1:J){

    prob_id=temp$problem_id[pr]

    if(pr<J){
      trans[prob_id,]=trans[prob_id,]+(m.k.u[pr,]*(1-u.knowledge[pr,]))*u.knowledge[pr+1,]
      trans.denom[prob_id,]=trans.denom[prob_id,]+m.k.u[pr,]*(1-u.knowledge[pr,])
    }

    guess[prob_id,]=guess[prob_id,]+(m.k.u[pr,]*(1-u.knowledge[pr,]))*temp$score[pr]
    guess.denom[prob_id,]=guess.denom[prob_id,]+(m.k.u[pr,]*(1-u.knowledge[pr,]))

    slip[prob_id,]=slip[prob_id,]+(m.k.u[pr,]*u.knowledge[pr,])*(1-temp$score[pr])
    slip.denom[prob_id,]=slip.denom[prob_id,]+(m.k.u[pr,]*u.knowledge[pr,])
  }
  
  
  
  
  
  
  }

}

####PROBLEM GROUPING#######

# ind=which(m.tagging!=0)
# trans=replace(trans,ind,sum(trans))
# trans.denom=replace(trans.denom,ind,sum(trans.denom))
# 
# ind=which(m.tagging!=0)
# guess=replace(guess,ind,sum(guess))
# guess.denom=replace(guess.denom,ind,sum(guess.denom))
# 
# ind=which(m.tagging!=0)
# slip=replace(slip,ind,sum(slip))
# slip.denom=replace(slip.denom,ind,sum(slip.denom))

###########################



##Impose the information threshold:


p.i.denom[which(p.i.denom<information.threshold)]=NA
trans.denom[which(trans.denom<information.threshold)]=NA
guess.denom[which(guess.denom<information.threshold)]=NA
slip.denom[which(slip.denom<information.threshold)]=NA

##Normalize the results over users.
p.i=p.i/p.i.denom
trans=trans/trans.denom
guess=guess/guess.denom
slip=slip/slip.denom

##Remove guess and slip probabilities of 0.5 and above (degeneracy):

if(remove.degeneracy){
  
  ind_g=which((guess>=0.5)|(guess+slip>=1))
  ind_s=which((slip>=0.5)|(guess+slip>=1))
  
  guess[ind_g]=NA
  slip[ind_s]=NA
  # guess[which(guess>=0.5)]=NA
  # slip[which(slip>=0.5)]=NA
  
}
#Replicate the initial knowledge to all users:
p.i=matrix(rep(p.i,n.users),nrow=n.users, byrow=TRUE)
dimnames(p.i)=dimnames(m.L.i)


#Convert to odds
p.i=pmin(pmax(p.i,epsilon),1-epsilon)
trans=pmin(pmax(trans,epsilon),1-epsilon)
guess=pmin(pmax(guess,epsilon),1-epsilon)
slip=pmin(pmax(slip,epsilon),1-epsilon)

L.i=(p.i/(1-p.i))
trans=trans/(1-trans)
guess=guess/(1-guess)
slip=slip/(1-slip)

## Matrices contain NaNs or Infs in those elements that we do not want to update (it means we don't have sufficient data). Therefore, replace them by the previously stored values.

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
