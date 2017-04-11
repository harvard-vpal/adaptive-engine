##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


# m.p.i=matrix(runif(n.los*n.users),ncol=n.los, nrow=n.users)
m.p.i=matrix(0,ncol=n.los, nrow=n.users)
rownames(m.p.i)=users$id
colnames(m.p.i)=los$id


##Define the matrix which keeps track whether a LO for a user has ever been updated
m.p.pristine=matrix(T,ncol=n.los, nrow=n.users)
rownames(m.p.pristine)=users$id
colnames(m.p.pristine)=los$id


##Define pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
m.w<<-matrix(runif(n.los^2),nrow=n.los);
rownames(m.w)=los$id
colnames(m.w)=los$id
for(i in 1:nrow(m.w)){
  
  for(j in 1:ncol(m.w)){
    des=sample(c(T,F),1)
    if(des){
      m.w[i,j]=0
    }else{
      m.w[j,i]=0
    }
  }
  
}
##





##Define the relevance matrix: problems tagged with LOs. rownames are problems. Assumed that the entries are in [0,1] interval ####

fraction.zeros=0.8;
temp=runif(n.probs*n.los);
temp[temp<fraction.zeros]=1;
temp=(1-temp)/(1-fraction.zeros)
m.k<<-matrix(temp,nrow=n.probs);
rownames(m.k)=probs$id
colnames(m.k)=los$id
##

##Define the vector of difficulties ####
difficulty<<-rep(1,n.probs);
names(difficulty)=probs$id
##

##Define the matrix of transit probabilities ####
# m.transit<<-matrix(0.1,nrow=n.probs, ncol = n.los);
# rownames(m.transit)=probs$id
# colnames(m.transit)=los$id

m.transit<<-0.1*m.k
##

##Define the matrix of guess probabilities ####
m.guess<<-matrix(0.1,nrow=n.probs, ncol = n.los);
rownames(m.guess)=probs$id
colnames(m.guess)=los$id
##

##Define the matrix of slip probabilities ####
m.slip<<-matrix(0.1,nrow=n.probs, ncol = n.los);
rownames(m.slip)=probs$id
colnames(m.slip)=los$id
##

##Define the matrix of odd increments:

m.odds.incr.zero<<- log(pmax(m.slip,epsilon)) - log(1-pmax(m.guess,epsilon))
m.odds.incr.slope<<- log((1-pmax(m.slip,epsilon))/pmax(m.slip,epsilon)) + log((1-pmax(m.guess,epsilon))/pmax(m.guess,epsilon))
# rownames(m.odds.incr.zero)=probs$id
# colnames(m.odds.incr.zero)=los$id
# rownames(m.odds.incr.slope)=probs$id
# colnames(m.odds.incr.slope)=los$id


##Define the matrix of "user has seen a problem or not": rownames are problems. ####
m.unseen<<-matrix(T,nrow=n.users, ncol=n.probs);
rownames(m.unseen)=users$id
colnames(m.unseen)=probs$id
##
##Define the matrix of results of user interactions with problems.####
m.correctness<<-matrix(NA,nrow=n.users, ncol=n.probs);
# m.correctness<<-matrix(sample(c(T,F),n.users*n.probs,replace=T),nrow=n.users, ncol=n.probs);
rownames(m.correctness)=users$id
colnames(m.correctness)=probs$id

##Define the matrix of time stamps of results of user interactions with problems.####
m.timestamp<<-matrix(NA,nrow=n.users, ncol=n.probs);
rownames(m.timestamp)=users$id
colnames(m.timestamp)=probs$id
