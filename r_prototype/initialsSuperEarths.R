##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA
library(plyr)

slip.probability=0.1
guess.probability=0.1
trans.probability=0.1
prior.knowledge=0.13

####Global variables####
epsilon<<-1e-10 # a regularization cutoff, the smallest value of a mastery probability
eta=0 ##Relevance threshold used in the BKT optimization procedure
M=20 ##Information threshold user in the BKT optimization procedure
L.star<<- 3 #Threshold odds. If mastery odds are >= than L.star, the LO is considered mastered
r.star<<- 0 #Threshold for forgiving lower odds of mastering pre-requisite LOs.
V.r<<-5 ##Importance of readiness in recommending the next item
V.d<<-3 ##Importance of demand in recommending the next item
V.a<<-1 ##Importance of appropriate difficulty in recommending the next item
V.c<<-1 ##Importance of continuity in recommending the next item

#####

if(!exists("before.optimizing")){before.optimizing=T}


###########################
### DEFINE DATA MATRICES###
###########################


##List which items should be used for training the BKT
useForTraining=probs$id


##Relations among the LOs:
##Define pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
m.w<<-matrix(0,nrow=n.los, ncol=n.los);
rownames(m.w)=los$id
colnames(m.w)=los$id

##

m.tagging<<- matrix(0,nrow=n.probs,ncol=n.los)
rownames(m.tagging)=probs$id
colnames(m.tagging)=los$id

for (i in 1:nrow(df_tag)){
  
  temp=df_tag[i,]
  m.tagging[temp$edx.id,temp$LO]=1
  
}

##Check that all problems are tagged and that all LOs are used:

# ind=which(rowSums(m.tagging)==0)
# if(length(ind)>0){
#   cat("Problem without an LO: ",paste0(rownames(m.tagging)[ind],collapse=", "),"\n")
# }else{
#   cat("Problems without an LO: none\n")
# }
# ind=which(colSums(m.tagging)==0)
# if(length(ind)>0){
#   cat("LOs without a problem: ",paste0(colnames(m.tagging)[ind],collapse=", "),"\n")
# }else{
#   cat("LOs without a problem: none\n")
# }


##Define the vector of difficulties ####
difficulty<<-rep(1,n.probs);
names(difficulty)=probs$id

##

if(before.optimizing){
  ##Define the matrix of transit odds ####
  
  m.trans<<- (trans.probability/(1-trans.probability))*m.tagging
  ##
  
  ##Define the matrix of guess odds ####
  m.guess<<-matrix(guess.probability/(1-guess.probability),nrow=n.probs, ncol = n.los);
  m.guess[which(m.tagging==0)]=1
  rownames(m.guess)=probs$id
  colnames(m.guess)=los$id
  ##
  
  ##Define the matrix of slip odds ####
  m.slip<<-matrix(slip.probability/(1-slip.probability),nrow=n.probs, ncol = n.los);
  m.slip[which(m.tagging==0)]=1
  rownames(m.slip)=probs$id
  colnames(m.slip)=los$id
  ##
}



if(before.optimizing){
#Initialize the matrix of mastery odds
m.L.i<<-matrix((prior.knowledge/(1-prior.knowledge)),ncol=n.los, nrow=n.users)
rownames(m.L.i)=users$id
colnames(m.L.i)=los$id
}

##Define the matrix which keeps track whether a LO for a user has ever been updated
m.exposure<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.exposure)=users$id
colnames(m.exposure)=los$id

##Define the matrix which keeps track whether a LO for a user has ever been updated
m.exposure.before.problem<<-matrix(0,ncol=n.probs, nrow=n.users)
rownames(m.exposure.before.problem)=users$id
colnames(m.exposure.before.problem)=probs$id

##Define the matrix of confidence: essentially how much information we had for the mastery estimate
m.confidence<<-matrix(0,ncol=n.los, nrow=n.users)
rownames(m.confidence)=users$id
colnames(m.confidence)=los$id
row.confidence<<- m.confidence[1,]

##Define the matrix of "user has seen a problem or not": rownames are problems. ####
m.unseen<<-matrix(T,nrow=n.users, ncol=n.probs);
rownames(m.unseen)=users$id
colnames(m.unseen)=probs$id
##


##Define the data frame of interaction records
#transactions<<-data.frame()
transactions<<-plyr::rename(Pcheck[,c("username","problem_id","time","correctness")],c("username"="user_id","correctness"="score"))

# ##Define the matrix of results of user interactions with problems.####
# m.correctness<<-matrix(NA,nrow=n.users, ncol=n.probs);
# # m.correctness<<-matrix(sample(c(T,F),n.users*n.probs,replace=T),nrow=n.users, ncol=n.probs);
# rownames(m.correctness)=users$id
# colnames(m.correctness)=probs$id
# 
# m.predicted<<-m.correctness
# 
# 
# ##Define the matrix of time stamps of results of user interactions with problems.####
# m.timestamp<<-matrix(NA,nrow=n.users, ncol=n.probs);
# rownames(m.timestamp)=users$id
# colnames(m.timestamp)=probs$id


##Define vector that will store the latest item seen by a user

last.seen<<- rep("",n.users);
names(last.seen)=users$id

#Let problems be divided into several modules of adaptivity. In each module, only the items from that scope are used.
##Proposed code: 
# -1 - is not among the adaptively served ones
# 0 - problem can be served in any module
# n=1,2,3,...  - problem can be served in the module n
scope<<-rep(1, n.probs)
# cat("Initialization complete\n")

