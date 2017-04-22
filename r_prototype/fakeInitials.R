##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

n.users<<-20
n.los<<-10
n.probs<<-200
users=data.frame("id"=paste0("u",1:n.users),"name"=paste0("user ",1:n.users))
users$id=as.character(users$id)
los=data.frame("id"=paste0("l",1:n.los),"name"=paste0("LO ",1:n.los))
los$id=as.character(los$id)
probs=data.frame("id"=paste0("p",1:n.probs),"name"=paste0("problem ",1:n.probs))
probs$id=as.character(probs$id)

#Initialize the matrix of mastery odds
m.L.i=matrix(0,ncol=n.los, nrow=n.users)
rownames(m.L.i)=users$id
colnames(m.L.i)=los$id



##Define the matrix which keeps track whether a LO for a user has ever been updated
m.pristine=matrix(T,ncol=n.los, nrow=n.users)
rownames(m.pristine)=users$id
colnames(m.pristine)=los$id


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


##Define the vector of difficulties ####
difficulty<<-rep(1,n.probs);
names(difficulty)=probs$id

difficulty=pmin(difficulty, 1-epsilon);
difficulty=pmax(difficulty,epsilon)
difficulty=log(difficulty/(1-difficulty))

##


##Define the preliminary relevance matrix: problems tagged with LOs. rownames are problems. Assumed that the entries are in [0,1] interval ####

los.per.problem=2

temp=c(0.5+0.5*runif(los.per.problem),rep(0,n.los-los.per.problem))
m.tagging=NULL
for(q in 1:n.probs){
  m.tagging=c(m.tagging,sample(temp))
}
m.tagging=matrix(m.tagging, nrow=n.probs,byrow=T)

rownames(m.tagging)=probs$id
colnames(m.tagging)=los$id
##

##Define the matrix of transit odds ####

m.trans<<-0.18*m.tagging
##

##Define the matrix of guess odds (and probabilities) ####
m.guess<<-matrix(0.1,nrow=n.probs, ncol = n.los);
m.guess[which(m.tagging==0)]=1
rownames(m.guess)=probs$id
colnames(m.guess)=los$id
##

##Define the matrix of slip odds ####
m.slip<<-matrix(0.1,nrow=n.probs, ncol = n.los);
m.slip[which(m.tagging==0)]=1
rownames(m.slip)=probs$id
colnames(m.slip)=los$id
##


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

##Define vector that will store the latest item seen by a user

last.seen<<- rep(NA,n.users);
names(last.seen)=users$id