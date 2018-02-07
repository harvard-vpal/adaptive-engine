##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

n.users<<-1
n.los<<-8
n.probs<<-40
n.modules=2

slip.probability=0.15
guess.probability=0.1
trans.probability=0.1
prior.knowledge=0.2
forgetting=exp(-1)

####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=0 ##Relevance threshold used in the BKT optimization procedure
M=20 ##Information threshold user in the BKT optimization procedure
L.star<<- 3 #Threshold odds. If mastery odds are >= than L.star, the LO is considered mastered
r.star<<- 0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.

##Substrategy weights

W<<-c(  
  'remediation'=3
  ,'continuity'=0.5
  ,'readiness'=1
  ,'difficulty'=1
  ,'memory'=1
  ,'suggested'=1
      )

##List of substrategies:
strategy<<-rep(list(NULL),length(W))
names(strategy)=names(W)


options(stringsAsFactors = FALSE)


users=data.frame("id"=paste0("u",1:n.users),"name"=paste0("user ",1:n.users), "group"=1)
users$group[1:round(n.users*2/3)]=0
users$id=as.character(users$id)
los=data.frame("id"=paste0("l",1:n.los),"name"=paste0("LO ",1:n.los))
los$id=as.character(los$id)
probs=data.frame("id"=paste0("p",1:n.probs),"name"=paste0("problem ",1:n.probs))
probs$id=as.character(probs$id)

probs$required.next.id=''
probs$suggested.next.id=''
# probs$required.next.id[2]=c(probs$id[1])
probs$suggested.next.id=c(probs$id[-1],'')

probs$maxsubmits.for.serving=c(NA,rep(1,nrow(probs)-1))


#Let problems be divided into several modules of adaptivity. In each module, only the items from that scope are used.

scope<<-matrix(FALSE,nrow=n.probs, ncol=n.modules)
scope[,1]=TRUE
rownames(scope)=probs$id



##List which items should be used for training the BKT
useForTraining=probs$id


#Initialize the matrix of mastery odds

L.i<<-exp(rep(0,n.los))

# Define the matrix of initial mastery by replicating the same row for each user
m.L.i<<-matrix(rep(L.i,n.users),ncol=n.los, byrow = FALSE)
rownames(m.L.i)=users$id
colnames(m.L.i)=los$id

##Define pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
m.w<<-matrix(runif(n.los^2),nrow=n.los);
rownames(m.w)=los$id
colnames(m.w)=los$id
for(i in 1:nrow(m.w)){
  
  for(j in 1:ncol(m.w)){
    des=sample(c(TRUE,FALSE),1)
    if(des){
      m.w[i,j]=0
    }else{
      m.w[j,i]=0
    }
  }
  
}
##


##Define the vector of difficulties ####
difficulty<<-rep(0.5,n.probs);
names(difficulty)=probs$id

difficulty=pmin(pmax(difficulty,epsilon),1-epsilon)
difficulty=log(difficulty/(1-difficulty))

##


##Define the preliminary relevance matrix: problems tagged with LOs. rownames are problems. Assumed that the entries are in [0,1] interval ####

los.per.problem=1

temp=c(rep(1,los.per.problem),rep(0,n.los-los.per.problem))
m.tagging<<-matrix(0,nrow=n.probs, ncol=n.los);

for(i in 1:n.probs){
  m.tagging[i,]=sample(temp,replace=FALSE)
}
rownames(m.tagging)=probs$id
colnames(m.tagging)=los$id


##Define the matrix of transit odds ####

m.trans<<-(trans.probability/(1-trans.probability))*m.tagging
##

##Define the matrix of guess odds (and probabilities) ####
m.guess<<-(guess.probability/(1-guess.probability))*matrix(1,nrow=n.probs, ncol = n.los);
m.guess[which(m.tagging==0)]=1
rownames(m.guess)=probs$id
colnames(m.guess)=los$id
##

##Define the matrix of slip odds ####
m.slip<<-(slip.probability/(1-slip.probability))*matrix(1,nrow=n.probs, ncol = n.los);
m.slip[which(m.tagging==0)]=1
rownames(m.slip)=probs$id
colnames(m.slip)=los$id
##

##Define the matrix which keeps track whether a LO for a user has ever been updated
m.exposure<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.exposure)=users$id
colnames(m.exposure)=los$id
row.exposure<<- m.exposure[1,]

##Define the matrix of confidence: essentially how much information we had for the mastery estimate
m.confidence<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.confidence)=users$id
colnames(m.confidence)=los$id
row.confidence<<- m.confidence[1,]

##Define the matrix of "user has seen a problem or not": rownames are problems. ####
m.times.submitted<<-matrix(0,nrow=n.users, ncol=n.probs);
rownames(m.times.submitted)=users$id
colnames(m.times.submitted)=probs$id
row.times.submitted<<-m.times.submitted[1,]
##

##Define the matrix of item forgetting parameters
m.forgetting<<-matrix(forgetting,nrow=nrow(users),ncol=nrow(probs))
rownames(m.forgetting)=users$id
colnames(m.forgetting)=probs$id

m.item.memory<<-matrix(0,nrow=nrow(users),ncol=nrow(probs))
rownames(m.item.memory)=users$id
colnames(m.item.memory)=probs$id

##Define the data frame of interaction records
transactions<<-data.frame()

##Define vector that will store the latest item seen by a user

last.seen<<- rep("",n.users);
names(last.seen)=users$id