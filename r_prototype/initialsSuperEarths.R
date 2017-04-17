##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA


slip.probability=0.15
guess.probability=0.1
trans.probability=0.1
prior.knowledge=0.2

library(plyr)

datadir="Super-Earths data"
datadir_charlesRiverX="/Users/ilr548/Documents/HX_data/Courses/SPU30x-3T2016";
xblockPrefix="https://courses.edx.org/xblock/block-v1:HarvardX[+]SPU30x[+]3T2016[+]type@problem[+]block@"
moduleIDPrefix="HarvardX/SPU30x/problem/"

df.probs=read.csv(file.path(datadir,"adaptive edx activity list and answers - problem.csv"),header=T, stringsAsFactors = F)
df.probs$problem_id=as.character(df.probs$problem_id)
df.probs$edx.id=gsub(xblockPrefix,"",df.probs$xblock_url)
df.probs.lo=read.csv(file.path(datadir,"adaptive edx activity list and answers - problem LO.csv"),header=T, stringsAsFactors = F)
df.probs.lo$problem_id=as.character(df.probs.lo$problem_id)
df.probs.lo$LO=as.character(df.probs.lo$LO)
int=intersect(df.probs$problem_id,df.probs.lo$problem_id)
df.probs=subset(df.probs,problem_id %in% int)
df.probs.lo=subset(df.probs.lo,problem_id %in% int)
df=merge(df.probs.lo,df.probs,by="problem_id")

###Course grain to the state of a single LO
df$LO="the whole thing"

##Define the lists of LOs and problems
los=data.frame("id"=unique(df$LO));
los$name=los$id
los=los[order(los$id),]
n.los=nrow(los)

probs=data.frame("id"=unique(df$edx.id));
temp=unique(df[,c("edx.id","display_name.x")])
probs=merge(probs,temp,by.x="id",by.y="edx.id")
probs=plyr::rename(probs,c("display_name.x"="name"))
probs=probs[order(probs$id),]
n.probs=nrow(probs)

##Relations among the LOs:
##Define pre-requisite matrix. rownames are pre-reqs. Assumed that the entries are in [0,1] interval ####
m.w<<-matrix(0,nrow=n.los, ncol=n.los);
rownames(m.w)=los$id
colnames(m.w)=los$id

##

m.tagging<<- matrix(0,nrow=n.probs,ncol=n.los)
rownames(m.tagging)=probs$id
colnames(m.tagging)=los$id

for (i in 1:nrow(df.probs.lo)){
  
  temp=df[i,]
  m.tagging[temp$edx.id,temp$LO]=1
  
}

##Check that all problems are tagged and that all LOs are used:

ind=which(rowSums(m.tagging)==0)
if(length(ind)>0){
cat("Problem without an LO: ",paste0(rownames(m.tagging)[ind],collapse=", "),"\n")
}else{
  cat("Problems without an LO: none\n")
}
ind=which(colSums(m.tagging)==0)
if(length(ind)>0){
  cat("LOs without a problem: ",paste0(colnames(m.tagging)[ind],collapse=", "),"\n")
}else{
  cat("LOs without a problem: none\n")
}


##Define the vector of difficulties ####
difficulty<<-rep(1,n.probs);
names(difficulty)=probs$id

difficulty=pmin(difficulty, 1-epsilon);
difficulty=pmax(difficulty,epsilon)
difficulty=log(difficulty/(1-difficulty))

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


####################
##STUFF WITH USERS##
####################

Pcheck=read.csv(file.path(datadir_charlesRiverX,"problem_check.csv.gz"),header=T, stringsAsFactors = F)
options(digits.secs=8)
Pcheck$time=as.POSIXct(Pcheck$time,tz="UTC")
Pcheck$problem_id=gsub(moduleIDPrefix,"",Pcheck$module_id)

Pcheck=subset(Pcheck,problem_id %in% probs$id)
Pcheck$correctness=0
Pcheck$correctness[which(Pcheck$success=="correct")]=1

##Leave the first attempts only:
Pcheck$userproblem_id=paste(Pcheck$username,Pcheck$problem_id)
temp=aggregate(Pcheck$time, by=list("userproblem_id"=Pcheck$userproblem_id), FUN=min)
temp=merge(Pcheck,temp, by="userproblem_id")
Pcheck=subset(temp,time==x);
Pcheck$userproblem_id=NULL
Pcheck$x=NULL
Pcheck$time=as.numeric(Pcheck$time)

source("staffUserNames.R")
Pcheck=subset(Pcheck,!(username %in% staff$username))


##Remove those who did not do a lot

#Define the list of users
users=data.frame("id"=unique(Pcheck$username))
users$name=users$id
n.users=nrow(users)

if(before.optimizing){
#Initialize the matrix of mastery odds
m.L.i=matrix(log(prior.knowledge/(1-prior.knowledge)),ncol=n.los, nrow=n.users)
rownames(m.L.i)=users$id
colnames(m.L.i)=los$id
}

##Define the matrix which keeps track whether a LO for a user has ever been updated
m.pristine=matrix(T,ncol=n.los, nrow=n.users)
rownames(m.pristine)=users$id
colnames(m.pristine)=los$id

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

m.predicted<<-m.correctness


##Define the matrix of time stamps of results of user interactions with problems.####
m.timestamp<<-matrix(NA,nrow=n.users, ncol=n.probs);
rownames(m.timestamp)=users$id
colnames(m.timestamp)=probs$id

cat("Initialization complete\n")

